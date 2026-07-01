"""Reserved interface: constrained model planning.

Future scope: given a user-confirmed dependent variable, a small set of
candidate independent/control variables, and the detected dataset structure,
propose a short, ranked list of model specifications (formula + estimator +
fixed-effects configuration) for the user to review and run — never run
unconstrained/automatic search.

The MVP's `app.services` model execution is invoked directly by the user via
explicit configuration; this module is not wired into that flow yet.
"""
from __future__ import annotations

from typing import Protocol

import pandas as pd

from app.schemas.dataset import StructureDetectionResult


class CandidateModelSpec(Protocol):
    formula: str
    estimator: str
    rationale: str


class ModelPlanner(Protocol):
    def propose_specifications(
        self,
        df: pd.DataFrame,
        dependent_variable: str,
        candidate_independent_variables: list[str],
        structure: StructureDetectionResult,
    ) -> list[dict]:
        """Return a small (bounded) list of candidate model specs for human review."""
        ...


class MockModelPlanner:
    """Deterministic placeholder: proposes at most one specification per
    compatible estimator, based only on the already-detected data structure.
    Performs no search and no estimation.
    """

    MAX_SPECIFICATIONS = 3

    def propose_specifications(
        self,
        df: pd.DataFrame,
        dependent_variable: str,
        candidate_independent_variables: list[str],
        structure: StructureDetectionResult,
    ) -> list[dict]:
        rhs = " + ".join(candidate_independent_variables) if candidate_independent_variables else "1"
        formula = f"{dependent_variable} ~ {rhs}"
        specs = [
            {
                "formula": formula,
                "estimator": "ols",
                "rationale": "Baseline specification for comparison.",
            }
        ]
        if structure.dataset_type == "panel":
            specs.append(
                {
                    "formula": formula,
                    "estimator": "fixed_effects",
                    "rationale": (
                        f"Panel structure detected ('{structure.entity_column}' x "
                        f"'{structure.time_column}'); entity fixed effects control for "
                        "time-invariant unobserved heterogeneity."
                    ),
                }
            )
            specs.append(
                {
                    "formula": formula,
                    "estimator": "two_way_fixed_effects",
                    "rationale": "Adds time fixed effects to control for common shocks across entities.",
                }
            )
        return specs[: self.MAX_SPECIFICATIONS]
