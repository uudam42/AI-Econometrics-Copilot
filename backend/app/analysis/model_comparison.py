"""Multi-model comparison engine.

Runs each candidate model independently on the same processed dataset and
variable selection. Failures are captured without cancelling the full
comparison. Returns a structured ComparisonResult.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.analysis.comparison_metrics import (
    build_diagnostic_summary,
    ols_fit_summary,
    panel_fit_summary,
)
from app.analysis.comparison_rules import get_compatible_models
from app.analysis.diagnostics import (
    compute_breusch_pagan,
    compute_durbin_watson,
    compute_hausman,
    compute_jarque_bera,
    compute_vif,
)
from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER
from app.analysis.model_selection_service import _MODEL_LABELS, select_recommended_model
from app.analysis.ols_models import run_ols
from app.analysis.panel_models import (
    run_fixed_effects_for_hausman,
    run_panel,
    run_random_effects_for_hausman,
)
from app.core.errors import ModelExecutionError, ValidationAppError
from app.models.dataset_registry import DatasetRecord
from app.schemas.comparison import (
    CoefficientStabilityEntry,
    ComparisonRequest,
    ComparisonResult,
    ModelComparisonEntry,
    ModelFitSummary,
)
from app.schemas.modeling import ModelType
from app.services.transformation_service import apply_transformations


def _significance(p: float | None) -> str:
    if p is None:
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _direction(coeff: float | None) -> str:
    if coeff is None:
        return "unavailable"
    if coeff > 1e-10:
        return "positive"
    if coeff < -1e-10:
        return "negative"
    return "zero"


def _run_single_ols(
    df: pd.DataFrame,
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    robust: bool,
) -> dict[str, Any]:
    """Run OLS or Robust OLS and return a dict with all comparison info."""
    result = run_ols(df, dep_var, primary_iv, controls, robust=robust)
    sm = result.sm_result

    vif_list = []
    if sm is not None:
        try:
            vif_list = compute_vif(sm.model.exog, list(sm.model.exog_names))
        except Exception:
            pass

    bp = None
    jb = None
    dw = None
    if sm is not None and result.residuals:
        resid_arr = np.array(result.residuals)
        bp = compute_breusch_pagan(resid_arr, sm.model.exog)
        jb = compute_jarque_bera(resid_arr)
        dw = compute_durbin_watson(resid_arr)

    # Primary IV coefficient
    primary_coeff = next(
        (c for c in result.coefficients if c["variable"] == primary_iv), None
    )

    return {
        "run": result,
        "fit_summary": ols_fit_summary(result),
        "diag_summary": build_diagnostic_summary(vif_list, bp, None, dw),
        "vif": vif_list,
        "primary_coeff": primary_coeff,
        "formula": result.formula,
        "se_type": "HC1 (heteroskedasticity-robust)" if robust else "OLS (non-robust)",
    }


def _run_single_panel(
    df: pd.DataFrame,
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    entity_col: str,
    time_col: str,
    model_type: ModelType,
    cluster_se: bool,
    hausman_rejects: bool | None,
) -> dict[str, Any]:
    """Run a panel model and return comparison info."""
    result = run_panel(
        df=df,
        dep_var=dep_var,
        primary_iv=primary_iv,
        controls=controls,
        entity_col=entity_col,
        time_col=time_col,
        model_type=model_type,
        cluster_by_entity=cluster_se,
    )

    dw = None
    if result.residuals:
        resid_arr = np.array(result.residuals)
        dw = compute_durbin_watson(resid_arr)

    from app.schemas.modeling import HausmanTestResult, DiagnosticTestResult
    hausman = HausmanTestResult(
        available=False,
        unavailable_reason="Hausman test is run at comparison level.",
    )

    primary_coeff = next(
        (c for c in result.coefficients if c["variable"] == primary_iv), None
    )

    se_type = "clustered (entity)" if cluster_se else "standard"

    return {
        "run": result,
        "fit_summary": panel_fit_summary(result),
        "diag_summary": build_diagnostic_summary([], None, None, dw),
        "primary_coeff": primary_coeff,
        "formula": result.formula,
        "se_type": se_type,
        "entity_effects": result.model_metadata.get("entity_effects", False),
        "time_effects": result.model_metadata.get("time_effects", False),
    }


def run_comparison(
    request: ComparisonRequest,
    record: DatasetRecord,
) -> ComparisonResult:
    """Execute the full multi-model comparison and return a ComparisonResult."""
    comparison_id = str(uuid.uuid4())

    # Step 1: Apply transformations once
    ops = [t.model_dump() for t in request.transformations]
    df, transformation_log = apply_transformations(record.dataframe, ops)

    vs = request.variable_selection
    dep_var = vs.dependent_variable
    primary_iv = vs.primary_independent_variable
    controls = vs.control_variables
    has_entity = bool(vs.entity_column)
    has_time = bool(vs.time_column)

    transformation_summary = (
        f"{len(transformation_log)} transformation step(s) applied; "
        f"{df.shape[0]} rows remaining."
        if transformation_log
        else "No transformations applied."
    )

    # Step 2: Determine compatible models
    compatible, unavailable_reasons = get_compatible_models(
        has_entity_column=has_entity,
        has_time_column=has_time,
        requested_models=request.candidate_models,
    )

    # Step 3: Run Hausman test once (for all panel comparisons)
    hausman_rejects: bool | None = None
    shared_hausman = None
    if has_entity and has_time and vs.entity_column and vs.time_column:
        try:
            fe_r = run_fixed_effects_for_hausman(df, dep_var, [primary_iv] + controls, vs.entity_column, vs.time_column)
            re_r = run_random_effects_for_hausman(df, dep_var, [primary_iv] + controls, vs.entity_column, vs.time_column)
            shared_hausman = compute_hausman(fe_r, re_r)
            if shared_hausman.available and shared_hausman.p_value is not None:
                hausman_rejects = shared_hausman.p_value < 0.05
        except Exception:
            pass

    # Step 4: Run each compatible model
    entries: list[ModelComparisonEntry] = []
    coefficient_stability: list[CoefficientStabilityEntry] = []

    for model_type in compatible:
        label = _MODEL_LABELS.get(model_type, model_type)
        try:
            if model_type in ("ols", "robust_ols"):
                info = _run_single_ols(
                    df, dep_var, primary_iv, controls,
                    robust=(model_type == "robust_ols"),
                )
            else:
                info = _run_single_panel(
                    df, dep_var, primary_iv, controls,
                    entity_col=vs.entity_column or "",
                    time_col=vs.time_column or "",
                    model_type=model_type,
                    cluster_se=request.cluster_standard_errors_by_entity,
                    hausman_rejects=hausman_rejects,
                )

            # Attach shared Hausman to panel entries
            diag_sum = info["diag_summary"]
            if shared_hausman is not None and shared_hausman.available and model_type not in ("ols", "robust_ols"):
                diag_sum.hausman_rejects_re = hausman_rejects
                diag_sum.hausman_p_value = shared_hausman.p_value

            entry = ModelComparisonEntry(
                model_type=model_type,
                model_label=label,
                status="completed",
                formula=info.get("formula"),
                fit_metrics=info["fit_summary"],
                diagnostic_summary=diag_sum,
                standard_error_type=info.get("se_type"),
                entity_effects=info.get("entity_effects"),
                time_effects=info.get("time_effects"),
            )
            entries.append(entry)

            # Coefficient stability
            pc = info.get("primary_coeff")
            if pc:
                coeff_val = pc.get("coefficient")
                stability_entry = CoefficientStabilityEntry(
                    model_type=model_type,
                    model_label=label,
                    coefficient=coeff_val,
                    std_error=pc.get("std_error"),
                    p_value=pc.get("p_value"),
                    ci_lower=pc.get("ci_lower"),
                    ci_upper=pc.get("ci_upper"),
                    significance=pc.get("significance", ""),
                    direction=_direction(coeff_val),
                )
                coefficient_stability.append(stability_entry)

        except (ModelExecutionError, ValidationAppError) as exc:
            entries.append(ModelComparisonEntry(
                model_type=model_type,
                model_label=label,
                status="failed",
                reason=str(exc),
            ))
        except Exception as exc:
            entries.append(ModelComparisonEntry(
                model_type=model_type,
                model_label=label,
                status="failed",
                reason=f"Model estimation failed: {exc!s}",
            ))

    # Step 5: Add unavailable entries (wrong structure)
    for model_type, reason in unavailable_reasons.items():
        if model_type in request.candidate_models:
            label = _MODEL_LABELS.get(model_type, model_type)
            entries.append(ModelComparisonEntry(
                model_type=model_type,
                model_label=label,
                status="unavailable",
                reason=reason,
            ))

    # Step 6: Model selection recommendation
    recommendation = select_recommended_model(
        entries,
        has_entity=has_entity,
        has_time=has_time,
        cluster_se=request.cluster_standard_errors_by_entity,
    )

    return ComparisonResult(
        comparison_id=comparison_id,
        dataset_id=record.dataset_id,
        dataset_filename=record.filename,
        created_at=datetime.now(timezone.utc),
        variable_selection=vs,
        transformation_summary=transformation_summary,
        models=entries,
        coefficient_stability=coefficient_stability,
        recommendation=recommendation,
        disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
    )
