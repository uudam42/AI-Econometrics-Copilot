"""In-process registry for discovery results."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.errors import ModelNotFoundError
from app.schemas.discovery import DiscoveryResult


@dataclass
class DiscoveryRecord:
    discovery_id: str
    dataset_id: str
    result: DiscoveryResult
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DiscoveryRegistry:
    def __init__(self) -> None:
        self._records: dict[str, DiscoveryRecord] = {}
        self._lock = threading.Lock()

    def create(self, result: DiscoveryResult) -> DiscoveryRecord:
        record = DiscoveryRecord(
            discovery_id=result.discovery_id,
            dataset_id=result.dataset_id,
            result=result,
        )
        with self._lock:
            self._records[result.discovery_id] = record
        return record

    def get(self, discovery_id: str) -> DiscoveryRecord:
        with self._lock:
            record = self._records.get(discovery_id)
        if record is None:
            raise ModelNotFoundError(
                f"No discovery result found with id '{discovery_id}'."
            )
        return record

    def exists(self, discovery_id: str) -> bool:
        with self._lock:
            return discovery_id in self._records


discovery_registry = DiscoveryRegistry()
