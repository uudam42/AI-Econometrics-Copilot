"""Variable eligibility screening for exploratory discovery.

Evaluates each column for suitability as an outcome or predictor variable.
Exclusion reasons are transparent and reported to the user.
"""
from __future__ import annotations

import re

import pandas as pd

from app.schemas.discovery import VariableEligibility
from app.services.column_typing import (
    _ENTITY_NAME_PATTERN,
    _ID_NAME_PATTERN,
    _TIME_NAME_PATTERN,
    infer_column_type,
)


def _looks_like_year(series: pd.Series) -> bool:
    clean = series.dropna()
    if clean.empty or not pd.api.types.is_numeric_dtype(series):
        return False
    return bool(clean.between(1000, 3000).mean() > 0.9)


def _is_near_duplicate(
    series: pd.Series,
    other_series: pd.Series,
    threshold: float = 0.999,
) -> bool:
    both_valid = series.notna() & other_series.notna()
    if both_valid.sum() < 10:
        return False
    try:
        corr = series[both_valid].corr(other_series[both_valid])
        return corr is not None and abs(corr) > threshold
    except Exception:
        return False


def screen_variables(
    df: pd.DataFrame,
    excluded_variables: list[str],
    max_missing_rate: float = 0.30,
    min_observations: int = 50,
    min_unique_values: int = 8,
) -> list[VariableEligibility]:
    results: list[VariableEligibility] = []
    n_rows = len(df)
    numeric_cols: list[str] = []

    for col in df.columns:
        series = df[col]
        reasons: list[str] = []
        missing_count = int(series.isna().sum())
        missing_rate = missing_count / n_rows if n_rows > 0 else 1.0
        non_missing = n_rows - missing_count
        unique_count = int(series.nunique(dropna=True))
        is_constant = unique_count <= 1

        if col in excluded_variables:
            reasons.append("Excluded by user")

        if not pd.api.types.is_numeric_dtype(series):
            reasons.append(f"Non-numeric dtype ({series.dtype})")

        if _ID_NAME_PATTERN.search(col):
            col_info = infer_column_type(series, col)
            if col_info.inferred_role == "identifier":
                reasons.append("Likely identifier column (ID pattern)")

        if _ENTITY_NAME_PATTERN.search(col):
            reasons.append("Likely entity identifier column")

        if _TIME_NAME_PATTERN.search(col) or _looks_like_year(series):
            reasons.append("Likely time variable")

        if is_constant:
            reasons.append("Constant or near-constant (≤1 unique value)")

        if missing_rate > max_missing_rate:
            reasons.append(
                f"Missing rate {missing_rate:.1%} exceeds threshold {max_missing_rate:.0%}"
            )

        if non_missing < min_observations:
            reasons.append(
                f"Only {non_missing} non-missing observations (minimum: {min_observations})"
            )

        if pd.api.types.is_numeric_dtype(series) and unique_count < min_unique_values:
            reasons.append(
                f"Only {unique_count} unique values (minimum: {min_unique_values})"
            )

        quality = 0.0
        if not reasons and pd.api.types.is_numeric_dtype(series):
            completeness = 1.0 - missing_rate
            variation = min(unique_count / max(n_rows * 0.1, 1), 1.0)
            quality = round(0.6 * completeness + 0.4 * variation, 3)
            numeric_cols.append(col)

        results.append(VariableEligibility(
            column_name=col,
            eligible=len(reasons) == 0 and pd.api.types.is_numeric_dtype(series),
            exclusion_reasons=reasons,
            missing_rate=round(missing_rate, 4),
            unique_values=unique_count,
            is_constant=is_constant,
            quality_score=quality,
        ))

    # Near-duplicate detection among eligible columns
    eligible_names = [r.column_name for r in results if r.eligible]
    for i, col_a in enumerate(eligible_names):
        for col_b in eligible_names[i + 1:]:
            if _is_near_duplicate(df[col_a], df[col_b]):
                for r in results:
                    if r.column_name == col_b and r.eligible:
                        r.exclusion_reasons.append(
                            f"Near-duplicate of '{col_a}' (correlation > 0.999)"
                        )
                        r.eligible = False
                        r.quality_score = 0.0
                        break

    return results


def select_candidate_outcomes(
    eligibility: list[VariableEligibility],
    max_outcomes: int = 5,
    user_specified: list[str] | None = None,
) -> list[str]:
    if user_specified:
        return [
            v for v in user_specified
            if any(e.column_name == v and e.eligible for e in eligibility)
        ]

    eligible = sorted(
        [e for e in eligibility if e.eligible],
        key=lambda e: -e.quality_score,
    )
    return [e.column_name for e in eligible[:max_outcomes]]


def select_candidate_predictors(
    df: pd.DataFrame,
    outcome: str,
    eligibility: list[VariableEligibility],
    max_predictors: int = 10,
) -> list[str]:
    eligible = [
        e for e in eligibility
        if e.eligible and e.column_name != outcome
    ]

    scored: list[tuple[str, float]] = []
    outcome_series = df[outcome].dropna()

    for e in eligible:
        series = df[e.column_name]
        both_valid = outcome_series.index.intersection(series.dropna().index)
        overlap = len(both_valid) / max(len(outcome_series), 1)

        try:
            corr = abs(df[outcome].corr(series))
            if corr != corr:  # NaN
                corr = 0.0
        except Exception:
            corr = 0.0

        score = 0.4 * e.quality_score + 0.3 * min(corr, 1.0) + 0.3 * overlap
        scored.append((e.column_name, score))

    scored.sort(key=lambda x: -x[1])
    return [name for name, _ in scored[:max_predictors]]
