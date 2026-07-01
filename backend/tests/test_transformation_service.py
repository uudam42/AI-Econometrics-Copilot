"""Tests for the data transformation service."""
from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from app.core.errors import ValidationAppError
from app.services.transformation_service import apply_transformations


@pytest.fixture()
def base_df() -> pd.DataFrame:
    return pd.DataFrame({
        "y": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 100.0, 1000.0],
        "x1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "x2": [5.0, 5.0, 5.0, np.nan, 5.0, 5.0, 5.0, 5.0],
        "cat": ["a", "b", "a", "b", "a", "b", "a", "b"],
    })


def test_drop_duplicates(base_df):
    df_dup = pd.concat([base_df, base_df.iloc[:2]], ignore_index=True)
    result_df, log = apply_transformations(df_dup, [{"operation": "drop_duplicates", "columns": [], "parameters": {}}])
    assert len(result_df) == len(base_df)
    assert log[0].operation == "drop_duplicates"
    assert log[0].rows_before == len(df_dup)
    assert log[0].rows_after == len(base_df)


def test_drop_missing_rows(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "drop_missing_rows", "columns": ["x2"], "parameters": {}}],
    )
    assert result_df["x2"].isna().sum() == 0
    assert len(result_df) == len(base_df) - 1
    assert log[0].rows_before == len(base_df)


def test_drop_missing_rows_no_columns_raises(base_df):
    with pytest.raises(ValidationAppError, match="no columns"):
        apply_transformations(base_df, [{"operation": "drop_missing_rows", "columns": [], "parameters": {}}])


def test_median_imputation(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "median_imputation", "columns": ["x2"], "parameters": {}}],
    )
    assert result_df["x2"].isna().sum() == 0
    assert result_df["x2"].iloc[3] == pytest.approx(5.0)
    assert log[0].operation == "median_imputation"
    assert len(result_df) == len(base_df)


def test_mean_imputation(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "mean_imputation", "columns": ["x2"], "parameters": {}}],
    )
    assert result_df["x2"].isna().sum() == 0
    assert log[0].operation == "mean_imputation"


def test_imputation_non_numeric_raises(base_df):
    with pytest.raises(ValidationAppError, match="not numeric"):
        apply_transformations(base_df, [{"operation": "median_imputation", "columns": ["cat"], "parameters": {}}])


def test_winsorize_creates_new_column(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "winsorize", "columns": ["y"], "parameters": {"lower_quantile": 0.05, "upper_quantile": 0.95}}],
    )
    assert "y_wins" in result_df.columns
    assert "y" in result_df.columns  # original preserved
    assert log[0].created_columns == ["y_wins"]
    assert result_df["y_wins"].max() <= result_df["y"].quantile(0.95)


def test_winsorize_default_quantiles(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "winsorize", "columns": ["y"], "parameters": {}}],
    )
    assert "y_wins" in result_df.columns


def test_winsorize_non_numeric_raises(base_df):
    with pytest.raises(ValidationAppError, match="not numeric"):
        apply_transformations(base_df, [{"operation": "winsorize", "columns": ["cat"], "parameters": {}}])


def test_log_transform_creates_new_column(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "log_transform", "columns": ["y"], "parameters": {}}],
    )
    assert "log_y" in result_df.columns
    assert "y" in result_df.columns  # original preserved
    assert log[0].created_columns == ["log_y"]
    assert result_df["log_y"].iloc[0] == pytest.approx(np.log(10.0))


def test_log_transform_fails_on_non_positive():
    df = pd.DataFrame({"y": [1.0, -1.0, 3.0]})
    with pytest.raises(ValidationAppError, match="zero or negative"):
        apply_transformations(df, [{"operation": "log_transform", "columns": ["y"], "parameters": {}}])


def test_log_transform_fails_on_zero():
    df = pd.DataFrame({"y": [0.0, 1.0, 2.0]})
    with pytest.raises(ValidationAppError, match="zero or negative"):
        apply_transformations(df, [{"operation": "log_transform", "columns": ["y"], "parameters": {}}])


def test_log_transform_non_numeric_raises(base_df):
    with pytest.raises(ValidationAppError, match="not numeric"):
        apply_transformations(base_df, [{"operation": "log_transform", "columns": ["cat"], "parameters": {}}])


def test_standardize_creates_new_column(base_df):
    result_df, log = apply_transformations(
        base_df,
        [{"operation": "standardize", "columns": ["x1"], "parameters": {}}],
    )
    assert "x1_std" in result_df.columns
    assert "x1" in result_df.columns  # original preserved
    assert abs(result_df["x1_std"].mean()) < 1e-10
    assert abs(result_df["x1_std"].std() - 1.0) < 0.01


def test_standardize_non_numeric_raises(base_df):
    with pytest.raises(ValidationAppError, match="not numeric"):
        apply_transformations(base_df, [{"operation": "standardize", "columns": ["cat"], "parameters": {}}])


def test_transformation_log_has_correct_steps(base_df):
    ops = [
        {"operation": "median_imputation", "columns": ["x2"], "parameters": {}},
        {"operation": "log_transform", "columns": ["y"], "parameters": {}},
    ]
    _, log = apply_transformations(base_df, ops)
    assert len(log) == 2
    assert log[0].step == 1
    assert log[1].step == 2


def test_original_df_not_mutated(base_df):
    original_len = len(base_df)
    original_cols = list(base_df.columns)
    apply_transformations(
        base_df,
        [
            {"operation": "drop_missing_rows", "columns": ["x2"], "parameters": {}},
            {"operation": "log_transform", "columns": ["y"], "parameters": {}},
        ],
    )
    assert len(base_df) == original_len
    assert list(base_df.columns) == original_cols


def test_unknown_operation_raises():
    df = pd.DataFrame({"y": [1.0, 2.0]})
    with pytest.raises(ValidationAppError, match="Unknown transformation"):
        apply_transformations(df, [{"operation": "not_real_op", "columns": [], "parameters": {}}])
