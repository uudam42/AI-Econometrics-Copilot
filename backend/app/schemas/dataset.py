"""Pydantic schemas for dataset upload, preview, and profiling."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ColumnTypeInfo(BaseModel):
    name: str
    pandas_dtype: str
    inferred_role: Literal[
        "numeric",
        "categorical",
        "datetime",
        "identifier",
        "boolean",
        "text",
        "unknown",
    ]
    unique_count: int
    unique_ratio: float
    role_hints: list[str] = Field(
        default_factory=list,
        description="e.g. Potential Outcome, Possible Entity ID, Possible Time Variable",
    )


class DatasetSummary(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int
    n_columns: int
    columns: list[str]
    uploaded_at: datetime


class DatasetOverviewResponse(BaseModel):
    dataset_id: str
    filename: str
    n_rows: int
    n_columns: int
    column_types: list[ColumnTypeInfo]
    preview_rows: list[dict[str, Any]]
    uploaded_at: datetime


class ColumnQualityReport(BaseModel):
    column: str
    dtype: str
    missing_count: int
    missing_rate: float
    duplicate_value_count: int = 0
    is_constant: bool
    outlier_count: int | None = None
    outlier_method: str | None = None
    zero_ratio: float | None = None
    negative_ratio: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None
    suggested_transformation: str | None = None
    reason: str | None = None


class DatasetQualityReport(BaseModel):
    dataset_id: str
    n_rows: int
    n_columns: int
    duplicate_row_count: int
    duplicate_row_rate: float
    constant_columns: list[str]
    potential_id_columns: list[str]
    potential_time_columns: list[str]
    potential_categorical_columns: list[str]
    columns: list[ColumnQualityReport]


class StructureDetectionResult(BaseModel):
    dataset_type: Literal["panel", "time_series", "cross_sectional", "unknown"]
    entity_column: str | None = None
    time_column: str | None = None
    is_balanced_panel: bool | None = None
    entity_count: int | None = None
    time_period_count: int | None = None
    explanation: str


class DatasetProfileResponse(BaseModel):
    dataset_id: str
    quality: DatasetQualityReport
    structure: StructureDetectionResult
