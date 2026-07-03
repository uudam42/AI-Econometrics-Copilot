"""Pydantic schemas for constrained exploratory relationship discovery."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

DiscoveryMode = Literal["guided", "open"]
MultipleTestingMethod = Literal["benjamini_hochberg", "bonferroni", "none"]
SupportLevel = Literal[
    "strong", "moderate", "weak", "insufficient", "not_suitable",
]
StabilityLabel = Literal[
    "stable",
    "partially_stable",
    "sensitive",
    "insufficient_evidence",
]


class DiscoveryConfig(BaseModel):
    dataset_id: str
    mode: DiscoveryMode = "open"
    outcome_variables: list[str] = Field(default_factory=list)
    excluded_variables: list[str] = Field(default_factory=list)
    maximum_outcomes: int = Field(default=5, ge=1, le=10)
    maximum_predictors_per_outcome: int = Field(default=10, ge=1, le=20)
    maximum_controls_per_model: int = Field(default=4, ge=0, le=8)
    maximum_specifications: int = Field(default=30, ge=1, le=100)
    multiple_testing_method: MultipleTestingMethod = "benjamini_hochberg"
    significance_level: float = Field(default=0.05, gt=0.0, lt=1.0)
    min_observations: int = Field(default=50, ge=10)
    max_missing_rate: float = Field(default=0.30, ge=0.0, le=1.0)
    min_unique_values: int = Field(default=8, ge=2)


class VariableEligibility(BaseModel):
    column_name: str
    eligible: bool
    exclusion_reasons: list[str] = Field(default_factory=list)
    missing_rate: float | None = None
    unique_values: int | None = None
    is_constant: bool = False
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)


class CandidateSpecification(BaseModel):
    spec_id: str
    outcome_variable: str
    primary_predictor: str
    controls: list[str] = Field(default_factory=list)
    model_type: str
    transformations: list[dict[str, Any]] = Field(default_factory=list)
    generation_reason: str


class SpecificationResult(BaseModel):
    spec_id: str
    status: Literal["completed", "failed", "rejected"]
    outcome_variable: str
    primary_predictor: str
    controls: list[str] = Field(default_factory=list)
    model_type: str
    formula: str | None = None
    coefficient: float | None = None
    std_error: float | None = None
    p_value: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    n_obs: int | None = None
    r_squared: float | None = None
    direction: str | None = None
    significance: str = ""
    warnings: list[str] = Field(default_factory=list)
    failure_reason: str | None = None
    absorbed_variables: list[str] | None = None


class CorrectedResult(BaseModel):
    spec_id: str
    raw_p_value: float | None = None
    adjusted_p_value: float | None = None
    correction_method: str
    passes_threshold: bool = False


class StabilityAssessment(BaseModel):
    outcome_variable: str
    primary_predictor: str
    n_specifications: int
    n_completed: int
    n_corrected_significant: int
    direction_consistent: bool
    significance_consistent: bool
    coefficient_range: list[float] | None = None
    stability_label: StabilityLabel
    specifications_used: list[str] = Field(default_factory=list)


class FindingScoreComponent(BaseModel):
    criterion: str
    score: float
    weight: float
    explanation: str


class ExploratoryFinding(BaseModel):
    finding_id: str
    outcome_variable: str
    primary_predictor: str
    relationship_direction: str
    exploratory_score: float
    support_level: SupportLevel
    raw_p_value: float | None = None
    adjusted_q_value: float | None = None
    multiple_testing_method: str
    stability_label: StabilityLabel
    best_coefficient: float | None = None
    best_n_obs: int | None = None
    best_r_squared: float | None = None
    score_breakdown: list[FindingScoreComponent]
    specification_ids: list[str]
    warnings: list[str] = Field(default_factory=list)


class DiscoveryResult(BaseModel):
    discovery_id: str
    dataset_id: str
    dataset_filename: str
    mode: DiscoveryMode
    config: DiscoveryConfig
    created_at: datetime
    eligibility_results: list[VariableEligibility]
    candidate_outcomes: list[str]
    candidate_predictors: dict[str, list[str]]
    specifications_generated: int
    specifications_completed: int
    specifications_failed: int
    specification_results: list[SpecificationResult]
    corrected_results: list[CorrectedResult]
    stability_assessments: list[StabilityAssessment]
    findings: list[ExploratoryFinding]
    disclaimer: str


DISCOVERY_DISCLAIMER = (
    "Exploratory results are generated from multiple tested specifications. "
    "They should be treated as hypothesis-generating and require theory-driven "
    "validation, pre-specified analysis, or independent-sample confirmation."
)

UNCORRECTED_WARNING = (
    "No multiple-testing correction is applied. Results are highly susceptible "
    "to false positives. This setting should only be used for educational or "
    "diagnostic purposes."
)
