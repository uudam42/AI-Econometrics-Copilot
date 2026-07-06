"""SQLite-backed repository implementations.

Each repository persists Pydantic models as JSON in SQLite and maintains
an in-memory cache for fast access. DataFrames are loaded lazily from
the stored file on disk.
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select, update, delete

from app.core.config import settings
from app.core.errors import (
    DatasetNotFoundError,
    ModelNotFoundError,
    ProjectNotFoundError,
    ProjectDeletionError,
    StorageError,
)
from app.core.logging import get_logger
from app.storage.database import get_session
from app.storage.models import (
    AnalysisRow,
    ComparisonRow,
    DatasetRow,
    DiscoveryRow,
    PlanRow,
    ProjectRow,
    PublicationExportRow,
    ReportRow,
    TimelineEventRow,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Timeline helper
# ---------------------------------------------------------------------------

def _add_timeline_event(
    project_id: str | None,
    event_type: str,
    description: str,
    artifact_type: str | None = None,
    artifact_id: str | None = None,
) -> None:
    if project_id is None:
        return
    try:
        with get_session() as session:
            session.add(TimelineEventRow(
                project_id=project_id,
                event_type=event_type,
                artifact_type=artifact_type,
                artifact_id=artifact_id,
                description=description,
                created_at=datetime.now(timezone.utc),
            ))
            session.commit()
    except Exception:
        logger.debug("Failed to record timeline event", exc_info=True)


# ---------------------------------------------------------------------------
# Project Repository
# ---------------------------------------------------------------------------

class ProjectRepository:

    def create(
        self,
        *,
        title: str,
        description: str = "",
        research_question: str = "",
        tags: list[str] | None = None,
        research_context: str = "",
        notes: str = "",
        methodology_notes: str = "",
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        project_id = str(uuid.uuid4())
        row = ProjectRow(
            id=project_id,
            title=title,
            description=description,
            research_question=research_question,
            status="draft",
            tags=tags or [],
            research_context=research_context,
            notes=notes,
            methodology_notes=methodology_notes,
            created_at=now,
            updated_at=now,
        )
        with get_session() as session:
            session.add(row)
            session.commit()
            return self._row_to_dict(row)

    def get(self, project_id: str) -> dict[str, Any]:
        with get_session() as session:
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise ProjectNotFoundError(f"No project found with id '{project_id}'.")
            return self._row_to_dict(row)

    def list_all(self, include_archived: bool = False) -> list[dict[str, Any]]:
        with get_session() as session:
            stmt = select(ProjectRow).order_by(ProjectRow.updated_at.desc())
            if not include_archived:
                stmt = stmt.where(ProjectRow.status != "archived")
            rows = session.execute(stmt).scalars().all()
            return [self._row_to_dict(r) for r in rows]

    def update(self, project_id: str, **fields) -> dict[str, Any]:
        with get_session() as session:
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise ProjectNotFoundError(f"No project found with id '{project_id}'.")
            allowed = {
                "title", "description", "research_question", "status",
                "tags", "default_dataset_id", "research_context", "notes",
                "methodology_notes",
            }
            for k, v in fields.items():
                if k in allowed:
                    setattr(row, k, v)
            row.updated_at = datetime.now(timezone.utc)
            session.commit()
            return self._row_to_dict(row)

    def delete(self, project_id: str, force: bool = False) -> None:
        with get_session() as session:
            row = session.get(ProjectRow, project_id)
            if row is None:
                raise ProjectNotFoundError(f"No project found with id '{project_id}'.")

            if not force:
                artifact_count = sum(
                    session.execute(
                        select(table).where(table.project_id == project_id)
                    ).first() is not None
                    for table in [DatasetRow, AnalysisRow, ComparisonRow,
                                  PlanRow, ReportRow, DiscoveryRow]
                )
                if artifact_count > 0:
                    raise ProjectDeletionError(
                        f"Project '{project_id}' has linked artifacts. "
                        "Use force=true to delete everything.",
                    )

            for table in [TimelineEventRow, AnalysisRow, ComparisonRow,
                          PlanRow, ReportRow, DiscoveryRow]:
                session.execute(delete(table).where(table.project_id == project_id))
            session.execute(delete(DatasetRow).where(DatasetRow.project_id == project_id))
            session.delete(row)
            session.commit()

    def get_timeline(self, project_id: str) -> list[dict[str, Any]]:
        self.get(project_id)
        with get_session() as session:
            rows = session.execute(
                select(TimelineEventRow)
                .where(TimelineEventRow.project_id == project_id)
                .order_by(TimelineEventRow.created_at.desc())
            ).scalars().all()
            return [
                {
                    "event_type": r.event_type,
                    "artifact_type": r.artifact_type,
                    "artifact_id": r.artifact_id,
                    "description": r.description,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    def get_artifacts(self, project_id: str) -> dict[str, list[dict]]:
        self.get(project_id)
        result: dict[str, list[dict]] = {
            "datasets": [],
            "plans": [],
            "analyses": [],
            "comparisons": [],
            "reports": [],
            "discoveries": [],
        }
        with get_session() as session:
            for row in session.execute(
                select(DatasetRow).where(DatasetRow.project_id == project_id)
            ).scalars().all():
                result["datasets"].append({
                    "dataset_id": row.id, "filename": row.filename,
                    "n_rows": row.n_rows, "n_columns": row.n_columns,
                    "uploaded_at": row.uploaded_at.isoformat() if row.uploaded_at else None,
                })
            for row in session.execute(
                select(PlanRow).where(PlanRow.project_id == project_id)
            ).scalars().all():
                result["plans"].append({
                    "plan_id": row.id, "dataset_id": row.dataset_id,
                    "approved": bool(row.approved),
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            for row in session.execute(
                select(AnalysisRow).where(AnalysisRow.project_id == project_id)
            ).scalars().all():
                result["analyses"].append({
                    "analysis_id": row.id, "dataset_id": row.dataset_id,
                    "dataset_filename": row.dataset_filename,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            for row in session.execute(
                select(ComparisonRow).where(ComparisonRow.project_id == project_id)
            ).scalars().all():
                result["comparisons"].append({
                    "comparison_id": row.id, "dataset_id": row.dataset_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            for row in session.execute(
                select(ReportRow).where(ReportRow.project_id == project_id)
            ).scalars().all():
                result["reports"].append({
                    "report_id": row.id,
                    "source_type": row.source_type, "source_id": row.source_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
            for row in session.execute(
                select(DiscoveryRow).where(DiscoveryRow.project_id == project_id)
            ).scalars().all():
                result["discoveries"].append({
                    "discovery_id": row.id, "dataset_id": row.dataset_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                })
        return result

    @staticmethod
    def _row_to_dict(row: ProjectRow) -> dict[str, Any]:
        return {
            "project_id": row.id,
            "title": row.title,
            "description": row.description,
            "research_question": row.research_question,
            "status": row.status,
            "tags": row.tags or [],
            "default_dataset_id": row.default_dataset_id,
            "research_context": row.research_context or "",
            "notes": row.notes or "",
            "methodology_notes": row.methodology_notes or "",
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


# ---------------------------------------------------------------------------
# Dataset Repository
# ---------------------------------------------------------------------------

class DatasetRecord:
    """In-memory representation of a dataset, compatible with the old registry."""

    __slots__ = (
        "dataset_id", "filename", "original_path", "dataframe",
        "uploaded_at", "processed_dataframe", "transformation_log",
        "project_id", "checksum",
    )

    def __init__(
        self,
        dataset_id: str,
        filename: str,
        original_path: Path,
        dataframe: pd.DataFrame,
        uploaded_at: datetime | None = None,
        project_id: str | None = None,
        checksum: str | None = None,
    ):
        self.dataset_id = dataset_id
        self.filename = filename
        self.original_path = original_path
        self.dataframe = dataframe
        self.uploaded_at = uploaded_at or datetime.now(timezone.utc)
        self.processed_dataframe: pd.DataFrame | None = None
        self.transformation_log: list[dict] = []
        self.project_id = project_id
        self.checksum = checksum


class DatasetRepository:

    def __init__(self) -> None:
        self._cache: dict[str, DatasetRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        filename: str,
        original_path: Path,
        dataframe: pd.DataFrame,
        project_id: str | None = None,
    ) -> DatasetRecord:
        dataset_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        checksum = hashlib.sha256(original_path.read_bytes()).hexdigest()

        storage_rel = str(original_path.relative_to(settings.upload_dir)) if _is_subpath(original_path, settings.upload_dir) else original_path.name

        row = DatasetRow(
            id=dataset_id,
            project_id=project_id,
            filename=filename,
            storage_path=storage_rel,
            file_type=Path(filename).suffix.lower(),
            checksum=checksum,
            n_rows=dataframe.shape[0],
            n_columns=dataframe.shape[1],
            uploaded_at=now,
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = DatasetRecord(
            dataset_id=dataset_id,
            filename=filename,
            original_path=original_path,
            dataframe=dataframe,
            uploaded_at=now,
            project_id=project_id,
            checksum=checksum,
        )
        with self._lock:
            self._cache[dataset_id] = record

        _add_timeline_event(
            project_id, "dataset_uploaded",
            f"Dataset '{filename}' uploaded ({dataframe.shape[0]} rows × {dataframe.shape[1]} columns)",
            artifact_type="dataset", artifact_id=dataset_id,
        )
        return record

    def get(self, dataset_id: str) -> DatasetRecord:
        with self._lock:
            if dataset_id in self._cache:
                return self._cache[dataset_id]

        with get_session() as session:
            row = session.get(DatasetRow, dataset_id)
            if row is None:
                raise DatasetNotFoundError(f"No dataset found with id '{dataset_id}'.")

            stored_path = settings.upload_dir / row.storage_path
            if not stored_path.exists():
                raise StorageError(
                    f"Dataset file missing from storage: '{row.storage_path}'.",
                    details={"dataset_id": dataset_id},
                )

            suffix = Path(row.filename).suffix.lower()
            if suffix == ".csv":
                df = pd.read_csv(stored_path)
            else:
                df = pd.read_excel(stored_path)

            record = DatasetRecord(
                dataset_id=dataset_id,
                filename=row.filename,
                original_path=stored_path,
                dataframe=df,
                uploaded_at=row.uploaded_at,
                project_id=row.project_id,
                checksum=row.checksum,
            )
            with self._lock:
                self._cache[dataset_id] = record
            return record

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            if dataset_id in self._cache:
                return True
        with get_session() as session:
            return session.get(DatasetRow, dataset_id) is not None

    def list_by_project(self, project_id: str) -> list[dict[str, Any]]:
        with get_session() as session:
            rows = session.execute(
                select(DatasetRow).where(DatasetRow.project_id == project_id)
            ).scalars().all()
            return [
                {
                    "dataset_id": r.id,
                    "filename": r.filename,
                    "n_rows": r.n_rows,
                    "n_columns": r.n_columns,
                    "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
                    "checksum": r.checksum,
                }
                for r in rows
            ]

    def update_profile(self, dataset_id: str, profile_json: dict, structure_json: dict) -> None:
        with get_session() as session:
            session.execute(
                update(DatasetRow)
                .where(DatasetRow.id == dataset_id)
                .values(profile_json=profile_json, structure_json=structure_json)
            )
            session.commit()

    def set_project(self, dataset_id: str, project_id: str) -> None:
        with get_session() as session:
            session.execute(
                update(DatasetRow)
                .where(DatasetRow.id == dataset_id)
                .values(project_id=project_id)
            )
            session.commit()
        with self._lock:
            if dataset_id in self._cache:
                self._cache[dataset_id].project_id = project_id

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()


# ---------------------------------------------------------------------------
# Analysis Repository
# ---------------------------------------------------------------------------

class AnalysisRecord:
    __slots__ = (
        "analysis_id", "dataset_id", "dataset_filename", "created_at",
        "config", "result", "diagnostics", "transformation_log", "project_id",
    )

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class AnalysisRepository:
    def __init__(self) -> None:
        self._cache: dict[str, AnalysisRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        *,
        dataset_id: str,
        dataset_filename: str,
        config,
        result,
        diagnostics,
        transformation_log,
        project_id: str | None = None,
    ) -> AnalysisRecord:
        analysis_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        row = AnalysisRow(
            id=analysis_id,
            project_id=project_id,
            dataset_id=dataset_id,
            dataset_filename=dataset_filename,
            created_at=now,
            config_json=config.model_dump(mode="json"),
            result_json=result.model_dump(mode="json"),
            diagnostics_json=diagnostics.model_dump(mode="json"),
            transformation_log_json=[t.model_dump(mode="json") for t in transformation_log],
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = AnalysisRecord(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            dataset_filename=dataset_filename,
            created_at=now,
            config=config,
            result=result,
            diagnostics=diagnostics,
            transformation_log=transformation_log,
            project_id=project_id,
        )
        with self._lock:
            self._cache[analysis_id] = record

        _add_timeline_event(
            project_id, "analysis_executed",
            f"Analysis executed on '{dataset_filename}'",
            artifact_type="analysis", artifact_id=analysis_id,
        )
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        with self._lock:
            if analysis_id in self._cache:
                return self._cache[analysis_id]

        with get_session() as session:
            row = session.get(AnalysisRow, analysis_id)
            if row is None:
                raise ModelNotFoundError(f"No analysis found with id '{analysis_id}'.")

            from app.schemas.modeling import (
                AnalysisConfigurationRequest,
                AnalysisResult,
                ModelDiagnosticsResponse,
                TransformationLogEntry,
            )

            record = AnalysisRecord(
                analysis_id=analysis_id,
                dataset_id=row.dataset_id,
                dataset_filename=row.dataset_filename,
                created_at=row.created_at,
                config=AnalysisConfigurationRequest(**row.config_json),
                result=AnalysisResult(**row.result_json),
                diagnostics=ModelDiagnosticsResponse(**row.diagnostics_json),
                transformation_log=[TransformationLogEntry(**t) for t in (row.transformation_log_json or [])],
                project_id=row.project_id,
            )
            with self._lock:
                self._cache[analysis_id] = record
            return record

    def exists(self, analysis_id: str) -> bool:
        with self._lock:
            if analysis_id in self._cache:
                return True
        with get_session() as session:
            return session.get(AnalysisRow, analysis_id) is not None

    def update_result(self, analysis_id: str, result, diagnostics) -> None:
        with get_session() as session:
            session.execute(
                update(AnalysisRow)
                .where(AnalysisRow.id == analysis_id)
                .values(
                    result_json=result.model_dump(mode="json"),
                    diagnostics_json=diagnostics.model_dump(mode="json"),
                )
            )
            session.commit()
        with self._lock:
            if analysis_id in self._cache:
                self._cache[analysis_id].result = result
                self._cache[analysis_id].diagnostics = diagnostics


# ---------------------------------------------------------------------------
# Comparison Repository
# ---------------------------------------------------------------------------

class ComparisonRecord:
    __slots__ = ("comparison_id", "dataset_id", "created_at", "request", "result", "project_id")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ComparisonRepository:
    def __init__(self) -> None:
        self._cache: dict[str, ComparisonRecord] = {}
        self._lock = threading.Lock()

    def create(self, *, dataset_id: str, request, result, project_id: str | None = None) -> ComparisonRecord:
        row = ComparisonRow(
            id=result.comparison_id,
            project_id=project_id,
            dataset_id=dataset_id,
            created_at=result.created_at,
            request_json=request.model_dump(mode="json"),
            result_json=result.model_dump(mode="json"),
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = ComparisonRecord(
            comparison_id=result.comparison_id,
            dataset_id=dataset_id,
            created_at=result.created_at,
            request=request,
            result=result,
            project_id=project_id,
        )
        with self._lock:
            self._cache[result.comparison_id] = record

        _add_timeline_event(
            project_id, "comparison_completed",
            f"Model comparison completed ({len(result.models)} models)",
            artifact_type="comparison", artifact_id=result.comparison_id,
        )
        return record

    def get(self, comparison_id: str) -> ComparisonRecord:
        with self._lock:
            if comparison_id in self._cache:
                return self._cache[comparison_id]

        with get_session() as session:
            row = session.get(ComparisonRow, comparison_id)
            if row is None:
                raise ModelNotFoundError(f"No comparison found with id '{comparison_id}'.")

            from app.schemas.comparison import ComparisonRequest, ComparisonResult
            record = ComparisonRecord(
                comparison_id=comparison_id,
                dataset_id=row.dataset_id,
                created_at=row.created_at,
                request=ComparisonRequest(**row.request_json),
                result=ComparisonResult(**row.result_json),
                project_id=row.project_id,
            )
            with self._lock:
                self._cache[comparison_id] = record
            return record


# ---------------------------------------------------------------------------
# Plan Repository
# ---------------------------------------------------------------------------

class PlanRecord:
    __slots__ = ("plan_id", "dataset_id", "plan", "created_at", "approved", "project_id")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class PlanRepository:
    def __init__(self) -> None:
        self._cache: dict[str, PlanRecord] = {}
        self._lock = threading.Lock()

    def create(self, plan, dataset_id: str, project_id: str | None = None) -> PlanRecord:
        now = datetime.now(timezone.utc)
        row = PlanRow(
            id=plan.plan_id,
            project_id=project_id,
            dataset_id=dataset_id,
            created_at=now,
            plan_json=plan.model_dump(mode="json"),
            approved=0,
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = PlanRecord(
            plan_id=plan.plan_id,
            dataset_id=dataset_id,
            plan=plan,
            created_at=now,
            approved=False,
            project_id=project_id,
        )
        with self._lock:
            self._cache[plan.plan_id] = record

        _add_timeline_event(
            project_id, "plan_created",
            f"Research plan created for dataset '{dataset_id}'",
            artifact_type="plan", artifact_id=plan.plan_id,
        )
        return record

    def get(self, plan_id: str) -> PlanRecord:
        with self._lock:
            if plan_id in self._cache:
                return self._cache[plan_id]

        with get_session() as session:
            row = session.get(PlanRow, plan_id)
            if row is None:
                raise ModelNotFoundError(f"No research plan found with id '{plan_id}'.")

            from app.schemas.planning import ResearchPlan
            record = PlanRecord(
                plan_id=plan_id,
                dataset_id=row.dataset_id,
                plan=ResearchPlan(**row.plan_json),
                created_at=row.created_at,
                approved=bool(row.approved),
                project_id=row.project_id,
            )
            with self._lock:
                self._cache[plan_id] = record
            return record

    def mark_approved(self, plan_id: str) -> PlanRecord:
        record = self.get(plan_id)
        record.approved = True
        with get_session() as session:
            session.execute(
                update(PlanRow).where(PlanRow.id == plan_id).values(approved=1)
            )
            session.commit()
        return record

    def exists(self, plan_id: str) -> bool:
        with self._lock:
            if plan_id in self._cache:
                return True
        with get_session() as session:
            return session.get(PlanRow, plan_id) is not None


# ---------------------------------------------------------------------------
# Report Repository
# ---------------------------------------------------------------------------

class ReportRecord:
    __slots__ = ("report_id", "created_at", "artifact", "project_id")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ReportRepository:
    def __init__(self) -> None:
        self._cache: dict[str, ReportRecord] = {}
        self._lock = threading.Lock()

    def create(self, artifact, project_id: str | None = None, source_type: str | None = None, source_id: str | None = None) -> ReportRecord:
        row = ReportRow(
            id=artifact.report_id,
            project_id=project_id,
            source_type=source_type,
            source_id=source_id,
            created_at=artifact.created_at,
            artifact_json=artifact.model_dump(mode="json"),
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = ReportRecord(
            report_id=artifact.report_id,
            created_at=artifact.created_at,
            artifact=artifact,
            project_id=project_id,
        )
        with self._lock:
            self._cache[artifact.report_id] = record

        _add_timeline_event(
            project_id, "report_generated",
            f"Research report generated",
            artifact_type="report", artifact_id=artifact.report_id,
        )
        return record

    def get(self, report_id: str) -> ReportRecord:
        with self._lock:
            if report_id in self._cache:
                return self._cache[report_id]

        with get_session() as session:
            row = session.get(ReportRow, report_id)
            if row is None:
                raise ModelNotFoundError(f"No report found with id '{report_id}'.")

            from app.schemas.reports import ReportArtifact
            record = ReportRecord(
                report_id=report_id,
                created_at=row.created_at,
                artifact=ReportArtifact(**row.artifact_json),
                project_id=row.project_id,
            )
            with self._lock:
                self._cache[report_id] = record
            return record


# ---------------------------------------------------------------------------
# Discovery Repository
# ---------------------------------------------------------------------------

class DiscoveryRecord:
    __slots__ = ("discovery_id", "dataset_id", "result", "created_at", "project_id")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class DiscoveryRepository:
    def __init__(self) -> None:
        self._cache: dict[str, DiscoveryRecord] = {}
        self._lock = threading.Lock()

    def create(self, result, project_id: str | None = None) -> DiscoveryRecord:
        row = DiscoveryRow(
            id=result.discovery_id,
            project_id=project_id,
            dataset_id=result.dataset_id,
            created_at=result.created_at,
            result_json=result.model_dump(mode="json"),
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = DiscoveryRecord(
            discovery_id=result.discovery_id,
            dataset_id=result.dataset_id,
            result=result,
            created_at=result.created_at,
            project_id=project_id,
        )
        with self._lock:
            self._cache[result.discovery_id] = record

        _add_timeline_event(
            project_id, "discovery_completed",
            f"Exploratory discovery completed ({len(result.findings)} findings)",
            artifact_type="discovery", artifact_id=result.discovery_id,
        )
        return record

    def get(self, discovery_id: str) -> DiscoveryRecord:
        with self._lock:
            if discovery_id in self._cache:
                return self._cache[discovery_id]

        with get_session() as session:
            row = session.get(DiscoveryRow, discovery_id)
            if row is None:
                raise ModelNotFoundError(f"No discovery result found with id '{discovery_id}'.")

            from app.schemas.discovery import DiscoveryResult
            record = DiscoveryRecord(
                discovery_id=discovery_id,
                dataset_id=row.dataset_id,
                result=DiscoveryResult(**row.result_json),
                created_at=row.created_at,
                project_id=row.project_id,
            )
            with self._lock:
                self._cache[discovery_id] = record
            return record

    def exists(self, discovery_id: str) -> bool:
        with self._lock:
            if discovery_id in self._cache:
                return True
        with get_session() as session:
            return session.get(DiscoveryRow, discovery_id) is not None


# ---------------------------------------------------------------------------
# Publication Export Repository
# ---------------------------------------------------------------------------

class PublicationExportRecord:
    __slots__ = ("export_id", "project_id", "source_type", "source_id",
                 "title", "created_at", "config", "result")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class PublicationExportRepository:
    def __init__(self) -> None:
        self._cache: dict[str, PublicationExportRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        result,
        config,
        project_id: str | None = None,
    ) -> PublicationExportRecord:
        row = PublicationExportRow(
            id=result.export_id,
            project_id=project_id,
            source_type=result.source_type,
            source_id=result.source_id,
            title=result.title,
            created_at=result.created_at,
            config_json=config.model_dump(mode="json"),
            result_json=result.model_dump(mode="json"),
        )
        with get_session() as session:
            session.add(row)
            session.commit()

        record = PublicationExportRecord(
            export_id=result.export_id,
            project_id=project_id,
            source_type=result.source_type,
            source_id=result.source_id,
            title=result.title,
            created_at=result.created_at,
            config=config,
            result=result,
        )
        with self._lock:
            self._cache[result.export_id] = record

        _add_timeline_event(
            project_id, "publication_export_created",
            f"Publication export created: {result.title}",
            artifact_type="publication_export", artifact_id=result.export_id,
        )
        return record

    def get(self, export_id: str) -> PublicationExportRecord:
        with self._lock:
            if export_id in self._cache:
                return self._cache[export_id]

        with get_session() as session:
            row = session.get(PublicationExportRow, export_id)
            if row is None:
                raise ModelNotFoundError(f"No publication export found with id '{export_id}'.")

            from app.schemas.publication_export import (
                PublicationExportConfig,
                PublicationExportResult,
            )
            record = PublicationExportRecord(
                export_id=export_id,
                project_id=row.project_id,
                source_type=row.source_type,
                source_id=row.source_id,
                title=row.title,
                created_at=row.created_at,
                config=PublicationExportConfig(**row.config_json),
                result=PublicationExportResult(**row.result_json),
            )
            with self._lock:
                self._cache[export_id] = record
            return record

    def list_by_project(self, project_id: str) -> list[PublicationExportRecord]:
        records: list[PublicationExportRecord] = []
        with get_session() as session:
            rows = session.execute(
                select(PublicationExportRow)
                .where(PublicationExportRow.project_id == project_id)
                .order_by(PublicationExportRow.created_at.desc())
            ).scalars().all()
            for row in rows:
                with self._lock:
                    if row.id in self._cache:
                        records.append(self._cache[row.id])
                        continue
                from app.schemas.publication_export import (
                    PublicationExportConfig,
                    PublicationExportResult,
                )
                rec = PublicationExportRecord(
                    export_id=row.id,
                    project_id=row.project_id,
                    source_type=row.source_type,
                    source_id=row.source_id,
                    title=row.title,
                    created_at=row.created_at,
                    config=PublicationExportConfig(**row.config_json),
                    result=PublicationExportResult(**row.result_json),
                )
                with self._lock:
                    self._cache[row.id] = rec
                records.append(rec)
        return records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_subpath(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Module-level singletons (replace old registry singletons)
# ---------------------------------------------------------------------------

project_repository = ProjectRepository()
dataset_repository = DatasetRepository()
analysis_repository = AnalysisRepository()
comparison_repository = ComparisonRepository()
plan_repository = PlanRepository()
report_repository = ReportRepository()
discovery_repository = DiscoveryRepository()
publication_export_repository = PublicationExportRepository()
