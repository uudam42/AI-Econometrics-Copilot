"""Constrained exploratory relationship discovery engine.

Orchestrates: screening → candidate generation → model execution →
multiple-testing correction → stability evaluation → finding ranking.

Every result is labeled as exploratory. No causal claims. No unconstrained
variable-combination search. All limits are configurable with safe defaults.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.analysis.discovery_candidates import generate_specifications
from app.analysis.discovery_scoring import assess_stability, score_finding
from app.analysis.discovery_screening import (
    screen_variables,
    select_candidate_outcomes,
    select_candidate_predictors,
)
from app.analysis.multiple_testing import apply_correction
from app.analysis.ols_models import run_ols
from app.analysis.panel_models import run_panel
from app.core.errors import ModelExecutionError, ValidationAppError
from app.models.dataset_registry import DatasetRecord
from app.schemas.dataset import StructureDetectionResult
from app.schemas.discovery import (
    DISCOVERY_DISCLAIMER,
    CandidateSpecification,
    CorrectedResult,
    DiscoveryConfig,
    DiscoveryResult,
    ExploratoryFinding,
    SpecificationResult,
    StabilityAssessment,
    VariableEligibility,
)
from app.services.structure_detector import detect_structure
from app.services.transformation_service import apply_transformations


def _safe(v: Any) -> float | None:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


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


def _execute_spec(
    spec: CandidateSpecification,
    df: pd.DataFrame,
    structure: StructureDetectionResult,
) -> SpecificationResult:
    outcome = spec.outcome_variable
    predictor = spec.primary_predictor
    controls = spec.controls
    model_type = spec.model_type

    work_df = df.copy()
    for t in spec.transformations:
        if t.get("operation") == "log_transform":
            for col in t.get("columns", []):
                if col in work_df.columns:
                    log_col = f"log_{col}"
                    valid = work_df[col] > 0
                    work_df.loc[valid, log_col] = np.log(work_df.loc[valid, col])
                    work_df.loc[~valid, log_col] = np.nan

    if outcome not in work_df.columns:
        return SpecificationResult(
            spec_id=spec.spec_id,
            status="failed",
            outcome_variable=outcome,
            primary_predictor=predictor,
            controls=controls,
            model_type=model_type,
            failure_reason=f"Outcome variable '{outcome}' not found after transformations",
        )

    if predictor not in work_df.columns:
        return SpecificationResult(
            spec_id=spec.spec_id,
            status="failed",
            outcome_variable=outcome,
            primary_predictor=predictor,
            controls=controls,
            model_type=model_type,
            failure_reason=f"Predictor '{predictor}' not found in dataset",
        )

    valid_controls = [c for c in controls if c in work_df.columns]

    try:
        if model_type in ("ols", "robust_ols"):
            result = run_ols(
                df=work_df,
                dep_var=outcome,
                primary_iv=predictor,
                controls=valid_controls,
                robust=(model_type == "robust_ols"),
            )
            primary_coeff = next(
                (c for c in result.coefficients if c["variable"] == predictor), None
            )
            coeff_val = primary_coeff.get("coefficient") if primary_coeff else None
            p_val = primary_coeff.get("p_value") if primary_coeff else None

            return SpecificationResult(
                spec_id=spec.spec_id,
                status="completed",
                outcome_variable=outcome,
                primary_predictor=predictor,
                controls=valid_controls,
                model_type=model_type,
                formula=result.formula,
                coefficient=_safe(coeff_val),
                std_error=_safe(primary_coeff.get("std_error")) if primary_coeff else None,
                p_value=_safe(p_val),
                ci_lower=_safe(primary_coeff.get("ci_lower")) if primary_coeff else None,
                ci_upper=_safe(primary_coeff.get("ci_upper")) if primary_coeff else None,
                n_obs=result.fit.get("n_obs"),
                r_squared=_safe(result.fit.get("r_squared")),
                direction=_direction(_safe(coeff_val)),
                significance=_significance(_safe(p_val)),
                warnings=[],
            )

        else:
            entity_col = structure.entity_column
            time_col = structure.time_column
            if not entity_col or not time_col:
                return SpecificationResult(
                    spec_id=spec.spec_id,
                    status="rejected",
                    outcome_variable=outcome,
                    primary_predictor=predictor,
                    controls=valid_controls,
                    model_type=model_type,
                    failure_reason="Panel model requires entity and time columns",
                )

            panel_result = run_panel(
                df=work_df,
                dep_var=outcome,
                primary_iv=predictor,
                controls=valid_controls,
                entity_col=entity_col,
                time_col=time_col,
                model_type=model_type,
            )

            absorbed = panel_result.absorbed_variables or []
            warnings: list[str] = []
            if predictor in absorbed:
                return SpecificationResult(
                    spec_id=spec.spec_id,
                    status="rejected",
                    outcome_variable=outcome,
                    primary_predictor=predictor,
                    controls=valid_controls,
                    model_type=model_type,
                    failure_reason=f"Primary predictor '{predictor}' was absorbed by fixed effects",
                    absorbed_variables=absorbed,
                )

            if absorbed:
                warnings.append(f"Absorbed variables: {', '.join(absorbed)}")

            primary_coeff = next(
                (c for c in panel_result.coefficients if c["variable"] == predictor), None
            )
            coeff_val = primary_coeff.get("coefficient") if primary_coeff else None
            p_val = primary_coeff.get("p_value") if primary_coeff else None

            return SpecificationResult(
                spec_id=spec.spec_id,
                status="completed",
                outcome_variable=outcome,
                primary_predictor=predictor,
                controls=valid_controls,
                model_type=model_type,
                formula=panel_result.formula,
                coefficient=_safe(coeff_val),
                std_error=_safe(primary_coeff.get("std_error")) if primary_coeff else None,
                p_value=_safe(p_val),
                ci_lower=_safe(primary_coeff.get("ci_lower")) if primary_coeff else None,
                ci_upper=_safe(primary_coeff.get("ci_upper")) if primary_coeff else None,
                n_obs=int(panel_result.fit.get("n_obs", 0)),
                r_squared=_safe(panel_result.fit.get("r_squared")),
                direction=_direction(_safe(coeff_val)),
                significance=_significance(_safe(p_val)),
                warnings=warnings,
                absorbed_variables=absorbed if absorbed else None,
            )

    except (ModelExecutionError, ValidationAppError) as exc:
        return SpecificationResult(
            spec_id=spec.spec_id,
            status="failed",
            outcome_variable=outcome,
            primary_predictor=predictor,
            controls=valid_controls,
            model_type=model_type,
            failure_reason=str(exc),
        )
    except Exception as exc:
        return SpecificationResult(
            spec_id=spec.spec_id,
            status="failed",
            outcome_variable=outcome,
            primary_predictor=predictor,
            controls=valid_controls,
            model_type=model_type,
            failure_reason=f"Unexpected error: {exc!s}",
        )


def run_discovery(
    config: DiscoveryConfig,
    record: DatasetRecord,
) -> DiscoveryResult:
    discovery_id = str(uuid.uuid4())
    df = record.processed_dataframe if record.processed_dataframe is not None else record.dataframe
    structure = detect_structure(df)

    # Step 1: Screen variables
    eligibility = screen_variables(
        df,
        excluded_variables=config.excluded_variables,
        max_missing_rate=config.max_missing_rate,
        min_observations=config.min_observations,
        min_unique_values=config.min_unique_values,
    )

    # Step 2: Select candidate outcomes
    user_outcomes = config.outcome_variables if config.mode == "guided" else []
    candidate_outcomes = select_candidate_outcomes(
        eligibility,
        max_outcomes=config.maximum_outcomes,
        user_specified=user_outcomes if user_outcomes else None,
    )

    if not candidate_outcomes:
        raise ValidationAppError(
            "No eligible outcome variables found. Check data quality thresholds or "
            "try specifying outcome variables manually in guided mode."
        )

    # Step 3: Select candidate predictors per outcome
    candidate_predictors: dict[str, list[str]] = {}
    for outcome in candidate_outcomes:
        preds = select_candidate_predictors(
            df, outcome, eligibility,
            max_predictors=config.maximum_predictors_per_outcome,
        )
        candidate_predictors[outcome] = preds

    # Step 4: Generate bounded specifications
    all_specs: list[CandidateSpecification] = []
    for outcome in candidate_outcomes:
        preds = candidate_predictors.get(outcome, [])
        controls_pool = [
            e.column_name for e in eligibility
            if e.eligible and e.column_name != outcome and e.column_name not in preds
        ]
        specs = generate_specifications(
            df=df,
            outcome=outcome,
            predictors=preds,
            controls_pool=controls_pool,
            structure=structure,
            max_controls=config.maximum_controls_per_model,
            max_specs=config.maximum_specifications,
            existing_count=len(all_specs),
        )
        all_specs.extend(specs)
        if len(all_specs) >= config.maximum_specifications:
            break

    all_specs = all_specs[:config.maximum_specifications]

    # Step 5: Execute specifications
    all_results: list[SpecificationResult] = []
    for spec in all_specs:
        result = _execute_spec(spec, df, structure)
        all_results.append(result)

    completed_count = sum(1 for r in all_results if r.status == "completed")
    failed_count = sum(1 for r in all_results if r.status in ("failed", "rejected"))

    # Step 6: Multiple-testing correction
    p_values = [
        (r.spec_id, r.p_value)
        for r in all_results
        if r.status == "completed"
    ]
    corrected = apply_correction(
        p_values, config.multiple_testing_method, config.significance_level
    )
    corrected_map = {c.spec_id: c for c in corrected}

    # Step 7: Stability assessment and scoring per (outcome, predictor) pair
    pairs: dict[tuple[str, str], list[SpecificationResult]] = {}
    for r in all_results:
        key = (r.outcome_variable, r.primary_predictor)
        pairs.setdefault(key, []).append(r)

    stability_assessments: list[StabilityAssessment] = []
    findings: list[ExploratoryFinding] = []

    for (outcome, predictor), pair_results in pairs.items():
        stability = assess_stability(outcome, predictor, pair_results, corrected_map)
        stability_assessments.append(stability)

        completed_pair = [r for r in pair_results if r.status == "completed"]
        if not completed_pair:
            continue

        best_corrected_for_pair: CorrectedResult | None = None
        for r in completed_pair:
            cr = corrected_map.get(r.spec_id)
            if cr and cr.raw_p_value is not None:
                if best_corrected_for_pair is None or (cr.raw_p_value < (best_corrected_for_pair.raw_p_value or float("inf"))):
                    best_corrected_for_pair = cr

        finding = score_finding(
            outcome, predictor, pair_results, stability, best_corrected_for_pair
        )
        findings.append(finding)

    findings.sort(key=lambda f: -f.exploratory_score)

    return DiscoveryResult(
        discovery_id=discovery_id,
        dataset_id=record.dataset_id,
        dataset_filename=record.filename,
        mode=config.mode,
        config=config,
        created_at=datetime.now(timezone.utc),
        eligibility_results=eligibility,
        candidate_outcomes=candidate_outcomes,
        candidate_predictors=candidate_predictors,
        specifications_generated=len(all_specs),
        specifications_completed=completed_count,
        specifications_failed=failed_count,
        specification_results=all_results,
        corrected_results=corrected,
        stability_assessments=stability_assessments,
        findings=findings,
        disclaimer=DISCOVERY_DISCLAIMER,
    )
