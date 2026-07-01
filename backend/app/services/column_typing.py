"""Rule-driven column type and role-hint inference for the overview page."""
from __future__ import annotations

import re

import pandas as pd

from app.schemas.dataset import ColumnTypeInfo

_ID_NAME_PATTERN = re.compile(r"(^id$|_id$|^id_|code$|identifier)", re.IGNORECASE)
_TIME_NAME_PATTERN = re.compile(r"(year|date|time|period|quarter|month|fiscal)", re.IGNORECASE)
_ENTITY_NAME_PATTERN = re.compile(
    r"(country|entity|firm|company|region|state|province|city|individual|person)",
    re.IGNORECASE,
)

CATEGORICAL_MAX_UNIQUE_RATIO = 0.05
CATEGORICAL_MAX_UNIQUE_COUNT = 50


def _unique_ratio(series: pd.Series) -> float:
    n = len(series)
    return float(series.nunique(dropna=True)) / n if n else 0.0


def infer_column_type(series: pd.Series, name: str) -> ColumnTypeInfo:
    unique_count = int(series.nunique(dropna=True))
    ratio = _unique_ratio(series)
    hints: list[str] = []

    if pd.api.types.is_datetime64_any_dtype(series):
        role = "datetime"
        hints.append("Possible Time Variable")
    elif pd.api.types.is_bool_dtype(series):
        role = "boolean"
        hints.append("Categorical Variable")
    elif pd.api.types.is_numeric_dtype(series):
        looks_like_year = _TIME_NAME_PATTERN.search(name) is not None and series.dropna().between(1000, 3000).mean() > 0.9 if series.dropna().size else False
        if looks_like_year:
            role = "datetime"
            hints.append("Possible Time Variable")
        elif _ID_NAME_PATTERN.search(name) and ratio > 0.9:
            role = "identifier"
            hints.append("Possible Entity ID")
        elif _ENTITY_NAME_PATTERN.search(name) and 0 < ratio < 0.9:
            role = "numeric"
            hints.extend(["Possible Entity ID", "Potential Control"])
        else:
            role = "numeric"
            hints.extend(["Potential Outcome", "Potential Explanatory Variable", "Potential Control"])
    else:
        # object / category dtype
        if _ID_NAME_PATTERN.search(name) and ratio > 0.9:
            role = "identifier"
            hints.append("Possible Entity ID")
        elif _ENTITY_NAME_PATTERN.search(name):
            role = "categorical"
            hints.extend(["Possible Entity ID", "Categorical Variable"])
        elif _TIME_NAME_PATTERN.search(name):
            role = "categorical"
            hints.append("Possible Time Variable")
        elif unique_count <= CATEGORICAL_MAX_UNIQUE_COUNT and ratio <= CATEGORICAL_MAX_UNIQUE_RATIO + 0.45:
            role = "categorical"
            hints.extend(["Categorical Variable", "Potential Control"])
        elif ratio > 0.9:
            role = "identifier"
            hints.append("Possible Entity ID")
        else:
            role = "text"

    return ColumnTypeInfo(
        name=name,
        pandas_dtype=str(series.dtype),
        inferred_role=role,
        unique_count=unique_count,
        unique_ratio=round(ratio, 4),
        role_hints=hints,
    )


def infer_all_column_types(df: pd.DataFrame) -> list[ColumnTypeInfo]:
    return [infer_column_type(df[col], col) for col in df.columns]
