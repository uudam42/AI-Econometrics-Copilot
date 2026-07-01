"""In-process registry holding uploaded datasets for the lifetime of the server.

MVP scope: no external database. Each dataset is kept as a pandas DataFrame in
memory and mirrored to disk (storage/uploads) for reproducibility of the
original upload.
"""
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from app.core.errors import DatasetNotFoundError


@dataclass
class DatasetRecord:
    dataset_id: str
    filename: str
    original_path: Path
    dataframe: pd.DataFrame
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed_dataframe: pd.DataFrame | None = None
    transformation_log: list[dict] = field(default_factory=list)


class DatasetRegistry:
    def __init__(self) -> None:
        self._records: dict[str, DatasetRecord] = {}
        self._lock = threading.Lock()

    def create(self, filename: str, original_path: Path, dataframe: pd.DataFrame) -> DatasetRecord:
        dataset_id = str(uuid.uuid4())
        record = DatasetRecord(
            dataset_id=dataset_id,
            filename=filename,
            original_path=original_path,
            dataframe=dataframe,
        )
        with self._lock:
            self._records[dataset_id] = record
        return record

    def get(self, dataset_id: str) -> DatasetRecord:
        with self._lock:
            record = self._records.get(dataset_id)
        if record is None:
            raise DatasetNotFoundError(f"No dataset found with id '{dataset_id}'.")
        return record

    def exists(self, dataset_id: str) -> bool:
        with self._lock:
            return dataset_id in self._records


registry = DatasetRegistry()
