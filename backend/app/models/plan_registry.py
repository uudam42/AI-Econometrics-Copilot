"""In-process registry for research plans."""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.errors import ModelNotFoundError
from app.schemas.planning import ResearchPlan


@dataclass
class PlanRecord:
    plan_id: str
    dataset_id: str
    plan: ResearchPlan
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved: bool = False


class PlanRegistry:
    def __init__(self) -> None:
        self._records: dict[str, PlanRecord] = {}
        self._lock = threading.Lock()

    def create(self, plan: ResearchPlan, dataset_id: str) -> PlanRecord:
        record = PlanRecord(
            plan_id=plan.plan_id,
            dataset_id=dataset_id,
            plan=plan,
        )
        with self._lock:
            self._records[plan.plan_id] = record
        return record

    def get(self, plan_id: str) -> PlanRecord:
        with self._lock:
            record = self._records.get(plan_id)
        if record is None:
            raise ModelNotFoundError(f"No research plan found with id '{plan_id}'.")
        return record

    def mark_approved(self, plan_id: str) -> PlanRecord:
        record = self.get(plan_id)
        record.approved = True
        return record

    def exists(self, plan_id: str) -> bool:
        with self._lock:
            return plan_id in self._records


plan_registry = PlanRegistry()
