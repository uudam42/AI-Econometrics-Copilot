"""Rule-driven detection of cross-sectional / time-series / panel data structure.

Decisions are based on cardinality, repetition patterns, and value ranges —
never on column names alone — so the result is explainable and reproducible.
"""
from __future__ import annotations

import pandas as pd

from app.schemas.dataset import StructureDetectionResult
from app.services.column_typing import _ENTITY_NAME_PATTERN, _ID_NAME_PATTERN, _TIME_NAME_PATTERN


def _looks_like_year_series(series: pd.Series) -> bool:
    clean = series.dropna()
    if clean.empty:
        return False
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    if pd.api.types.is_numeric_dtype(series):
        return bool(clean.between(1000, 3000).mean() > 0.9)
    return False


def _candidate_time_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    for col in df.columns:
        series = df[col]
        if _looks_like_year_series(series) or _TIME_NAME_PATTERN.search(col):
            n_unique = series.nunique(dropna=True)
            if n_unique > 1:
                candidates.append(col)
    return candidates


def _candidate_entity_columns(df: pd.DataFrame, time_col: str | None) -> list[str]:
    n = len(df)
    candidates = []
    for col in df.columns:
        if col == time_col:
            continue
        series = df[col]
        n_unique = series.nunique(dropna=True)
        if n_unique < 2 or n_unique >= n:
            continue
        # An entity column must repeat: each value appears on average > 1 time.
        avg_repeat = n / n_unique
        name_matches = bool(_ENTITY_NAME_PATTERN.search(col) or _ID_NAME_PATTERN.search(col))
        if avg_repeat > 1.5 or name_matches:
            candidates.append((col, avg_repeat, name_matches))

    # Prefer name-matching columns, then higher repetition.
    candidates.sort(key=lambda c: (not c[2], -c[1]))
    return [c[0] for c in candidates]


def detect_structure(df: pd.DataFrame) -> StructureDetectionResult:
    time_candidates = _candidate_time_columns(df)

    if not time_candidates:
        return StructureDetectionResult(
            dataset_type="cross_sectional",
            explanation=(
                "No column with repeated, multi-valued time-like data (year/date/period) "
                "was found, so the dataset is treated as cross-sectional."
            ),
        )

    time_col = time_candidates[0]
    entity_candidates = _candidate_entity_columns(df, time_col)

    if not entity_candidates:
        n_periods = int(df[time_col].nunique(dropna=True))
        return StructureDetectionResult(
            dataset_type="time_series",
            time_column=time_col,
            time_period_count=n_periods,
            explanation=(
                f"Column '{time_col}' has {n_periods} unique, repeated time values, "
                "but no repeated entity/grouping column was found alongside it. "
                "Treated as a single time series."
            ),
        )

    entity_col = entity_candidates[0]
    entity_count = int(df[entity_col].nunique(dropna=True))
    time_count = int(df[time_col].nunique(dropna=True))

    group_sizes = df.groupby(entity_col)[time_col].nunique()
    is_balanced = bool((group_sizes == time_count).all()) if len(group_sizes) else False

    return StructureDetectionResult(
        dataset_type="panel",
        entity_column=entity_col,
        time_column=time_col,
        is_balanced_panel=is_balanced,
        entity_count=entity_count,
        time_period_count=time_count,
        explanation=(
            f"Detected repeated '{entity_col}' observations across {time_count} distinct "
            f"values of '{time_col}' ({entity_count} entities), consistent with panel data. "
            f"{'Every entity has the same number of periods (balanced).' if is_balanced else 'Entities have differing numbers of periods (unbalanced).'}"
        ),
    )
