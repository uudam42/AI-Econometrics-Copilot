"""Pydantic schemas for publication-ready academic export."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

ExportSourceType = Literal["analysis", "comparison", "report", "project"]
TableStyle = Literal["academic", "compact", "detailed"]
ExportFormat = Literal["markdown", "html", "docx", "latex", "json"]


class PublicationExportConfig(BaseModel):
    project_id: str | None = None
    source_type: ExportSourceType
    source_id: str

    title: str
    subtitle: str | None = None
    author_name: str | None = None
    institution_name: str | None = None
    course_or_supervisor: str | None = None
    report_date: date | None = None

    selected_model_id: str | None = None
    selected_table_style: TableStyle = "academic"

    include_cover_page: bool = True
    include_executive_summary: bool = True
    include_dataset_section: bool = True
    include_variable_table: bool = True
    include_descriptive_statistics: bool = True
    include_regression_table: bool = True
    include_model_comparison: bool = True
    include_diagnostics: bool = True
    include_figures: bool = True
    include_methodology_section: bool = True
    include_limitations_section: bool = True
    include_appendix: bool = True
    include_reproducibility_appendix: bool = True

    output_formats: list[ExportFormat] = Field(default_factory=lambda: ["docx"])


class FigureMetadata(BaseModel):
    figure_id: str
    figure_type: str
    caption: str
    filename: str
    source_artifact_id: str
    variables: list[str] = Field(default_factory=list)
    model_type: str | None = None
    generated_at: str | None = None


class PublicationExportResult(BaseModel):
    export_id: str
    project_id: str | None
    source_type: ExportSourceType
    source_id: str
    title: str
    created_at: datetime
    available_formats: list[ExportFormat]
    figures: list[FigureMetadata] = Field(default_factory=list)
    sections_included: list[str] = Field(default_factory=list)
    disclaimer: str


class PublicationExportListItem(BaseModel):
    export_id: str
    title: str
    source_type: ExportSourceType
    source_id: str
    created_at: str
    available_formats: list[ExportFormat]
