"""Reserved interface: Autonomous Econometric Discovery Engine (future phase).

NOT implemented in this MVP and NOT wired into any API route.

Future scope (explicitly bounded, never unconstrained search):
    1. Propose a small number of candidate dependent variables from the dataset.
    2. Filter plausible independent/control variables using domain-agnostic
       rules (data type, missingness, variance, collinearity) — not blind
       combinatorics over all columns.
    3. Generate a limited set of candidate models (see `model_planner.py`).
    4. Run real statistical tests via `app.services` (never LLM-guessed stats).
    5. Apply multiple-testing correction and flag it explicitly.
    6. Return findings labeled unambiguously as:
         - "Exploratory finding"
         - "Not causal evidence"
         - "Requires theory-driven validation"

Every finding object returned by a future implementation MUST include the
three labels above verbatim so the UI can render the appropriate warnings.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class ExploratoryFinding(Protocol):
    dependent_variable: str
    independent_variable: str
    association_summary: str
    p_value: float
    labels: list[str]  # must include the three mandatory labels


class DiscoveryEngine(Protocol):
    def discover(self, df: pd.DataFrame, max_candidate_models: int = 10) -> list[dict]:
        """Return a bounded list of exploratory findings. Must not run unconstrained search."""
        ...


class NotImplementedDiscoveryEngine:
    """Explicit no-op used until Phase 5 (see docs/development_plan.md) is built."""

    def discover(self, df: pd.DataFrame, max_candidate_models: int = 10) -> list[dict]:
        raise NotImplementedError(
            "The Autonomous Econometric Discovery Engine is reserved for a future "
            "phase and is not available in this build."
        )
