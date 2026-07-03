"""Pydantic schemas for natural-language research planning."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

VariableRole = Literal[
    "dependent_variable",
    "primary_independent_variable",
    "control_variable",
    "entity_column",
    "time_column",
    "unresolved",
]

AnalysisIntent = Literal[
    "association",
    "exploratory",
    "causal_claim_requested",
    "unclear",
]


class CandidateVariable(BaseModel):
    column_name: str
    role: VariableRole
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SuggestedTransformation(BaseModel):
    operation: str
    columns: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    requires_user_confirmation: bool = True


class SuggestedModel(BaseModel):
    model_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: list[str]
    requirements: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    plan_id: str
    dataset_id: str
    research_question: str
    normalized_question: str
    user_context: str | None = None
    inferred_analysis_intent: AnalysisIntent
    candidate_variables: list[CandidateVariable]
    suggested_transformations: list[SuggestedTransformation]
    suggested_models: list[SuggestedModel]
    detected_structure_summary: str
    ambiguities: list[str]
    causal_warning: str
    user_approval_required: bool = True


class PlanGenerationRequest(BaseModel):
    dataset_id: str
    research_question: str
    context: str | None = None
    preferred_outcome: str | None = None
    preferred_primary_independent_variable: str | None = None


class PlanApprovalRequest(BaseModel):
    dependent_variable: str
    primary_independent_variable: str
    control_variables: list[str] = Field(default_factory=list)
    entity_column: str | None = None
    time_column: str | None = None
    approved_transformations: list[dict[str, Any]] = Field(default_factory=list)
    selected_candidate_models: list[str] = Field(default_factory=list)


class PlanApprovalResult(BaseModel):
    plan_id: str
    approved: bool
    variable_selection: dict[str, Any]
    transformations: list[dict[str, Any]]
    candidate_models: list[str]
    redirect_path: str
