"""Comparison execution and retrieval endpoints."""
from __future__ import annotations

import importlib

from fastapi import APIRouter

from app.analysis.model_comparison import run_comparison
from app.storage.repositories import comparison_repository, dataset_repository
from app.schemas.comparison import (
    ComparisonExportArtifact,
    ComparisonRequest,
    ComparisonResult,
)

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.post("/run", response_model=ComparisonResult)
async def run_comparison_endpoint(request: ComparisonRequest) -> ComparisonResult:
    """Run multiple models on the same dataset and variable selection."""
    record = dataset_repository.get(request.dataset_id)
    result = run_comparison(request, record)

    project_id = getattr(record, "project_id", None)

    comparison_repository.create(
        dataset_id=record.dataset_id,
        request=request,
        result=result,
        project_id=project_id,
    )
    return result


@router.get("/{comparison_id}", response_model=ComparisonResult)
async def get_comparison(comparison_id: str) -> ComparisonResult:
    record = comparison_repository.get(comparison_id)
    return record.result


@router.get("/{comparison_id}/export/json", response_model=ComparisonExportArtifact)
async def export_comparison_json(comparison_id: str) -> ComparisonExportArtifact:
    """Export a complete reproducible comparison artifact."""
    rec = comparison_repository.get(comparison_id)
    result = rec.result
    request = rec.request

    versions: dict[str, str] = {}
    for pkg in ("pandas", "numpy", "statsmodels", "scipy", "linearmodels"):
        try:
            mod = importlib.import_module(pkg)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"

    model_results = [
        {
            "model_type": m.model_type,
            "model_label": m.model_label,
            "status": m.status,
            "reason": m.reason,
            "formula": m.formula,
            "fit_metrics": m.fit_metrics.model_dump() if m.fit_metrics else None,
            "diagnostic_summary": m.diagnostic_summary.model_dump() if m.diagnostic_summary else None,
            "standard_error_type": m.standard_error_type,
            "entity_effects": m.entity_effects,
            "time_effects": m.time_effects,
            "warnings": m.warnings,
        }
        for m in result.models
    ]

    return ComparisonExportArtifact(
        comparison_id=result.comparison_id,
        dataset_id=result.dataset_id,
        dataset_filename=result.dataset_filename,
        created_at=result.created_at,
        variable_selection=result.variable_selection.model_dump(),
        transformations=[t.model_dump() for t in request.transformations],
        candidate_models=[str(m) for m in request.candidate_models],
        model_results=model_results,
        recommendation=result.recommendation.model_dump(),
        software_versions=versions,
        disclaimer=result.disclaimer,
    )
