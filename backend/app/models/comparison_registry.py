"""In-process registry for completed comparison artifacts."""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.errors import ModelNotFoundError
from app.schemas.comparison import ComparisonRequest, ComparisonResult


@dataclass
class ComparisonRecord:
    comparison_id: str
    dataset_id: str
    created_at: datetime
    request: ComparisonRequest
    result: ComparisonResult


class ComparisonRegistry:
    def __init__(self) -> None:
        self._records: dict[str, ComparisonRecord] = {}
        self._lock = threading.Lock()

    def create(
        self,
        *,
        dataset_id: str,
        request: ComparisonRequest,
        result: ComparisonResult,
    ) -> ComparisonRecord:
        record = ComparisonRecord(
            comparison_id=result.comparison_id,
            dataset_id=dataset_id,
            created_at=result.created_at,
            request=request,
            result=result,
        )
        with self._lock:
            self._records[result.comparison_id] = record
        return record

    def get(self, comparison_id: str) -> ComparisonRecord:
        with self._lock:
            record = self._records.get(comparison_id)
        if record is None:
            raise ModelNotFoundError(f"No comparison found with id '{comparison_id}'.")
        return record


comparison_registry = ComparisonRegistry()
