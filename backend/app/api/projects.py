"""Project workspace endpoints: CRUD, timeline, artifacts, export."""
from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.schemas.project import (
    ProjectArtifacts,
    ProjectCreateRequest,
    ProjectExport,
    ProjectResponse,
    ProjectUpdateRequest,
    TimelineEvent,
)
from app.services.dataset_service import ingest_upload
from app.storage.repositories import (
    analysis_repository,
    comparison_repository,
    dataset_repository,
    discovery_repository,
    plan_repository,
    project_repository,
    report_repository,
)

router = APIRouter(prefix="/projects", tags=["projects"])


def _to_response(d: dict) -> ProjectResponse:
    return ProjectResponse(**d)


@router.post("", response_model=ProjectResponse)
async def create_project(req: ProjectCreateRequest) -> ProjectResponse:
    data = project_repository.create(
        title=req.title,
        description=req.description,
        research_question=req.research_question,
        tags=req.tags,
        research_context=req.research_context,
        notes=req.notes,
        methodology_notes=req.methodology_notes,
    )
    return _to_response(data)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    include_archived: bool = Query(False),
) -> list[ProjectResponse]:
    return [_to_response(d) for d in project_repository.list_all(include_archived)]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str) -> ProjectResponse:
    return _to_response(project_repository.get(project_id))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, req: ProjectUpdateRequest) -> ProjectResponse:
    fields = req.model_dump(exclude_none=True)
    return _to_response(project_repository.update(project_id, **fields))


@router.delete("/{project_id}")
async def delete_project(project_id: str, force: bool = Query(False)) -> dict:
    project_repository.delete(project_id, force=force)
    return {"deleted": True, "project_id": project_id}


@router.get("/{project_id}/timeline", response_model=list[TimelineEvent])
async def get_timeline(project_id: str) -> list[TimelineEvent]:
    events = project_repository.get_timeline(project_id)
    return [TimelineEvent(**e) for e in events]


@router.get("/{project_id}/artifacts", response_model=ProjectArtifacts)
async def get_artifacts(project_id: str) -> ProjectArtifacts:
    data = project_repository.get_artifacts(project_id)
    return ProjectArtifacts(**data)


@router.post("/{project_id}/datasets/upload")
async def upload_dataset_to_project(
    project_id: str,
    file: UploadFile = File(...),
) -> dict:
    project_repository.get(project_id)
    content = await file.read()
    record = ingest_upload(
        filename=file.filename or "",
        content=content,
        project_id=project_id,
    )

    from app.services.column_typing import infer_all_column_types
    from app.services.dataset_service import build_preview

    df = record.dataframe
    return {
        "dataset_id": record.dataset_id,
        "filename": record.filename,
        "n_rows": df.shape[0],
        "n_columns": df.shape[1],
        "column_types": [c.model_dump() for c in infer_all_column_types(df)],
        "preview_rows": build_preview(df),
        "uploaded_at": record.uploaded_at.isoformat(),
    }


@router.get("/{project_id}/export/json", response_model=ProjectExport)
async def export_project_json(project_id: str) -> ProjectExport:
    proj = project_repository.get(project_id)
    artifacts = project_repository.get_artifacts(project_id)
    timeline = project_repository.get_timeline(project_id)
    return ProjectExport(
        project=ProjectResponse(**proj),
        artifacts=ProjectArtifacts(**artifacts),
        timeline=[TimelineEvent(**e) for e in timeline],
    )


@router.get("/{project_id}/export/bundle")
async def export_project_bundle(
    project_id: str,
    include_raw_data: bool = Query(False),
) -> StreamingResponse:
    proj = project_repository.get(project_id)
    artifacts_data = project_repository.get_artifacts(project_id)
    timeline_data = project_repository.get_timeline(project_id)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("project.json", json.dumps(proj, indent=2, default=str))

        zf.writestr("artifacts/datasets.json", json.dumps(artifacts_data["datasets"], indent=2, default=str))

        for ds_info in artifacts_data["datasets"]:
            ds_id = ds_info["dataset_id"]
            if include_raw_data:
                try:
                    ds_record = dataset_repository.get(ds_id)
                    path = ds_record.original_path
                    if path.exists():
                        zf.write(str(path), f"raw_data/{ds_record.filename}")
                except Exception:
                    pass

        for analysis_info in artifacts_data["analyses"]:
            aid = analysis_info["analysis_id"]
            try:
                ar = analysis_repository.get(aid)
                zf.writestr(
                    f"artifacts/analyses/{aid}.json",
                    json.dumps(ar.result.model_dump(mode="json"), indent=2, default=str),
                )
            except Exception:
                pass

        for comp_info in artifacts_data["comparisons"]:
            cid = comp_info["comparison_id"]
            try:
                cr = comparison_repository.get(cid)
                zf.writestr(
                    f"artifacts/comparisons/{cid}.json",
                    json.dumps(cr.result.model_dump(mode="json"), indent=2, default=str),
                )
            except Exception:
                pass

        for plan_info in artifacts_data["plans"]:
            pid = plan_info["plan_id"]
            try:
                pr = plan_repository.get(pid)
                zf.writestr(
                    f"artifacts/plans/{pid}.json",
                    json.dumps(pr.plan.model_dump(mode="json"), indent=2, default=str),
                )
            except Exception:
                pass

        for report_info in artifacts_data["reports"]:
            rid = report_info["report_id"]
            try:
                rr = report_repository.get(rid)
                zf.writestr(
                    f"artifacts/reports/{rid}.json",
                    json.dumps(rr.artifact.model_dump(mode="json"), indent=2, default=str),
                )
            except Exception:
                pass

        for disc_info in artifacts_data["discoveries"]:
            did = disc_info["discovery_id"]
            try:
                dr = discovery_repository.get(did)
                zf.writestr(
                    f"artifacts/discoveries/{did}.json",
                    json.dumps(dr.result.model_dump(mode="json"), indent=2, default=str),
                )
            except Exception:
                pass

        zf.writestr("timeline.json", json.dumps(timeline_data, indent=2, default=str))

        disclaimer = (
            "This bundle preserves the project configuration, transformation history, "
            "model outputs, diagnostics, comparisons, reports, and exploratory discovery "
            "results. It does not by itself establish causal claims."
        )
        readme = f"# Project: {proj['title']}\n\n{disclaimer}\n\n"
        readme += "## Contents\n\n"
        readme += "- `project.json` — project metadata\n"
        readme += "- `artifacts/` — analysis, comparison, plan, report, and discovery artifacts\n"
        readme += "- `timeline.json` — chronological research activity\n"
        if include_raw_data:
            readme += "- `raw_data/` — original uploaded dataset files\n"
        zf.writestr("README.md", readme)

    buf.seek(0)
    safe_title = proj["title"].replace(" ", "_")[:50]
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="project_{safe_title}.zip"',
        },
    )
