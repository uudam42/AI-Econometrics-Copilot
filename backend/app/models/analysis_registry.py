"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import AnalysisRecord, analysis_repository as analysis_registry

__all__ = ["AnalysisRecord", "analysis_registry"]
