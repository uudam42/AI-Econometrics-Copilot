"""In-process registry for generated research reports."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from app.core.errors import ModelNotFoundError
from app.schemas.reports import ReportArtifact


@dataclass
class ReportRecord:
    report_id: str
    created_at: datetime
    artifact: ReportArtifact


class ReportRegistry:
    def __init__(self) -> None:
        self._records: dict[str, ReportRecord] = {}
        self._lock = threading.Lock()

    def create(self, artifact: ReportArtifact) -> ReportRecord:
        record = ReportRecord(
            report_id=artifact.report_id,
            created_at=artifact.created_at,
            artifact=artifact,
        )
        with self._lock:
            self._records[artifact.report_id] = record
        return record

    def get(self, report_id: str) -> ReportRecord:
        with self._lock:
            record = self._records.get(report_id)
        if record is None:
            raise ModelNotFoundError(f"No report found with id '{report_id}'.")
        return record


report_registry = ReportRegistry()
