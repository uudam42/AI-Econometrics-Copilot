"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import ComparisonRecord, comparison_repository as comparison_registry

__all__ = ["ComparisonRecord", "comparison_registry"]
