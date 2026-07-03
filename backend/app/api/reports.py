"""Research report generation and retrieval endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.core.errors import ValidationAppError
from app.storage.repositories import (
    analysis_repository,
    comparison_repository,
    report_repository,
)
from app.reports.report_generator import generate_from_analysis, generate_from_comparison
from app.schemas.reports import ReportArtifact, ReportGenerationRequest

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportArtifact)
async def generate_report(req: ReportGenerationRequest) -> ReportArtifact:
    """Generate a research report from an existing analysis or comparison artifact."""
    project_id: str | None = None

    if req.source_type == "analysis":
        ar = analysis_repository.get(req.source_id)
        project_id = getattr(ar, "project_id", None)
        artifact = generate_from_analysis(req, ar.result, ar.diagnostics)
    elif req.source_type == "comparison":
        cr = comparison_repository.get(req.source_id)
        project_id = getattr(cr, "project_id", None)
        artifact = generate_from_comparison(req, cr.result)
    else:
        raise ValidationAppError(f"Unknown source_type: '{req.source_type}'.")

    report_repository.create(
        artifact,
        project_id=project_id,
        source_type=req.source_type,
        source_id=req.source_id,
    )
    return artifact


@router.get("/{report_id}", response_model=ReportArtifact)
async def get_report(report_id: str) -> ReportArtifact:
    rec = report_repository.get(report_id)
    return rec.artifact


@router.get("/{report_id}/markdown")
async def get_report_markdown(report_id: str) -> PlainTextResponse:
    rec = report_repository.get(report_id)
    return PlainTextResponse(
        content=rec.artifact.markdown_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="report_{report_id}.md"'},
    )


@router.get("/{report_id}/html")
async def get_report_html(report_id: str) -> HTMLResponse:
    rec = report_repository.get(report_id)
    return HTMLResponse(content=rec.artifact.html_content)


@router.get("/{report_id}/export/json", response_model=ReportArtifact)
async def export_report_json(report_id: str) -> ReportArtifact:
    rec = report_repository.get(report_id)
    return rec.artifact
