"""Research planning endpoints: generate, retrieve, approve, export."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.analysis.research_planner import generate_plan
from app.models.dataset_registry import registry as dataset_registry
from app.models.plan_registry import plan_registry
from app.schemas.planning import (
    PlanApprovalRequest,
    PlanApprovalResult,
    PlanGenerationRequest,
    ResearchPlan,
)
from app.services.structure_detector import detect_structure

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/generate", response_model=ResearchPlan)
async def generate_plan_endpoint(req: PlanGenerationRequest) -> ResearchPlan:
    record = dataset_registry.get(req.dataset_id)
    df = record.processed_dataframe if record.processed_dataframe is not None else record.dataframe
    structure = detect_structure(df)

    plan = generate_plan(
        dataset_id=req.dataset_id,
        df=df,
        research_question=req.research_question,
        structure=structure,
        context=req.context,
        preferred_outcome=req.preferred_outcome,
        preferred_primary_iv=req.preferred_primary_independent_variable,
    )

    plan_registry.create(plan, dataset_id=req.dataset_id)
    return plan


@router.get("/{plan_id}", response_model=ResearchPlan)
async def get_plan(plan_id: str) -> ResearchPlan:
    record = plan_registry.get(plan_id)
    return record.plan


@router.post("/{plan_id}/approve", response_model=PlanApprovalResult)
async def approve_plan(plan_id: str, approval: PlanApprovalRequest) -> PlanApprovalResult:
    pr = plan_registry.get(plan_id)
    plan_registry.mark_approved(plan_id)

    variable_selection: dict[str, Any] = {
        "dependent_variable": approval.dependent_variable,
        "primary_independent_variable": approval.primary_independent_variable,
        "control_variables": approval.control_variables,
        "entity_column": approval.entity_column,
        "time_column": approval.time_column,
    }

    redirect_path = f"/datasets/{pr.dataset_id}/model"

    return PlanApprovalResult(
        plan_id=plan_id,
        approved=True,
        variable_selection=variable_selection,
        transformations=approval.approved_transformations,
        candidate_models=approval.selected_candidate_models,
        redirect_path=redirect_path,
    )


@router.get("/{plan_id}/export/json")
async def export_plan_json(plan_id: str) -> dict:
    record = plan_registry.get(plan_id)
    plan = record.plan
    return {
        "plan_id": plan.plan_id,
        "dataset_id": plan.dataset_id,
        "research_question": plan.research_question,
        "normalized_question": plan.normalized_question,
        "user_context": plan.user_context,
        "inferred_analysis_intent": plan.inferred_analysis_intent,
        "candidate_variables": [cv.model_dump() for cv in plan.candidate_variables],
        "suggested_transformations": [st.model_dump() for st in plan.suggested_transformations],
        "suggested_models": [sm.model_dump() for sm in plan.suggested_models],
        "detected_structure_summary": plan.detected_structure_summary,
        "ambiguities": plan.ambiguities,
        "causal_warning": plan.causal_warning,
        "approved": record.approved,
        "created_at": record.created_at.isoformat(),
    }
