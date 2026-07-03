"""Pydantic schemas for research project workspaces."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProjectStatus = Literal["draft", "active", "archived"]


class ProjectCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    research_question: str = ""
    tags: list[str] = Field(default_factory=list)
    research_context: str = ""
    notes: str = ""
    methodology_notes: str = ""


class ProjectUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    research_question: str | None = None
    status: ProjectStatus | None = None
    tags: list[str] | None = None
    default_dataset_id: str | None = None
    research_context: str | None = None
    notes: str | None = None
    methodology_notes: str | None = None


class ProjectResponse(BaseModel):
    project_id: str
    title: str
    description: str
    research_question: str
    status: ProjectStatus
    tags: list[str]
    default_dataset_id: str | None
    research_context: str
    notes: str
    methodology_notes: str
    created_at: str
    updated_at: str


class TimelineEvent(BaseModel):
    event_type: str
    artifact_type: str | None
    artifact_id: str | None
    description: str
    created_at: str | None


class ProjectArtifacts(BaseModel):
    datasets: list[dict[str, Any]]
    plans: list[dict[str, Any]]
    analyses: list[dict[str, Any]]
    comparisons: list[dict[str, Any]]
    reports: list[dict[str, Any]]
    discoveries: list[dict[str, Any]]


class ProjectExport(BaseModel):
    project: ProjectResponse
    artifacts: ProjectArtifacts
    timeline: list[TimelineEvent]
    disclaimer: str = (
        "This bundle preserves the project configuration, transformation history, "
        "model outputs, diagnostics, comparisons, reports, and exploratory discovery "
        "results. It does not by itself establish causal claims."
    )
