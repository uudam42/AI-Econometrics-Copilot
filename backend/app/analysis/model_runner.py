"""Model runner — orchestrates transformation → validation → estimation → diagnostics.

Entry point: run_analysis(config, record) → (AnalysisResult, ModelDiagnosticsResponse)
"""
from __future__ import annotations

import importlib
import math
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.analysis.diagnostics import (
    compute_breusch_pagan,
    compute_correlation_matrix,
    compute_descriptive_stats,
    compute_durbin_watson,
    compute_hausman,
    compute_jarque_bera,
    compute_vif,
)
from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER
from app.analysis.model_recommender import recommend_model
from app.analysis.ols_models import run_ols
from app.analysis.panel_models import (
    run_fixed_effects_for_hausman,
    run_panel,
    run_random_effects_for_hausman,
)
from app.core.errors import ModelExecutionError, ValidationAppError
from app.models.dataset_registry import DatasetRecord
from app.schemas.modeling import (
    AnalysisConfigurationRequest,
    AnalysisResult,
    CoefficientResult,
    DiagnosticTestResult,
    HausmanTestResult,
    ModelDiagnosticsResponse,
    ModelFitStatistics,
    PlotData,
    TransformationLogEntry,
)
from app.services.transformation_service import apply_transformations

_MAX_PLOT_POINTS = 500


def _validate_variables(
    df: pd.DataFrame, config: AnalysisConfigurationRequest
) -> None:
    vs = config.variable_selection
    all_vars = (
        [vs.dependent_variable, vs.primary_independent_variable]
        + vs.control_variables
    )
    for col in all_vars:
        if col not in df.columns:
            raise ValidationAppError(
                f"Variable '{col}' does not exist in the dataset "
                "(after transformations were applied).",
                details={"column": col, "available_columns": list(df.columns)},
            )
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValidationAppError(
                f"Variable '{col}' must be numeric to be used in regression. "
                f"Its current dtype is '{df[col].dtype}'."
            )

    if config.variable_selection.entity_column:
        entity_col = config.variable_selection.entity_column
        if entity_col not in df.columns:
            raise ValidationAppError(
                f"Entity column '{entity_col}' does not exist in the dataset."
            )

    if config.variable_selection.time_column:
        time_col = config.variable_selection.time_column
        if time_col not in df.columns:
            raise ValidationAppError(
                f"Time column '{time_col}' does not exist in the dataset."
            )


def _is_panel_model(model_type: str) -> bool:
    return model_type in ("pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects")


def _limit_plot_data(vals: list[float]) -> list[float]:
    if len(vals) > _MAX_PLOT_POINTS:
        idx = list(range(0, len(vals), len(vals) // _MAX_PLOT_POINTS))[:_MAX_PLOT_POINTS]
        return [vals[i] for i in idx]
    return vals


def run_analysis(
    config: AnalysisConfigurationRequest,
    record: DatasetRecord,
) -> tuple[AnalysisResult, ModelDiagnosticsResponse]:
    """Apply transformations, fit model, compute diagnostics, return results."""
    analysis_id = str(uuid.uuid4())

    # Step 1: Apply transformations to a fresh copy of the original dataset
    ops = [t.model_dump() for t in config.transformations]
    df, transformation_log = apply_transformations(record.dataframe, ops)

    # Step 2: Validate that all required variables exist and are numeric
    _validate_variables(df, config)

    vs = config.variable_selection
    dep_var = vs.dependent_variable
    primary_iv = vs.primary_independent_variable
    controls = vs.control_variables
    regressors = [primary_iv] + controls

    # Step 3: Run the requested model
    is_panel = _is_panel_model(config.model_type)

    if is_panel:
        entity_col = vs.entity_column
        time_col = vs.time_column
        if not entity_col or not time_col:
            raise ValidationAppError(
                "Panel models require both an entity column and a time column to be specified."
            )
        panel_result = run_panel(
            df=df,
            dep_var=dep_var,
            primary_iv=primary_iv,
            controls=controls,
            entity_col=entity_col,
            time_col=time_col,
            model_type=config.model_type,
            cluster_by_entity=config.cluster_standard_errors_by_entity,
        )
        coeff_dicts = panel_result.coefficients
        fit_dict = panel_result.fit
        residuals_raw = panel_result.residuals
        fitted_raw = panel_result.fitted_values
        actual_raw = panel_result.actual_values
        formula = panel_result.formula
        metadata = panel_result.model_metadata
        sm_result = None
        lm_result = panel_result.lm_result
    else:
        robust = config.model_type == "robust_ols"
        ols_result = run_ols(
            df=df,
            dep_var=dep_var,
            primary_iv=primary_iv,
            controls=controls,
            robust=robust,
        )
        coeff_dicts = ols_result.coefficients
        fit_dict = ols_result.fit
        residuals_raw = ols_result.residuals
        fitted_raw = ols_result.fitted_values
        actual_raw = ols_result.actual_values
        formula = ols_result.formula
        metadata = ols_result.model_metadata
        sm_result = ols_result.sm_result
        lm_result = None

    # Step 4: Build coefficient objects
    coefficients = [CoefficientResult(**c) for c in coeff_dicts]

    fit = ModelFitStatistics(
        r_squared=fit_dict.get("r_squared"),
        adj_r_squared=fit_dict.get("adj_r_squared"),
        f_statistic=fit_dict.get("f_statistic"),
        f_pvalue=fit_dict.get("f_pvalue"),
        aic=fit_dict.get("aic"),
        bic=fit_dict.get("bic"),
        n_obs=fit_dict.get("n_obs", 0),
        formula=formula,
    )

    # Step 5: Plot data (limit to 500 points for response size)
    plot_data = None
    if residuals_raw and fitted_raw and actual_raw:
        plot_data = PlotData(
            fitted_values=_limit_plot_data(fitted_raw),
            actual_values=_limit_plot_data(actual_raw),
            residuals=_limit_plot_data(residuals_raw),
        )

    # Step 6: Compute diagnostics
    all_model_vars = [dep_var] + regressors
    desc_stats = compute_descriptive_stats(df, all_model_vars)
    corr_matrix = compute_correlation_matrix(df, all_model_vars)

    # VIF — only for OLS models with statsmodels result
    vif_results: list = []
    if sm_result is not None:
        try:
            exog = sm_result.model.exog
            var_names = list(sm_result.model.exog_names)
            vif_results = compute_vif(exog, var_names)
        except Exception:
            pass

    # Breusch-Pagan — OLS only
    bp_result: DiagnosticTestResult
    jb_result: DiagnosticTestResult
    dw_result: DiagnosticTestResult

    if sm_result is not None and residuals_raw:
        resid_arr = np.array(residuals_raw)
        exog = sm_result.model.exog
        bp_result = compute_breusch_pagan(resid_arr, exog)
        jb_result = compute_jarque_bera(resid_arr)
        dw_result = compute_durbin_watson(resid_arr)
    else:
        _na = "This diagnostic is not currently available for the selected panel model specification."
        bp_result = DiagnosticTestResult(
            name="Breusch-Pagan Heteroskedasticity Test",
            statistic=None,
            p_value=None,
            interpretation=_na,
            available=False,
            unavailable_reason=_na,
        )
        if residuals_raw:
            resid_arr = np.array(residuals_raw)
            jb_result = compute_jarque_bera(resid_arr)
            dw_result = compute_durbin_watson(resid_arr)
        else:
            jb_result = DiagnosticTestResult(
                name="Jarque-Bera Residual Normality Test",
                statistic=None, p_value=None, interpretation=_na,
                available=False, unavailable_reason=_na,
            )
            dw_result = DiagnosticTestResult(
                name="Durbin-Watson Autocorrelation Statistic",
                statistic=None, p_value=None, interpretation=_na,
                available=False, unavailable_reason=_na,
            )

    # Hausman test — only for panel models and only when FE + RE can both be estimated
    hausman_result: HausmanTestResult
    if is_panel and vs.entity_column and vs.time_column and config.model_type in (
        "fixed_effects", "random_effects", "two_way_fixed_effects", "pooled_ols"
    ):
        try:
            fe_r = run_fixed_effects_for_hausman(df, dep_var, regressors, vs.entity_column, vs.time_column)
            re_r = run_random_effects_for_hausman(df, dep_var, regressors, vs.entity_column, vs.time_column)
            hausman_result = compute_hausman(fe_r, re_r)
        except Exception as exc:
            hausman_result = HausmanTestResult(
                available=False,
                unavailable_reason=f"Hausman test could not run: {exc!s}",
            )
    else:
        hausman_result = HausmanTestResult(
            available=False,
            unavailable_reason="Hausman test requires panel data with both entity and time columns.",
        )

    # Step 7: Model recommendation
    n_entities = metadata.get("n_entities") if is_panel else None
    n_periods = metadata.get("n_time_periods") if is_panel else None

    recommendation = recommend_model(
        has_entity_column=bool(vs.entity_column),
        has_time_column=bool(vs.time_column),
        n_entities=n_entities,
        n_periods=n_periods,
        breusch_pagan=bp_result if not is_panel else None,
        hausman=hausman_result if is_panel else None,
        n_obs=fit.n_obs,
        cluster_by_entity=config.cluster_standard_errors_by_entity,
    )

    diagnostics = ModelDiagnosticsResponse(
        analysis_id=analysis_id,
        descriptive_stats=desc_stats,
        correlation_matrix=corr_matrix,
        vif=vif_results,
        breusch_pagan=bp_result,
        jarque_bera=jb_result,
        durbin_watson=dw_result,
        hausman=hausman_result,
    )

    result = AnalysisResult(
        analysis_id=analysis_id,
        dataset_id=record.dataset_id,
        dataset_filename=record.filename,
        created_at=datetime.now(timezone.utc),
        model_type=config.model_type,
        formula=formula,
        variable_selection=vs,
        transformation_log=transformation_log,
        coefficients=coefficients,
        fit=fit,
        plot_data=plot_data,
        model_metadata=metadata,
        recommendation=recommendation,
        disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
    )

    return result, diagnostics
