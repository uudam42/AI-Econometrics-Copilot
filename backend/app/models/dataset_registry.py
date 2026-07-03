"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import DatasetRecord, dataset_repository as registry

__all__ = ["DatasetRecord", "registry"]
