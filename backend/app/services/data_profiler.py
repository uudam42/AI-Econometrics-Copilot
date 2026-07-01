"""DatasetProfiler — rule-driven, explainable data quality analysis.

Detects missing values, duplicates, constant columns, outliers (IQR + Z-score),
distribution shape, and candidate ID/time/categorical columns. Every numeric
result is computed with pandas/numpy/scipy; nothing here is inferred by an LLM.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from app.core.config import settings
from app.schemas.dataset import ColumnQualityReport, DatasetQualityReport
from app.services.column_typing import _ID_NAME_PATTERN, _TIME_NAME_PATTERN


def _iqr_outlier_count(series: pd.Series) -> int:
    clean = series.dropna()
    if clean.empty:
        return 0
    q1, q3 = clean.quantile(0.25), clean.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    lower = q1 - settings.outlier_iqr_multiplier * iqr
    upper = q3 + settings.outlier_iqr_multiplier * iqr
    return int(((clean < lower) | (clean > upper)).sum())


def _zscore_outlier_count(series: pd.Series) -> int:
    clean = series.dropna()
    if clean.empty or clean.std(ddof=0) == 0:
        return 0
    z = np.abs(stats.zscore(clean))
    return int((z > settings.outlier_zscore_threshold).sum())


def _suggest_transformation(series: pd.Series, skewness: float | None) -> tuple[str | None, str | None]:
    clean = series.dropna()
    if clean.empty or skewness is None:
        return None, None

    all_positive = bool((clean > 0).all())
    if all_positive and skewness > settings.high_skew_threshold:
        return "log", "Variable is positive and heavily right-skewed."
    if skewness < -settings.high_skew_threshold:
        return "winsorize", "Variable is heavily left-skewed; consider winsorizing extreme values."
    if abs(skewness) > settings.high_skew_threshold and not all_positive:
        return "winsorize", "Variable is skewed and contains non-positive values, so log transform is not directly applicable."
    return None, None


def _profile_numeric_column(name: str, series: pd.Series) -> ColumnQualityReport:
    clean = series.dropna()
    n = len(series)
    missing = int(series.isna().sum())
    is_constant = bool(clean.nunique(dropna=True) <= 1)

    skewness = float(stats.skew(clean)) if len(clean) > 2 and clean.std(ddof=0) > 0 else None
    kurtosis = float(stats.kurtosis(clean)) if len(clean) > 2 and clean.std(ddof=0) > 0 else None

    outlier_count = _iqr_outlier_count(series)
    outlier_method = "IQR"
    # Fall back to Z-score when IQR is degenerate (e.g. zero IQR) but data still varies.
    if outlier_count == 0 and clean.std(ddof=0) > 0:
        z_count = _zscore_outlier_count(series)
        if z_count > 0:
            outlier_count, outlier_method = z_count, "Z-score"

    zero_ratio = float((clean == 0).mean()) if len(clean) else None
    negative_ratio = float((clean < 0).mean()) if len(clean) else None

    suggestion, reason = _suggest_transformation(series, skewness)

    return ColumnQualityReport(
        column=name,
        dtype=str(series.dtype),
        missing_count=missing,
        missing_rate=round(missing / n, 4) if n else 0.0,
        is_constant=is_constant,
        outlier_count=outlier_count,
        outlier_method=outlier_method,
        zero_ratio=round(zero_ratio, 4) if zero_ratio is not None else None,
        negative_ratio=round(negative_ratio, 4) if negative_ratio is not None else None,
        skewness=round(skewness, 4) if skewness is not None else None,
        kurtosis=round(kurtosis, 4) if kurtosis is not None else None,
        suggested_transformation=suggestion,
        reason=reason,
    )


def _profile_non_numeric_column(name: str, series: pd.Series) -> ColumnQualityReport:
    n = len(series)
    missing = int(series.isna().sum())
    non_null = series.dropna()
    is_constant = bool(non_null.nunique() <= 1)
    return ColumnQualityReport(
        column=name,
        dtype=str(series.dtype),
        missing_count=missing,
        missing_rate=round(missing / n, 4) if n else 0.0,
        is_constant=is_constant,
    )


def _detect_potential_id_columns(df: pd.DataFrame) -> list[str]:
    """A column is a plausible ID only if it is (near-)unique AND either its
    name matches an ID-like pattern or it holds discrete (int/string) values —
    a fully-unique continuous float measure (e.g. gdp_per_capita) is not an ID.
    """
    candidates = []
    n = len(df)
    for col in df.columns:
        series = df[col]
        ratio = series.nunique(dropna=True) / n if n else 0
        if ratio < 0.98:
            continue
        is_discrete = not pd.api.types.is_float_dtype(series)
        if _ID_NAME_PATTERN.search(col) or (ratio == 1.0 and is_discrete):
            candidates.append(col)
    return candidates


def _detect_potential_time_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            candidates.append(col)
            continue
        if _TIME_NAME_PATTERN.search(col):
            candidates.append(col)
            continue
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean) and clean.between(1000, 3000).mean() > 0.9:
                candidates.append(col)
    return candidates


def _detect_potential_categorical_columns(df: pd.DataFrame) -> list[str]:
    candidates = []
    n = len(df)
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            continue
        unique_count = series.nunique(dropna=True)
        ratio = unique_count / n if n else 0
        if unique_count <= 50 and ratio <= 0.5:
            candidates.append(col)
    return candidates


def profile_dataset(dataset_id: str, df: pd.DataFrame) -> DatasetQualityReport:
    n_rows, n_columns = df.shape
    duplicate_row_count = int(df.duplicated().sum())

    column_reports: list[ColumnQualityReport] = []
    constant_columns: list[str] = []

    for col in df.columns:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            report = _profile_numeric_column(col, series)
        else:
            report = _profile_non_numeric_column(col, series)
        column_reports.append(report)
        if report.is_constant:
            constant_columns.append(col)

    return DatasetQualityReport(
        dataset_id=dataset_id,
        n_rows=n_rows,
        n_columns=n_columns,
        duplicate_row_count=duplicate_row_count,
        duplicate_row_rate=round(duplicate_row_count / n_rows, 4) if n_rows else 0.0,
        constant_columns=constant_columns,
        potential_id_columns=_detect_potential_id_columns(df),
        potential_time_columns=_detect_potential_time_columns(df),
        potential_categorical_columns=_detect_potential_categorical_columns(df),
        columns=column_reports,
    )
