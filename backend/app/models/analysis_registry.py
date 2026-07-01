"""In-process registry for completed analysis artifacts.

Stores analysis results, diagnostics, and reproducibility information
for the lifetime of the server process.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.errors import ModelNotFoundError
from app.schemas.modeling import (
    AnalysisConfigurationRequest,
    AnalysisResult,
    ModelDiagnosticsResponse,
    TransformationLogEntry,
)


@dataclass
class AnalysisRecord:
    analysis_id: str
    dataset_id: str
    dataset_filename: str
    created_at: datetime
    config: AnalysisConfigurationRequest
    result: AnalysisResult
    diagnostics: ModelDiagnosticsResponse
    transformation_log: list[TransformationLogEntry] = field(default_factory=list)


class AnalysisRegistry:
    def __init__(self) -> None:
        self._records: dict[str, AnalysisRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        *,
        dataset_id: str,
        dataset_filename: str,
        config: AnalysisConfigurationRequest,
        result: AnalysisResult,
        diagnostics: ModelDiagnosticsResponse,
        transformation_log: list[TransformationLogEntry],
    ) -> AnalysisRecord:
        analysis_id = str(uuid.uuid4())
        record = AnalysisRecord(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            dataset_filename=dataset_filename,
            created_at=datetime.now(timezone.utc),
            config=config,
            result=result,
            diagnostics=diagnostics,
            transformation_log=transformation_log,
        )
        with self._lock:
            self._records[analysis_id] = record
        return record

    def get(self, analysis_id: str) -> AnalysisRecord:
        with self._lock:
            record = self._records.get(analysis_id)
        if record is None:
            raise ModelNotFoundError(
                f"No analysis found with id '{analysis_id}'."
            )
        return record

    def exists(self, analysis_id: str) -> bool:
        with self._lock:
            return analysis_id in self._records


analysis_registry = AnalysisRegistry()
