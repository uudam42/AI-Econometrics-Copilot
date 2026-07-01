from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.data_profiler import profile_dataset


def test_missing_value_profiling():
    df = pd.DataFrame({"x": [1.0, 2.0, None, 4.0, 5.0]})
    report = profile_dataset("ds1", df)
    col = report.columns[0]
    assert col.missing_count == 1
    assert col.missing_rate == 0.2


def test_duplicate_row_detection():
    df = pd.DataFrame({"x": [1, 1, 2, 3], "y": [10, 10, 20, 30]})
    report = profile_dataset("ds1", df)
    assert report.duplicate_row_count == 1
    assert report.duplicate_row_rate == 0.25


def test_constant_column_detection():
    df = pd.DataFrame({"x": [5, 5, 5, 5], "y": [1, 2, 3, 4]})
    report = profile_dataset("ds1", df)
    assert "x" in report.constant_columns
    assert "y" not in report.constant_columns


def test_iqr_outlier_detection():
    values = [10, 11, 12, 11, 10, 12, 13, 500]  # 500 is a clear outlier
    df = pd.DataFrame({"x": values})
    report = profile_dataset("ds1", df)
    col = next(c for c in report.columns if c.column == "x")
    assert col.outlier_count is not None and col.outlier_count >= 1
    assert col.outlier_method in {"IQR", "Z-score"}


def test_log_transform_suggested_for_right_skewed_positive_column():
    rng = np.random.default_rng(0)
    values = rng.lognormal(mean=1.0, sigma=1.2, size=500)
    df = pd.DataFrame({"income": values})
    report = profile_dataset("ds1", df)
    col = next(c for c in report.columns if c.column == "income")
    assert col.skewness is not None and col.skewness > 1.0
    assert col.suggested_transformation == "log"


def test_potential_id_and_time_columns_detected():
    df = pd.DataFrame(
        {
            "record_id": [1, 2, 3, 4, 5],
            "year": [2010, 2011, 2012, 2013, 2014],
            "value": [1.1, 2.2, 3.3, 4.4, 5.5],
        }
    )
    report = profile_dataset("ds1", df)
    assert "record_id" in report.potential_id_columns
    assert "year" in report.potential_time_columns


def test_unique_continuous_float_column_not_flagged_as_id():
    df = pd.DataFrame(
        {
            "country": ["A", "B", "C", "D", "E"],
            "gdp_per_capita": [1023.4, 5321.9, 9981.2, 4433.1, 7765.0],
        }
    )
    report = profile_dataset("ds1", df)
    assert "gdp_per_capita" not in report.potential_id_columns
