"""Multiple-testing correction for exploratory discovery.

Implements Benjamini-Hochberg FDR and Bonferroni corrections.
All corrections are transparent: both raw and adjusted values are returned.
"""
from __future__ import annotations

from app.schemas.discovery import CorrectedResult, MultipleTestingMethod


def benjamini_hochberg(
    p_values: list[tuple[str, float | None]],
    alpha: float = 0.05,
) -> list[CorrectedResult]:
    valid = [(spec_id, p) for spec_id, p in p_values if p is not None]
    invalid = [(spec_id, p) for spec_id, p in p_values if p is None]

    valid.sort(key=lambda x: x[1])
    m = len(valid)

    results: list[CorrectedResult] = []

    adjusted_ps: list[float] = [0.0] * m
    if m > 0:
        adjusted_ps[-1] = valid[-1][1]
        for i in range(m - 2, -1, -1):
            raw_p = valid[i][1]
            bh_adjusted = raw_p * m / (i + 1)
            adjusted_ps[i] = min(bh_adjusted, adjusted_ps[i + 1])

        for i, (spec_id, raw_p) in enumerate(valid):
            adj_p = min(adjusted_ps[i], 1.0)
            results.append(CorrectedResult(
                spec_id=spec_id,
                raw_p_value=raw_p,
                adjusted_p_value=round(adj_p, 6),
                correction_method="benjamini_hochberg",
                passes_threshold=adj_p < alpha,
            ))

    for spec_id, _ in invalid:
        results.append(CorrectedResult(
            spec_id=spec_id,
            raw_p_value=None,
            adjusted_p_value=None,
            correction_method="benjamini_hochberg",
            passes_threshold=False,
        ))

    return results


def bonferroni(
    p_values: list[tuple[str, float | None]],
    alpha: float = 0.05,
) -> list[CorrectedResult]:
    valid = [(spec_id, p) for spec_id, p in p_values if p is not None]
    invalid = [(spec_id, p) for spec_id, p in p_values if p is None]
    m = len(valid)

    results: list[CorrectedResult] = []
    for spec_id, raw_p in valid:
        adj_p = min(raw_p * m, 1.0)
        results.append(CorrectedResult(
            spec_id=spec_id,
            raw_p_value=raw_p,
            adjusted_p_value=round(adj_p, 6),
            correction_method="bonferroni",
            passes_threshold=adj_p < alpha,
        ))

    for spec_id, _ in invalid:
        results.append(CorrectedResult(
            spec_id=spec_id,
            raw_p_value=None,
            adjusted_p_value=None,
            correction_method="bonferroni",
            passes_threshold=False,
        ))

    return results


def no_correction(
    p_values: list[tuple[str, float | None]],
    alpha: float = 0.05,
) -> list[CorrectedResult]:
    results: list[CorrectedResult] = []
    for spec_id, raw_p in p_values:
        results.append(CorrectedResult(
            spec_id=spec_id,
            raw_p_value=raw_p,
            adjusted_p_value=raw_p,
            correction_method="none",
            passes_threshold=raw_p is not None and raw_p < alpha,
        ))
    return results


def apply_correction(
    p_values: list[tuple[str, float | None]],
    method: MultipleTestingMethod,
    alpha: float = 0.05,
) -> list[CorrectedResult]:
    if method == "benjamini_hochberg":
        return benjamini_hochberg(p_values, alpha)
    elif method == "bonferroni":
        return bonferroni(p_values, alpha)
    else:
        return no_correction(p_values, alpha)
