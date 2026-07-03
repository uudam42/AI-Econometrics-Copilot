"""Pydantic schemas for research reports."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SourceType = Literal["analysis", "comparison"]


class ReportGenerationRequest(BaseModel):
    source_type: SourceType
    source_id: str
    title: str | None = None
    research_question: str | None = None
    significance_level: float = 0.05
    include_appendix: bool = True


class ReportArtifact(BaseModel):
    report_id: str
    source_type: SourceType
    source_id: str
    title: str
    research_question: str | None
    created_at: datetime
    significance_level: float
    sections_included: list[str] = Field(default_factory=list)
    markdown_content: str
    html_content: str
    writing_rules_version: str = "1.0"
    disclaimer: str
