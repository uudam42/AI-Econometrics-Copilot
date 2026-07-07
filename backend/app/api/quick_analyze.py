"""Quick Analyze API — simplified 4-stage workflow for non-technical users.

Endpoints follow the session state machine:
  upload → plan → confirm/run → complete

Sessions persist in SQLite and link back to standard project/dataset/analysis
objects so the user can open the full Research Workspace at any point.
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.analysis.quick_analyze_service import (
    confirm_and_run,
    create_session_with_upload,
    get_session_detail,
    plan_session,
)
from app.core.config import settings
from app.schemas.quick_analyze import (
    ConfirmationRequest,
    QuickAnalyzePlanResponse,
    QuickAnalyzeRunResponse,
    QuickAnalyzeSession,
    QuickAnalyzeSessionDetail,
    QuickAnalyzeUploadResponse,
)
from app.storage.repositories import dataset_repository

router = APIRouter(prefix="/quick-analyze", tags=["quick-analyze"])


@router.post("/upload", response_model=QuickAnalyzeUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    research_question: str | None = Form(default=None),
    analysis_intent: str = Form(default="association"),
) -> QuickAnalyzeUploadResponse:
    """Stage 1 — upload a file and create a session.

    Accepts Excel (.xlsx, .xls) or CSV. Returns session_id needed for
    all subsequent calls.
    """
    content = await file.read()
    session = create_session_with_upload(
        filename=file.filename or "upload",
        content=content,
        research_question=research_question or None,
        analysis_intent=analysis_intent,
    )
    record = dataset_repository.get(session.dataset_id)  # type: ignore[arg-type]
    df = record.dataframe
    return QuickAnalyzeUploadResponse(
        session_id=session.session_id,
        dataset_id=session.dataset_id or "",
        project_id=session.project_id or "",
        filename=record.filename,
        n_rows=df.shape[0],
        n_columns=df.shape[1],
        stage=session.stage,
    )


@router.post("/{session_id}/plan", response_model=QuickAnalyzePlanResponse)
async def plan(session_id: str) -> QuickAnalyzePlanResponse:
    """Stage 2 — profile data, detect structure, generate recommendation.

    The response includes a RecommendationCard that the frontend shows for
    user confirmation. If `needs_user_input` is set, the user must select
    the missing variable before proceeding.
    """
    session = plan_session(session_id)
    if session.recommendation is None:
        raise HTTPException(status_code=500, detail="Planning produced no recommendation.")
    return QuickAnalyzePlanResponse(
        session_id=session.session_id,
        stage=session.stage,
        recommendation=session.recommendation,
        progress_message=session.progress_message,
    )


@router.post("/{session_id}/confirm", response_model=QuickAnalyzeRunResponse)
async def confirm(
    session_id: str,
    body: ConfirmationRequest,
) -> QuickAnalyzeRunResponse:
    """Stage 3 — user confirms variables and model; runs analysis synchronously.

    Returns a BeginnerSummary alongside the full analysis_id so the frontend
    can link to the Research Workspace for deeper investigation.
    """
    session = confirm_and_run(session_id, body)
    if session.summary is None or session.analysis_id is None:
        raise HTTPException(status_code=500, detail="Analysis completed but summary is missing.")
    return QuickAnalyzeRunResponse(
        session_id=session.session_id,
        stage=session.stage,
        analysis_id=session.analysis_id,
        summary=session.summary,
        progress_message=session.progress_message,
    )


@router.get("/{session_id}", response_model=QuickAnalyzeSessionDetail)
async def get_session(session_id: str) -> QuickAnalyzeSessionDetail:
    """Return full session state — useful for polling or deep-linking."""
    session = get_session_detail(session_id)
    workspace_url: str | None = None
    if session.analysis_id:
        workspace_url = f"/analyses/{session.analysis_id}"
    return QuickAnalyzeSessionDetail(session=session, workspace_url=workspace_url)


@router.get("/{session_id}/summary", response_model=QuickAnalyzeSession)
async def get_summary(session_id: str) -> QuickAnalyzeSession:
    """Convenience endpoint — returns session with embedded BeginnerSummary."""
    return get_session_detail(session_id)
