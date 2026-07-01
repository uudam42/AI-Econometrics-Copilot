from __future__ import annotations

import pandas as pd

from app.services.column_typing import infer_all_column_types, infer_column_type


def test_numeric_column_gets_outcome_hints():
    series = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5, 6.6])
    info = infer_column_type(series, "gdp_per_capita")
    assert info.inferred_role == "numeric"
    assert "Potential Outcome" in info.role_hints


def test_year_like_numeric_column_detected_as_datetime():
    series = pd.Series([2010, 2011, 2012, 2013, 2010, 2011])
    info = infer_column_type(series, "year")
    assert info.inferred_role == "datetime"
    assert "Possible Time Variable" in info.role_hints


def test_country_like_column_detected_as_entity():
    series = pd.Series(["A", "B", "C", "A", "B", "C"])
    info = infer_column_type(series, "country")
    assert "Possible Entity ID" in info.role_hints


def test_low_cardinality_object_column_is_categorical():
    series = pd.Series(["low", "high", "medium", "low", "high"] * 5)
    info = infer_column_type(series, "risk_bucket")
    assert info.inferred_role == "categorical"


def test_infer_all_column_types_covers_every_column():
    df = pd.DataFrame({"country": ["A", "B"], "year": [2010, 2011], "gdp": [1.0, 2.0]})
    types = infer_all_column_types(df)
    assert {t.name for t in types} == {"country", "year", "gdp"}
