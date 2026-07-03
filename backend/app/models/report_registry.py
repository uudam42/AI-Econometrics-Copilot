"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import ReportRecord, report_repository as report_registry

__all__ = ["ReportRecord", "report_registry"]
