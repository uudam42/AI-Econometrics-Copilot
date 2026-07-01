"""Pydantic schemas for modeling configuration and analysis results."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

ModelType = Literal[
    "ols",
    "robust_ols",
    "pooled_ols",
    "fixed_effects",
    "random_effects",
    "two_way_fixed_effects",
]

TransformationOp = Literal[
    "drop_duplicates",
    "drop_missing_rows",
    "median_imputation",
    "mean_imputation",
    "winsorize",
    "log_transform",
    "standardize",
]


class VariableSelectionRequest(BaseModel):
    dataset_id: str
    dependent_variable: str
    primary_independent_variable: str
    control_variables: list[str] = Field(default_factory=list)
    entity_column: str | None = None
    time_column: str | None = None

    @model_validator(mode="after")
    def check_no_overlap(self) -> "VariableSelectionRequest":
        all_vars = (
            [self.dependent_variable, self.primary_independent_variable]
            + self.control_variables
        )
        if len(all_vars) != len(set(all_vars)):
            raise ValueError(
                "Dependent variable, primary independent variable, and control "
                "variables must all be distinct."
            )
        return self


class TransformationOperation(BaseModel):
    operation: TransformationOp
    columns: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)


class AnalysisConfigurationRequest(BaseModel):
    dataset_id: str
    variable_selection: VariableSelectionRequest
    transformations: list[TransformationOperation] = Field(default_factory=list)
    model_type: ModelType
    include_intercept: bool = True
    robust_standard_errors: bool = False
    cluster_standard_errors_by_entity: bool = False


class TransformationLogEntry(BaseModel):
    step: int
    operation: str
    columns: list[str]
    parameters: dict[str, Any]
    reason: str
    rows_before: int
    rows_after: int
    created_columns: list[str] = Field(default_factory=list)


class TransformResult(BaseModel):
    dataset_id: str
    rows_before: int
    rows_after: int
    columns_added: list[str]
    log: list[TransformationLogEntry]


class CoefficientResult(BaseModel):
    variable: str
    coefficient: float
    std_error: float
    t_stat: float
    p_value: float
    ci_lower: float
    ci_upper: float
    significance: str  # "", "*", "**", "***"


class ModelFitStatistics(BaseModel):
    r_squared: float | None
    adj_r_squared: float | None
    f_statistic: float | None
    f_pvalue: float | None
    aic: float | None
    bic: float | None
    n_obs: int
    formula: str


class PlotData(BaseModel):
    fitted_values: list[float]
    actual_values: list[float]
    residuals: list[float]


class VIFResult(BaseModel):
    variable: str
    vif: float
    risk_level: str
    interpretation: str


class DiagnosticTestResult(BaseModel):
    name: str
    statistic: float | None
    p_value: float | None
    interpretation: str
    available: bool = True
    unavailable_reason: str | None = None


class HausmanTestResult(BaseModel):
    available: bool
    statistic: float | None = None
    degrees_of_freedom: int | None = None
    p_value: float | None = None
    recommendation: str | None = None
    unavailable_reason: str | None = None


class DescriptiveStats(BaseModel):
    variable: str
    count: int
    mean: float | None
    std: float | None
    min: float | None
    q25: float | None
    median: float | None
    q75: float | None
    max: float | None
    missing_count: int
    skewness: float | None


class CorrelationMatrixResult(BaseModel):
    variables: list[str]
    matrix: list[list[float | None]]


class ModelDiagnosticsResponse(BaseModel):
    analysis_id: str
    descriptive_stats: list[DescriptiveStats]
    correlation_matrix: CorrelationMatrixResult
    vif: list[VIFResult]
    breusch_pagan: DiagnosticTestResult
    jarque_bera: DiagnosticTestResult
    durbin_watson: DiagnosticTestResult
    hausman: HausmanTestResult


class ModelRecommendation(BaseModel):
    recommended_model: ModelType
    confidence: Literal["high", "medium", "low"]
    reasons: list[str]
    warnings: list[str]


class AnalysisResult(BaseModel):
    analysis_id: str
    dataset_id: str
    dataset_filename: str
    created_at: datetime
    model_type: ModelType
    formula: str
    variable_selection: VariableSelectionRequest
    transformation_log: list[TransformationLogEntry]
    coefficients: list[CoefficientResult]
    fit: ModelFitStatistics
    plot_data: PlotData | None
    model_metadata: dict[str, Any]
    recommendation: ModelRecommendation | None
    disclaimer: str


class AnalysisExportArtifact(BaseModel):
    analysis_id: str
    dataset_id: str
    dataset_filename: str
    created_at: datetime
    model_type: ModelType
    formula: str
    variable_selection: dict[str, Any]
    transformations: list[dict[str, Any]]
    transformation_log: list[dict[str, Any]]
    coefficients: list[dict[str, Any]]
    fit: dict[str, Any]
    diagnostics_summary: dict[str, Any]
    model_metadata: dict[str, Any]
    recommendation: dict[str, Any] | None
    software_versions: dict[str, str]
    disclaimer: str
