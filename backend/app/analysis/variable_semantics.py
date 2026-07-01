"""Reserved interface: variable semantic role inference.

Not implemented in the MVP. Today, role hints in `app.services.column_typing`
are purely rule-driven (name patterns + cardinality). This module reserves a
seam for a future component that reasons about *meaning* — e.g. recognizing
that "gdp_per_capita" is an economic outcome variable, or that "internet_users"
is a plausible explanatory variable for a development-economics question.

Any future implementation must still route through real statistical
computation (see `app.services.data_profiler`, `app.services.structure_detector`)
for anything reported as a number to the user. This module may only suggest
candidate roles/labels for human review — it must never assert significance,
coefficients, or causal claims.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd


class VariableSemanticsEngine(Protocol):
    """Future contract for semantic variable role suggestion."""

    def suggest_roles(self, df: pd.DataFrame) -> list[dict]:
        """Return a list of {column, suggested_role, confidence, rationale} dicts.

        `suggested_role` must be one of the existing rule-based roles
        (Potential Outcome / Potential Explanatory Variable / Potential Control /
        Possible Entity ID / Possible Time Variable / Categorical Variable).
        Confidence and rationale must be exposed to the user — no silent
        overriding of user selections is permitted.
        """
        ...


class MockVariableSemanticsEngine:
    """Deterministic placeholder used until a real semantics engine is built.

    Delegates entirely to the existing rule-based column typing so behaviour
    stays explainable and testable; adds no new inference.
    """

    def suggest_roles(self, df: pd.DataFrame) -> list[dict]:
        from app.services.column_typing import infer_all_column_types

        return [
            {
                "column": col.name,
                "suggested_role": col.role_hints[0] if col.role_hints else "unknown",
                "confidence": 0.5 if col.role_hints else 0.0,
                "rationale": "Derived from rule-based column typing (name patterns + cardinality). "
                "No semantic model is active in this build.",
            }
            for col in infer_all_column_types(df)
        ]
