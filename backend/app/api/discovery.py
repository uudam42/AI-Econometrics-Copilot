"""Exploratory discovery endpoints: run, retrieve, findings, export, handoff."""
from __future__ import annotations

from fastapi import APIRouter

from app.analysis.discovery_engine import run_discovery
from app.analysis.research_planner import generate_plan
from app.core.errors import ModelNotFoundError
from app.storage.repositories import dataset_repository, discovery_repository, plan_repository
from app.schemas.discovery import (
    DiscoveryConfig,
    DiscoveryResult,
)
from app.schemas.planning import ResearchPlan
from app.services.structure_detector import detect_structure

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.post("/run", response_model=DiscoveryResult)
async def run_discovery_endpoint(config: DiscoveryConfig) -> DiscoveryResult:
    record = dataset_repository.get(config.dataset_id)
    result = run_discovery(config, record)

    project_id = getattr(record, "project_id", None)
    discovery_repository.create(result, project_id=project_id)
    return result


@router.get("/{discovery_id}", response_model=DiscoveryResult)
async def get_discovery(discovery_id: str) -> DiscoveryResult:
    record = discovery_repository.get(discovery_id)
    return record.result


@router.get("/{discovery_id}/findings")
async def get_findings(discovery_id: str) -> list[dict]:
    record = discovery_repository.get(discovery_id)
    return [f.model_dump() for f in record.result.findings]


@router.get("/{discovery_id}/export/json")
async def export_discovery_json(discovery_id: str) -> dict:
    record = discovery_repository.get(discovery_id)
    result = record.result
    return {
        "discovery_id": result.discovery_id,
        "dataset_id": result.dataset_id,
        "dataset_filename": result.dataset_filename,
        "mode": result.mode,
        "config": result.config.model_dump(),
        "created_at": result.created_at.isoformat(),
        "eligibility_results": [e.model_dump() for e in result.eligibility_results],
        "candidate_outcomes": result.candidate_outcomes,
        "candidate_predictors": result.candidate_predictors,
        "specifications_generated": result.specifications_generated,
        "specifications_completed": result.specifications_completed,
        "specifications_failed": result.specifications_failed,
        "specification_results": [s.model_dump() for s in result.specification_results],
        "corrected_results": [c.model_dump() for c in result.corrected_results],
        "stability_assessments": [s.model_dump() for s in result.stability_assessments],
        "findings": [f.model_dump() for f in result.findings],
        "disclaimer": result.disclaimer,
    }


@router.post("/{discovery_id}/findings/{finding_id}/create-plan", response_model=ResearchPlan)
async def create_plan_from_finding(
    discovery_id: str,
    finding_id: str,
) -> ResearchPlan:
    disc_record = discovery_repository.get(discovery_id)
    result = disc_record.result

    finding = next(
        (f for f in result.findings if f.finding_id == finding_id),
        None,
    )
    if finding is None:
        raise ModelNotFoundError(f"No finding '{finding_id}' in discovery '{discovery_id}'.")

    ds_record = dataset_repository.get(result.dataset_id)
    df = ds_record.processed_dataframe if ds_record.processed_dataframe is not None else ds_record.dataframe
    structure = detect_structure(df)

    question = (
        f"Is {finding.primary_predictor} statistically associated with "
        f"{finding.outcome_variable} in the available dataset?"
    )

    plan = generate_plan(
        dataset_id=result.dataset_id,
        df=df,
        research_question=question,
        structure=structure,
        preferred_outcome=finding.outcome_variable,
        preferred_primary_iv=finding.primary_predictor,
    )

    project_id = getattr(disc_record, "project_id", None)
    plan_repository.create(plan, dataset_id=result.dataset_id, project_id=project_id)
    return plan
