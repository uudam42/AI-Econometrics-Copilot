"""Orchestrate plan generation from a research question + dataset.

Combines the question parser, variable matcher, column typing,
structure detection, and econometric rules to produce a ResearchPlan
that the user must review and approve before any model is run.
"""
from __future__ import annotations

import uuid

import pandas as pd

from app.analysis.economics_synonyms import get_concept_for_token
from app.analysis.research_question_parser import parse_research_question
from app.analysis.variable_matcher import match_variables
from app.schemas.dataset import StructureDetectionResult
from app.schemas.planning import (
    CandidateVariable,
    ResearchPlan,
    SuggestedModel,
    SuggestedTransformation,
)
from app.services.column_typing import infer_all_column_types


def _suggest_transformations(
    df: pd.DataFrame,
    candidates: list[CandidateVariable],
) -> list[SuggestedTransformation]:
    suggestions: list[SuggestedTransformation] = []
    numeric_candidates = [
        c for c in candidates
        if c.role not in ("entity_column", "time_column")
        and c.column_name in df.columns
        and pd.api.types.is_numeric_dtype(df[c.column_name])
    ]

    for cand in numeric_candidates:
        series = df[cand.column_name].dropna()
        if series.empty:
            continue

        all_positive = bool((series > 0).all())
        skew = float(series.skew()) if len(series) > 2 else 0.0

        if all_positive and abs(skew) > 2.0:
            suggestions.append(SuggestedTransformation(
                operation="log_transform",
                columns=[cand.column_name],
                confidence=0.7,
                reason=f"'{cand.column_name}' is positive and heavily skewed "
                       f"(skewness={skew:.2f}); log transform may stabilize variance.",
                requires_user_confirmation=True,
            ))

    return suggestions


def _suggest_models(
    structure: StructureDetectionResult,
    has_entity: bool,
    has_time: bool,
    n_candidates: int,
) -> list[SuggestedModel]:
    models: list[SuggestedModel] = []

    models.append(SuggestedModel(
        model_type="ols",
        confidence=0.5,
        reasons=["Baseline OLS serves as a reference model for any specification."],
        requirements=[],
        warnings=[],
    ))

    if structure.dataset_type == "panel" and has_entity and has_time:
        models.append(SuggestedModel(
            model_type="fixed_effects",
            confidence=0.85,
            reasons=[
                "Panel structure detected with entity and time columns.",
                "Entity fixed effects control for time-invariant unobserved heterogeneity.",
            ],
            requirements=["entity_column", "time_column"],
            warnings=[],
        ))
        models.append(SuggestedModel(
            model_type="random_effects",
            confidence=0.6,
            reasons=[
                "Random effects is appropriate if entity effects are uncorrelated with regressors.",
                "Use the Hausman test to compare with fixed effects.",
            ],
            requirements=["entity_column", "time_column"],
            warnings=["Hausman test should be run to validate this choice."],
        ))
        models.append(SuggestedModel(
            model_type="two_way_fixed_effects",
            confidence=0.7,
            reasons=[
                "Two-way fixed effects control for both entity and time heterogeneity.",
            ],
            requirements=["entity_column", "time_column"],
            warnings=["May absorb variables that are collinear with entity or time dummies."],
        ))

    if structure.dataset_type == "panel":
        models.append(SuggestedModel(
            model_type="robust_ols",
            confidence=0.55,
            reasons=["Robust standard errors (HC1) guard against heteroskedasticity."],
            requirements=[],
            warnings=[
                "Does not exploit panel structure — consider using fixed effects."
            ] if has_entity and has_time else [],
        ))

    if structure.dataset_type in ("cross_sectional", "unknown"):
        models.append(SuggestedModel(
            model_type="robust_ols",
            confidence=0.65,
            reasons=[
                "HC1-robust standard errors are recommended for cross-sectional data.",
            ],
            requirements=[],
            warnings=[],
        ))

    models.sort(key=lambda m: -m.confidence)
    return models


def _build_structure_summary(structure: StructureDetectionResult) -> str:
    parts = [f"Dataset type: {structure.dataset_type}"]
    if structure.entity_column:
        parts.append(f"entity column: '{structure.entity_column}'")
    if structure.time_column:
        parts.append(f"time column: '{structure.time_column}'")
    if structure.entity_count is not None:
        parts.append(f"{structure.entity_count} entities")
    if structure.time_period_count is not None:
        parts.append(f"{structure.time_period_count} time periods")
    if structure.is_balanced_panel is not None:
        parts.append("balanced" if structure.is_balanced_panel else "unbalanced")
    return "; ".join(parts) + "."


def generate_plan(
    dataset_id: str,
    df: pd.DataFrame,
    research_question: str,
    structure: StructureDetectionResult,
    context: str | None = None,
    preferred_outcome: str | None = None,
    preferred_primary_iv: str | None = None,
) -> ResearchPlan:
    parsed = parse_research_question(research_question)

    match_result = match_variables(
        df,
        parsed.extracted_tokens,
        preferred_outcome=preferred_outcome,
        preferred_primary_iv=preferred_primary_iv,
    )

    has_entity = any(
        c.role == "entity_column" for c in match_result.candidates
    )
    has_time = any(
        c.role == "time_column" for c in match_result.candidates
    )

    transformations = _suggest_transformations(df, match_result.candidates)

    models = _suggest_models(
        structure,
        has_entity=has_entity,
        has_time=has_time,
        n_candidates=len(match_result.candidates),
    )

    ambiguities = list(match_result.ambiguities)

    if parsed.detected_intent == "unclear":
        ambiguities.append(
            "Could not determine the analysis intent from your question. "
            "Please clarify whether you are looking for an association, "
            "an exploratory overview, or something else."
        )

    return ResearchPlan(
        plan_id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        research_question=parsed.original,
        normalized_question=parsed.normalized,
        user_context=context,
        inferred_analysis_intent=parsed.detected_intent,
        candidate_variables=match_result.candidates,
        suggested_transformations=transformations,
        suggested_models=models,
        detected_structure_summary=_build_structure_summary(structure),
        ambiguities=ambiguities,
        causal_warning=parsed.causal_warning,
        user_approval_required=True,
    )
