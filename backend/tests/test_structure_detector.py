from __future__ import annotations

import pandas as pd

from app.services.structure_detector import detect_structure


def test_detects_balanced_panel(panel_df):
    result = detect_structure(panel_df)
    assert result.dataset_type == "panel"
    assert result.entity_column == "country"
    assert result.time_column == "year"
    assert result.is_balanced_panel is True
    assert result.entity_count == 3
    assert result.time_period_count == 6


def test_detects_unbalanced_panel(panel_df):
    unbalanced = panel_df.drop(panel_df.index[0])
    result = detect_structure(unbalanced)
    assert result.dataset_type == "panel"
    assert result.is_balanced_panel is False


def test_detects_time_series_without_entity():
    df = pd.DataFrame({"year": list(range(2000, 2020)), "value": range(20)})
    result = detect_structure(df)
    assert result.dataset_type == "time_series"
    assert result.time_column == "year"


def test_detects_cross_sectional_without_time_column():
    df = pd.DataFrame(
        {
            "firm_id": [1, 2, 3, 4, 5],
            "revenue": [100.0, 200.0, 150.0, 300.0, 250.0],
            "employees": [10, 20, 15, 30, 25],
        }
    )
    result = detect_structure(df)
    assert result.dataset_type == "cross_sectional"
