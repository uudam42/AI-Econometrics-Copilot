"""Data transformation engine — applies user-approved operations to a copy of the dataset.

The original uploaded DataFrame is NEVER modified. All operations produce a new
derived DataFrame stored in DatasetRecord.processed_dataframe.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import mstats

from app.core.errors import ValidationAppError
from app.schemas.modeling import TransformationLogEntry, TransformationOp


def _safe_float(v: Any) -> float | None:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Individual operation functions
# ──────────────────────────────────────────────────────────────────────────────

def _apply_drop_duplicates(
    df: pd.DataFrame, columns: list[str], params: dict, step: int
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    rows_before = len(df)
    df_out = df.drop_duplicates()
    rows_after = len(df_out)
    return df_out, TransformationLogEntry(
        step=step,
        operation="drop_duplicates",
        columns=[],
        parameters=params,
        reason="User-approved: remove exact duplicate rows.",
        rows_before=rows_before,
        rows_after=rows_after,
    )


def _apply_drop_missing_rows(
    df: pd.DataFrame, columns: list[str], params: dict, step: int
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    if not columns:
        raise ValidationAppError(
            "Cannot drop rows with missing values because no columns were specified."
        )
    for col in columns:
        if col not in df.columns:
            raise ValidationAppError(f"Column '{col}' does not exist in the dataset.")
    rows_before = len(df)
    df_out = df.dropna(subset=columns)
    rows_after = len(df_out)
    if rows_after == 0:
        raise ValidationAppError(
            "Dropping rows with missing values in the selected columns would remove "
            "all observations. The operation was rejected to prevent an empty dataset."
        )
    return df_out, TransformationLogEntry(
        step=step,
        operation="drop_missing_rows",
        columns=columns,
        parameters=params,
        reason="User-approved: remove rows with missing values in selected columns.",
        rows_before=rows_before,
        rows_after=rows_after,
    )


def _apply_imputation(
    df: pd.DataFrame,
    columns: list[str],
    params: dict,
    step: int,
    method: str,
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    if not columns:
        raise ValidationAppError(
            f"Cannot apply {method} imputation because no columns were specified."
        )
    df_out = df.copy()
    for col in columns:
        if col not in df_out.columns:
            raise ValidationAppError(f"Column '{col}' does not exist in the dataset.")
        if not pd.api.types.is_numeric_dtype(df_out[col]):
            raise ValidationAppError(
                f"Cannot run {method} imputation because column '{col}' is not numeric."
            )
        fill_value = df_out[col].median() if method == "median" else df_out[col].mean()
        df_out[col] = df_out[col].fillna(fill_value)
    rows_before = len(df)
    return df_out, TransformationLogEntry(
        step=step,
        operation=f"{method}_imputation",
        columns=columns,
        parameters=params,
        reason=f"User-approved: fill missing values with column {method}.",
        rows_before=rows_before,
        rows_after=rows_before,
    )


def _apply_winsorize(
    df: pd.DataFrame, columns: list[str], params: dict, step: int
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    if not columns:
        raise ValidationAppError(
            "Cannot apply winsorization because no columns were specified."
        )
    lower_q = float(params.get("lower_quantile", 0.01))
    upper_q = float(params.get("upper_quantile", 0.99))
    if not (0.0 <= lower_q < upper_q <= 1.0):
        raise ValidationAppError(
            "Winsorization quantiles must satisfy 0 ≤ lower_quantile < upper_quantile ≤ 1."
        )
    df_out = df.copy()
    created_columns: list[str] = []
    for col in columns:
        if col not in df_out.columns:
            raise ValidationAppError(f"Column '{col}' does not exist in the dataset.")
        if not pd.api.types.is_numeric_dtype(df_out[col]):
            raise ValidationAppError(
                f"Cannot winsorize column '{col}' because it is not numeric."
            )
        new_col = f"{col}_wins"
        series = df_out[col].dropna()
        low_val = series.quantile(lower_q)
        high_val = series.quantile(upper_q)
        df_out[new_col] = df_out[col].clip(lower=low_val, upper=high_val)
        created_columns.append(new_col)
    rows_before = len(df)
    return df_out, TransformationLogEntry(
        step=step,
        operation="winsorize",
        columns=columns,
        parameters=params,
        reason="User-approved: clip extreme values at specified quantile bounds.",
        rows_before=rows_before,
        rows_after=rows_before,
        created_columns=created_columns,
    )


def _apply_log_transform(
    df: pd.DataFrame, columns: list[str], params: dict, step: int
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    if not columns:
        raise ValidationAppError(
            "Cannot apply log transformation because no columns were specified."
        )
    df_out = df.copy()
    created_columns: list[str] = []
    for col in columns:
        if col not in df_out.columns:
            raise ValidationAppError(f"Column '{col}' does not exist in the dataset.")
        if not pd.api.types.is_numeric_dtype(df_out[col]):
            raise ValidationAppError(
                f"Cannot apply log transformation because column '{col}' is not numeric."
            )
        valid = df_out[col].dropna()
        if (valid <= 0).any():
            raise ValidationAppError(
                f"Cannot apply log transformation because column '{col}' contains "
                "zero or negative values. Log transform requires strictly positive values."
            )
        new_col = f"log_{col}"
        df_out[new_col] = np.log(df_out[col])
        created_columns.append(new_col)
    rows_before = len(df)
    return df_out, TransformationLogEntry(
        step=step,
        operation="log_transform",
        columns=columns,
        parameters=params,
        reason="User-approved: apply natural log to reduce skewness.",
        rows_before=rows_before,
        rows_after=rows_before,
        created_columns=created_columns,
    )


def _apply_standardize(
    df: pd.DataFrame, columns: list[str], params: dict, step: int
) -> tuple[pd.DataFrame, TransformationLogEntry]:
    if not columns:
        raise ValidationAppError(
            "Cannot apply standardization because no columns were specified."
        )
    df_out = df.copy()
    created_columns: list[str] = []
    for col in columns:
        if col not in df_out.columns:
            raise ValidationAppError(f"Column '{col}' does not exist in the dataset.")
        if not pd.api.types.is_numeric_dtype(df_out[col]):
            raise ValidationAppError(
                f"Cannot standardize column '{col}' because it is not numeric."
            )
        mean = df_out[col].mean()
        std = df_out[col].std()
        if std == 0 or np.isnan(std):
            raise ValidationAppError(
                f"Cannot standardize column '{col}' because it has zero variance "
                "(constant column)."
            )
        new_col = f"{col}_std"
        df_out[new_col] = (df_out[col] - mean) / std
        created_columns.append(new_col)
    rows_before = len(df)
    return df_out, TransformationLogEntry(
        step=step,
        operation="standardize",
        columns=columns,
        parameters=params,
        reason="User-approved: z-score standardization (subtract mean, divide by std).",
        rows_before=rows_before,
        rows_after=rows_before,
        created_columns=created_columns,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point
# ──────────────────────────────────────────────────────────────────────────────

_HANDLERS: dict[str, Any] = {
    "drop_duplicates": _apply_drop_duplicates,
    "drop_missing_rows": _apply_drop_missing_rows,
    "median_imputation": lambda df, cols, p, s: _apply_imputation(df, cols, p, s, "median"),
    "mean_imputation": lambda df, cols, p, s: _apply_imputation(df, cols, p, s, "mean"),
    "winsorize": _apply_winsorize,
    "log_transform": _apply_log_transform,
    "standardize": _apply_standardize,
}


def apply_transformations(
    df: pd.DataFrame,
    operations: list[dict],
) -> tuple[pd.DataFrame, list[TransformationLogEntry]]:
    """Apply a sequence of transformations to *a copy* of df.

    Returns (processed_df, transformation_log).
    Raises ValidationAppError on any invalid input.
    """
    result = df.copy()
    log: list[TransformationLogEntry] = []

    for step, op in enumerate(operations, start=1):
        operation: str = op.get("operation", "")
        columns: list[str] = op.get("columns", [])
        params: dict = op.get("parameters", {})

        handler = _HANDLERS.get(operation)
        if handler is None:
            raise ValidationAppError(f"Unknown transformation operation: '{operation}'.")

        result, entry = handler(result, columns, params, step)
        log.append(entry)

    return result, log
