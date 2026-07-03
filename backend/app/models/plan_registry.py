"""Backward-compatible re-exports from the persistent storage layer."""
from app.storage.repositories import PlanRecord, plan_repository as plan_registry

__all__ = ["PlanRecord", "plan_registry"]
