"""Publication-ready export generation and retrieval endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, PlainTextResponse

from app.reports.publication_export_service import (
    generate_publication_export,
    get_export_file,
)
from app.schemas.publication_export import (
    PublicationExportConfig,
    PublicationExportListItem,
    PublicationExportResult,
)
from app.storage.repositories import publication_export_repository

router = APIRouter(prefix="/publication-exports", tags=["publication-exports"])


@router.post("/generate", response_model=PublicationExportResult)
async def create_publication_export(
    config: PublicationExportConfig,
) -> PublicationExportResult:
    result = generate_publication_export(config)
    publication_export_repository.create(
        result, config, project_id=config.project_id,
    )
    return result


@router.get("/{export_id}", response_model=PublicationExportResult)
async def get_publication_export(export_id: str) -> PublicationExportResult:
    rec = publication_export_repository.get(export_id)
    return rec.result


@router.get("/{export_id}/download/{fmt}")
async def download_export_file(export_id: str, fmt: str) -> FileResponse:
    path = get_export_file(export_id, fmt)  # type: ignore[arg-type]
    media_types = {
        "markdown": "text/markdown",
        "html": "text/html",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "latex": "text/x-latex",
        "json": "application/json",
    }
    filename_ext = {
        "markdown": "md",
        "html": "html",
        "docx": "docx",
        "latex": "tex",
        "json": "json",
    }
    return FileResponse(
        path=str(path),
        media_type=media_types.get(fmt, "application/octet-stream"),
        filename=f"export_{export_id}.{filename_ext.get(fmt, fmt)}",
    )


@router.get("/{export_id}/export/json", response_model=PublicationExportResult)
async def export_publication_json(export_id: str) -> PublicationExportResult:
    rec = publication_export_repository.get(export_id)
    return rec.result


# Project-scoped listing
@router.get(
    "/by-project/{project_id}",
    response_model=list[PublicationExportListItem],
)
async def list_project_exports(
    project_id: str,
) -> list[PublicationExportListItem]:
    records = publication_export_repository.list_by_project(project_id)
    return [
        PublicationExportListItem(
            export_id=r.export_id,
            title=r.title,
            source_type=r.source_type,
            source_id=r.source_id,
            created_at=r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
            available_formats=r.result.available_formats,
        )
        for r in records
    ]
