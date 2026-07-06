"""Demo project and onboarding endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.dataset_service import ingest_upload
from app.storage.repositories import project_repository

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

SAMPLE_DATA_LOCATIONS = [
    Path("sample_data/world_bank_panel_sample.xlsx"),
    Path("/app/sample_data/world_bank_panel_sample.xlsx"),
]

DEMO_PROJECT = {
    "title": "Demo: World Bank Panel Analysis",
    "description": (
        "A sample project using World Bank panel data across multiple countries and years. "
        "This demo walks you through the full research workflow: dataset profiling, "
        "research planning, variable review, model configuration, and results interpretation."
    ),
    "research_question": (
        "How do trade openness and foreign direct investment affect "
        "GDP per capita growth across developing economies?"
    ),
    "tags": ["demo", "panel-data", "world-bank", "growth-economics"],
    "research_context": (
        "Cross-country panel analysis is a cornerstone of empirical growth economics. "
        "This demo uses a simplified World Bank dataset to illustrate how the platform "
        "handles panel structure detection, variable transformation, and model comparison."
    ),
    "methodology_notes": (
        "Consider fixed effects to control for unobserved country heterogeneity, "
        "and compare with pooled OLS and random effects to assess robustness."
    ),
}


class DemoProjectResponse(BaseModel):
    project_id: str
    dataset_id: str
    title: str
    message: str


class OnboardingStatusResponse(BaseModel):
    has_projects: bool
    has_demo: bool
    sample_data_available: bool


def _find_sample_data() -> Path | None:
    for p in SAMPLE_DATA_LOCATIONS:
        if p.exists():
            return p
    return None


@router.get("/status", response_model=OnboardingStatusResponse)
async def onboarding_status() -> OnboardingStatusResponse:
    projects = project_repository.list_all(include_archived=False)
    has_demo = any("demo" in (p.get("tags") or []) for p in projects)
    return OnboardingStatusResponse(
        has_projects=len(projects) > 0,
        has_demo=has_demo,
        sample_data_available=_find_sample_data() is not None,
    )


@router.post("/demo-project", response_model=DemoProjectResponse)
async def create_demo_project() -> DemoProjectResponse:
    sample_path = _find_sample_data()
    if sample_path is None:
        raise HTTPException(
            status_code=404,
            detail="Sample dataset not found. Place world_bank_panel_sample.xlsx in sample_data/.",
        )

    proj = project_repository.create(**DEMO_PROJECT)
    project_id = proj["project_id"]

    content = sample_path.read_bytes()
    record = ingest_upload(
        filename="world_bank_panel_sample.xlsx",
        content=content,
        project_id=project_id,
    )

    project_repository.update(project_id, default_dataset_id=record.dataset_id)

    return DemoProjectResponse(
        project_id=project_id,
        dataset_id=record.dataset_id,
        title=DEMO_PROJECT["title"],
        message="Demo project created with World Bank panel dataset. Start exploring!",
    )
