"""Pydantic schemas for the Quick Analyze workflow."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

QuickAnalyzeStage = Literal[
    "created",
    "uploaded",
    "profiled",
    "planned",
    "awaiting_confirmation",
    "running",
    "complete",
    "failed",
]

AnalysisIntentChoice = Literal["association", "exploratory"]


class QuickAnalyzeSession(BaseModel):
    session_id: str
    stage: QuickAnalyzeStage
    project_id: str | None = None
    dataset_id: str | None = None
    plan_id: str | None = None
    analysis_id: str | None = None
    research_question: str | None = None
    analysis_intent: AnalysisIntentChoice = "association"
    recommendation: "RecommendationCard | None" = None
    summary: "BeginnerSummary | None" = None
    progress_message: str = ""
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class RecommendationCard(BaseModel):
    """One-screen summary of the recommended analysis for user confirmation."""
    outcome_variable: str
    main_variable: str
    control_variables: list[str] = Field(default_factory=list)
    detected_structure: str
    recommended_model: str
    recommended_model_type: str
    transformation_suggestions: list[str] = Field(default_factory=list)
    why_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    is_exploratory: bool = False
    needs_user_input: str | None = None


class ConfirmationRequest(BaseModel):
    dependent_variable: str
    primary_independent_variable: str
    control_variables: list[str] = Field(default_factory=list)
    entity_column: str | None = None
    time_column: str | None = None
    model_type: str
    apply_log_transform_to: list[str] = Field(default_factory=list)
    analysis_intent: AnalysisIntentChoice = "association"


class DiagnosticsStatusCard(BaseModel):
    data_quality: Literal["Good", "Needs review"]
    model_fit: Literal["Available", "Limited"]
    multicollinearity: Literal["Low concern", "Moderate concern", "High concern"]
    heteroskedasticity: Literal["Not detected", "Detected — robust standard errors recommended"]
    panel_structure: Literal["Detected", "Not detected"]
    causal_interpretation: Literal["Association only"]


class BeginnerSummary(BaseModel):
    """Plain-language summary of analysis results for non-technical users."""
    headline: str
    dataset_description: str
    model_used: str
    main_finding: str
    is_significant: bool
    significance_threshold: float = 0.05
    causal_warning: str
    key_warnings: list[str] = Field(default_factory=list)
    diagnostics_status: DiagnosticsStatusCard
    next_actions: list[str] = Field(default_factory=list)


class QuickAnalyzeUploadResponse(BaseModel):
    session_id: str
    dataset_id: str
    project_id: str
    filename: str
    n_rows: int
    n_columns: int
    stage: QuickAnalyzeStage


class QuickAnalyzePlanResponse(BaseModel):
    session_id: str
    stage: QuickAnalyzeStage
    recommendation: RecommendationCard
    progress_message: str


class QuickAnalyzeRunResponse(BaseModel):
    session_id: str
    stage: QuickAnalyzeStage
    analysis_id: str
    summary: BeginnerSummary
    progress_message: str


class QuickAnalyzeSessionDetail(BaseModel):
    session: QuickAnalyzeSession
    workspace_url: str | None = None
