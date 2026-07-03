"""Generate bounded candidate specifications for exploratory discovery.

Builds a limited set of economically interpretable model specifications
from screened outcome and predictor variables. Does not generate arbitrary
interactions, lags, or exhaustive control-variable subsets.
"""
from __future__ import annotations

import uuid

import pandas as pd

from app.schemas.dataset import StructureDetectionResult
from app.schemas.discovery import CandidateSpecification


def _should_log_transform(series: pd.Series) -> bool:
    clean = series.dropna()
    if clean.empty or len(clean) < 10:
        return False
    all_positive = bool((clean > 0).all())
    skew = float(clean.skew()) if len(clean) > 2 else 0.0
    return all_positive and abs(skew) > 2.0


def generate_specifications(
    df: pd.DataFrame,
    outcome: str,
    predictors: list[str],
    controls_pool: list[str],
    structure: StructureDetectionResult,
    max_controls: int = 4,
    max_specs: int = 30,
    existing_count: int = 0,
) -> list[CandidateSpecification]:
    specs: list[CandidateSpecification] = []
    budget = max_specs - existing_count

    has_panel = (
        structure.dataset_type == "panel"
        and structure.entity_column is not None
        and structure.time_column is not None
    )

    use_log_dv = _should_log_transform(df[outcome])
    available_controls = [c for c in controls_pool if c != outcome and c not in predictors][:max_controls]

    for predictor in predictors:
        if len(specs) >= budget:
            break

        # 1. Bivariate baseline: OLS
        specs.append(CandidateSpecification(
            spec_id=str(uuid.uuid4()),
            outcome_variable=outcome,
            primary_predictor=predictor,
            controls=[],
            model_type="ols",
            transformations=[],
            generation_reason=f"Bivariate baseline: {outcome} ~ {predictor}",
        ))

        # 2. With controls: Robust OLS
        if available_controls and len(specs) < budget:
            specs.append(CandidateSpecification(
                spec_id=str(uuid.uuid4()),
                outcome_variable=outcome,
                primary_predictor=predictor,
                controls=available_controls,
                model_type="robust_ols",
                transformations=[],
                generation_reason=(
                    f"Controlled specification with robust SE: {outcome} ~ {predictor} + "
                    + " + ".join(available_controls)
                ),
            ))

        # 3. Log-DV variant if valid
        if use_log_dv and len(specs) < budget:
            log_col = f"log_{outcome}"
            specs.append(CandidateSpecification(
                spec_id=str(uuid.uuid4()),
                outcome_variable=log_col,
                primary_predictor=predictor,
                controls=available_controls[:2],
                model_type="robust_ols",
                transformations=[{
                    "operation": "log_transform",
                    "columns": [outcome],
                }],
                generation_reason=(
                    f"Log-transformed DV for semi-elasticity: log({outcome}) ~ {predictor}"
                ),
            ))

        # 4. Panel FE if structure supports it
        if has_panel and len(specs) < budget:
            specs.append(CandidateSpecification(
                spec_id=str(uuid.uuid4()),
                outcome_variable=outcome,
                primary_predictor=predictor,
                controls=available_controls[:2],
                model_type="fixed_effects",
                transformations=[],
                generation_reason=(
                    f"Panel FE exploiting within-entity variation: {outcome} ~ {predictor}"
                ),
            ))

        # 5. Two-Way FE if panel
        if has_panel and len(specs) < budget:
            specs.append(CandidateSpecification(
                spec_id=str(uuid.uuid4()),
                outcome_variable=outcome,
                primary_predictor=predictor,
                controls=available_controls[:2],
                model_type="two_way_fixed_effects",
                transformations=[],
                generation_reason=(
                    f"Two-Way FE controlling entity + time effects: {outcome} ~ {predictor}"
                ),
            ))

    return specs
