"""Orchestration service for the Quick Analyze workflow.

Chains upload → profile → structure → plan/recommend → confirm → run → summarize
into a single session that persists in the database and links back to the
standard project/dataset/analysis objects.

No LLM is used. All decisions are deterministic and require user confirmation
of at least: dependent variable, primary explanatory variable, recommended
model, and any transformation before execution.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.analysis.model_runner import run_analysis
from app.analysis.model_recommender import recommend_model
from app.analysis.research_planner import generate_plan
from app.analysis.summary_generator import generate_beginner_summary
from app.core.errors import AppError, ValidationAppError
from app.core.logging import get_logger
from app.schemas.modeling import (
    AnalysisConfigurationRequest,
    ModelType,
    TransformationOperation,
    VariableSelectionRequest,
)
from app.schemas.planning import CandidateVariable, ResearchPlan
from app.schemas.quick_analyze import (
    BeginnerSummary,
    ConfirmationRequest,
    QuickAnalyzeSession,
    RecommendationCard,
)
from app.services.dataset_service import ingest_upload
from app.services.structure_detector import detect_structure
from app.storage.database import get_session
from app.storage.models import QuickAnalyzeSessionRow
from app.storage.repositories import (
    analysis_repository,
    dataset_repository,
    project_repository,
)

logger = get_logger(__name__)

_EXPLORATORY_QUESTION = (
    "Explore the key relationships in this dataset without a specific hypothesis."
)


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _load_row(session_id: str) -> QuickAnalyzeSessionRow:
    with get_session() as db:
        row = db.get(QuickAnalyzeSessionRow, session_id)
        if row is None:
            raise ValidationAppError(
                f"Quick Analyze session '{session_id}' not found.",
                details={"session_id": session_id},
            )
        db.expunge(row)
        return row


def _save_row(row: QuickAnalyzeSessionRow) -> None:
    row.updated_at = _now()
    with get_session() as db:
        db.merge(row)
        db.commit()


def _row_to_session(row: QuickAnalyzeSessionRow) -> QuickAnalyzeSession:
    rec_raw = row.recommendation_json
    recommendation = RecommendationCard(**rec_raw) if rec_raw else None

    sum_raw = row.summary_json
    summary = BeginnerSummary(**sum_raw) if sum_raw else None

    return QuickAnalyzeSession(
        session_id=row.id,
        stage=row.stage,
        project_id=row.project_id,
        dataset_id=row.dataset_id,
        plan_id=row.plan_id,
        analysis_id=row.analysis_id,
        research_question=row.research_question,
        analysis_intent=row.analysis_intent or "association",
        recommendation=recommendation,
        summary=summary,
        progress_message=row.progress_message or "",
        error_message=row.error_message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ---------------------------------------------------------------------------
# Stage 1 — Upload
# ---------------------------------------------------------------------------

def create_session_with_upload(
    filename: str,
    content: bytes,
    research_question: str | None = None,
    analysis_intent: str = "association",
) -> QuickAnalyzeSession:
    """Upload file → create project + dataset → return session at 'uploaded'."""
    record = ingest_upload(filename=filename, content=content)
    project_title = f"Analysis of {Path(filename).stem}"

    proj = project_repository.create(
        title=project_title,
        description="Created automatically by Quick Analyze.",
        research_question=research_question or "",
        tags=["quick-analyze"],
    )
    project_id = proj["project_id"]
    record.project_id = project_id
    dataset_repository.set_project(record.dataset_id, project_id)

    now = _now()
    row = QuickAnalyzeSessionRow(
        id=str(uuid.uuid4()),
        stage="uploaded",
        project_id=project_id,
        dataset_id=record.dataset_id,
        research_question=research_question or None,
        analysis_intent=analysis_intent,
        progress_message="Dataset uploaded. Ready to analyse.",
        created_at=now,
        updated_at=now,
    )
    with get_session() as db:
        db.add(row)
        db.commit()

    return _row_to_session(row)


# ---------------------------------------------------------------------------
# Stage 2 — Plan and recommend
# ---------------------------------------------------------------------------

def _pick_best_candidate(
    candidates: list[CandidateVariable],
    role: str,
) -> str | None:
    matches = [c for c in candidates if c.role == role]
    if not matches:
        return None
    return max(matches, key=lambda c: c.confidence).column_name


def _build_recommendation(
    plan: ResearchPlan,
    df: pd.DataFrame,
    structure,
    is_exploratory: bool,
) -> RecommendationCard:
    candidates = plan.candidate_variables
    dep = _pick_best_candidate(candidates, "dependent_variable")
    primary = _pick_best_candidate(candidates, "primary_independent_variable")
    controls = [
        c.column_name for c in candidates if c.role == "control_variable"
    ]
    entity = _pick_best_candidate(candidates, "entity_column")
    time = _pick_best_candidate(candidates, "time_column")

    needs_user_input: str | None = None
    if dep is None:
        needs_user_input = "outcome variable"
    elif primary is None:
        needs_user_input = "main explanatory variable"

    has_entity = entity is not None
    has_time = time is not None
    n_entities: int | None = None
    n_periods: int | None = None
    if has_entity and entity and entity in df.columns:
        n_entities = int(df[entity].nunique())
    if has_time and time and time in df.columns:
        n_periods = int(df[time].nunique())

    rec = recommend_model(
        has_entity_column=has_entity,
        has_time_column=has_time,
        n_entities=n_entities,
        n_periods=n_periods,
        breusch_pagan=None,
        hausman=None,
        n_obs=len(df),
        cluster_by_entity=has_entity,
    )

    model_labels = {
        "ols": "OLS Regression",
        "robust_ols": "Robust OLS",
        "pooled_ols": "Pooled OLS",
        "fixed_effects": "Fixed Effects",
        "random_effects": "Random Effects",
        "two_way_fixed_effects": "Two-Way Fixed Effects",
    }

    transform_suggestions = [
        f"Consider log-transforming '{t.columns[0]}' (right-skewed positive variable)"
        for t in plan.suggested_transformations
        if t.operation == "log_transform" and t.columns
    ]

    return RecommendationCard(
        outcome_variable=dep or "(not detected — please select)",
        main_variable=primary or "(not detected — please select)",
        control_variables=controls,
        entity_column=entity,
        time_column=time,
        detected_structure=plan.detected_structure_summary,
        recommended_model=model_labels.get(rec.recommended_model, rec.recommended_model),
        recommended_model_type=rec.recommended_model,
        transformation_suggestions=transform_suggestions,
        why_reasons=rec.reasons,
        warnings=rec.warnings + [w for c in candidates for w in c.warnings],
        is_exploratory=is_exploratory,
        needs_user_input=needs_user_input,
    )


def plan_session(session_id: str) -> QuickAnalyzeSession:
    """Run profiling, structure detection, and planning. Returns recommendation."""
    row = _load_row(session_id)
    if not row.dataset_id:
        raise ValidationAppError("Session has no dataset attached.")

    record = dataset_repository.get(row.dataset_id)
    df = record.dataframe

    row.progress_message = "Checking data quality and structure…"
    _save_row(row)

    structure = detect_structure(df)

    question = row.research_question or _EXPLORATORY_QUESTION
    is_exploratory = not bool(row.research_question)

    try:
        plan = generate_plan(
            dataset_id=row.dataset_id,
            df=df,
            research_question=question,
            structure=structure,
        )
    except Exception as exc:
        row.stage = "failed"
        row.error_message = str(exc)
        _save_row(row)
        raise

    recommendation = _build_recommendation(plan, df, structure, is_exploratory)

    row.stage = "awaiting_confirmation"
    row.plan_id = plan.plan_id
    row.recommendation_json = recommendation.model_dump()
    row.progress_message = (
        "Ready to review recommendation." if recommendation.needs_user_input is None
        else f"Please select the {recommendation.needs_user_input} to continue."
    )
    _save_row(row)
    return _row_to_session(row)


# ---------------------------------------------------------------------------
# Stage 3 — Confirm and run
# ---------------------------------------------------------------------------

def confirm_and_run(
    session_id: str,
    confirmation: ConfirmationRequest,
) -> QuickAnalyzeSession:
    """Accept user confirmation → apply transformations → run model → summarize."""
    row = _load_row(session_id)
    if not row.dataset_id:
        raise ValidationAppError("Session has no dataset attached.")

    record = dataset_repository.get(row.dataset_id)

    row.stage = "running"
    row.progress_message = "Running econometric model…"
    _save_row(row)

    transformations: list[TransformationOperation] = []
    for col in confirmation.apply_log_transform_to:
        transformations.append(
            TransformationOperation(operation="log_transform", columns=[col])
        )

    vs = VariableSelectionRequest(
        dataset_id=row.dataset_id,
        dependent_variable=confirmation.dependent_variable,
        primary_independent_variable=confirmation.primary_independent_variable,
        control_variables=confirmation.control_variables,
        entity_column=confirmation.entity_column,
        time_column=confirmation.time_column,
    )

    model_type: ModelType = confirmation.model_type  # type: ignore[assignment]

    config = AnalysisConfigurationRequest(
        dataset_id=row.dataset_id,
        variable_selection=vs,
        transformations=transformations,
        model_type=model_type,
        include_intercept=True,
        robust_standard_errors=(
            confirmation.entity_column is not None
            or model_type in ("robust_ols",)
        ),
        cluster_standard_errors_by_entity=(
            confirmation.entity_column is not None
        ),
    )

    try:
        result, diagnostics = run_analysis(config, record)
    except AppError:
        row.stage = "failed"
        row.error_message = "Analysis failed. Please review the variable selection and try again."
        _save_row(row)
        raise
    except Exception as exc:
        row.stage = "failed"
        row.error_message = f"Unexpected error: {exc}"
        _save_row(row)
        raise

    ar = analysis_repository.create(
        dataset_id=record.dataset_id,
        dataset_filename=record.filename,
        config=config,
        result=result,
        diagnostics=diagnostics,
        transformation_log=result.transformation_log,
        project_id=row.project_id,
    )
    result.analysis_id = ar.analysis_id
    diagnostics.analysis_id = ar.analysis_id
    ar.result = result
    ar.diagnostics = diagnostics
    analysis_repository.update_result(ar.analysis_id, result, diagnostics)

    summary = generate_beginner_summary(
        result=result,
        diagnostics=diagnostics,
        dataset_filename=record.filename,
        dependent_variable=confirmation.dependent_variable,
        primary_variable=confirmation.primary_independent_variable,
    )

    row.stage = "complete"
    row.analysis_id = ar.analysis_id
    row.analysis_intent = confirmation.analysis_intent
    row.summary_json = summary.model_dump()
    row.progress_message = "Analysis complete."
    _save_row(row)
    return _row_to_session(row)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_session_detail(session_id: str) -> QuickAnalyzeSession:
    return _row_to_session(_load_row(session_id))
