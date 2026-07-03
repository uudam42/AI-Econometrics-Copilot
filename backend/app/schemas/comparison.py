"""Pydantic schemas for multi-model comparison."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.modeling import ModelType, TransformationOperation, VariableSelectionRequest

ComparisonStatus = Literal["completed", "failed", "unavailable"]


class ModelFitSummary(BaseModel):
    r_squared: float | None = None
    adj_r_squared: float | None = None
    within_r_squared: float | None = None
    between_r_squared: float | None = None
    overall_r_squared: float | None = None
    aic: float | None = None
    bic: float | None = None
    f_statistic: float | None = None
    n_obs: int | None = None
    n_entities: int | None = None
    n_time_periods: int | None = None


class DiagnosticSummary(BaseModel):
    max_vif: float | None = None
    heteroskedasticity_detected: bool | None = None
    hausman_rejects_re: bool | None = None
    hausman_p_value: float | None = None
    durbin_watson: float | None = None


class CoefficientStabilityEntry(BaseModel):
    """How the primary IV coefficient behaves across completed models."""

    model_type: ModelType
    model_label: str
    coefficient: float | None
    std_error: float | None
    p_value: float | None
    ci_lower: float | None
    ci_upper: float | None
    significance: str
    direction: str  # "positive", "negative", "zero", "unavailable"


class ModelComparisonEntry(BaseModel):
    model_type: ModelType
    model_label: str
    status: ComparisonStatus
    reason: str | None = None
    formula: str | None = None
    fit_metrics: ModelFitSummary | None = None
    diagnostic_summary: DiagnosticSummary | None = None
    standard_error_type: str | None = None
    entity_effects: bool | None = None
    time_effects: bool | None = None
    warnings: list[str] = Field(default_factory=list)


class ModelScoreComponent(BaseModel):
    criterion: str
    score: int
    weight: float
    explanation: str


class ModelSelectionRecommendation(BaseModel):
    recommended_model: ModelType
    confidence: Literal["high", "medium", "low"]
    score: int
    reasons: list[str]
    warnings: list[str]
    score_breakdown: list[ModelScoreComponent]
    alternative_models: list[dict[str, str]] = Field(default_factory=list)


class ComparisonRequest(BaseModel):
    dataset_id: str
    variable_selection: VariableSelectionRequest
    transformations: list[TransformationOperation] = Field(default_factory=list)
    candidate_models: list[ModelType]
    cluster_standard_errors_by_entity: bool = False


class ComparisonResult(BaseModel):
    comparison_id: str
    dataset_id: str
    dataset_filename: str
    created_at: datetime
    variable_selection: VariableSelectionRequest
    transformation_summary: str
    models: list[ModelComparisonEntry]
    coefficient_stability: list[CoefficientStabilityEntry]
    recommendation: ModelSelectionRecommendation
    disclaimer: str


class ComparisonExportArtifact(BaseModel):
    comparison_id: str
    dataset_id: str
    dataset_filename: str
    created_at: datetime
    variable_selection: dict[str, Any]
    transformations: list[dict[str, Any]]
    candidate_models: list[str]
    model_results: list[dict[str, Any]]
    recommendation: dict[str, Any]
    software_versions: dict[str, str]
    disclaimer: str
