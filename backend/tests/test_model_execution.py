"""Tests for OLS, panel regression, and diagnostics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.analysis.diagnostics import (
    compute_breusch_pagan,
    compute_correlation_matrix,
    compute_descriptive_stats,
    compute_durbin_watson,
    compute_jarque_bera,
    compute_vif,
)
from app.analysis.ols_models import run_ols
from app.analysis.panel_models import run_panel
from app.core.errors import ModelExecutionError, ValidationAppError


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def cross_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 50
    x = rng.uniform(1, 10, n)
    y = 2.0 + 3.0 * x + rng.normal(0, 0.5, n)
    return pd.DataFrame({"y": y, "x": x, "z": rng.uniform(0, 5, n)})


@pytest.fixture()
def panel_df_large() -> pd.DataFrame:
    rows = []
    rng = np.random.default_rng(0)
    countries = [f"C{i}" for i in range(5)]
    for country in countries:
        for year in range(2010, 2020):
            gdp = 1000 + (year - 2010) * 50 + rng.normal(0, 20)
            internet = 10 + (year - 2010) * 3 + rng.normal(0, 1)
            rows.append({"country": country, "year": year, "gdp": gdp, "internet": internet})
    return pd.DataFrame(rows)


# ──────────────────────────────────────────────────────────────────────────────
# OLS
# ──────────────────────────────────────────────────────────────────────────────

def test_ols_runs_and_returns_coefficients(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=False)
    assert len(result.coefficients) >= 2  # Intercept + x
    x_coef = next(c for c in result.coefficients if c["variable"] == "x")
    assert abs(x_coef["coefficient"] - 3.0) < 0.5  # Should be near 3


def test_ols_fit_stats(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=False)
    assert result.fit["r_squared"] is not None
    assert result.fit["r_squared"] > 0.9
    assert result.fit["n_obs"] == 50


def test_ols_residuals_and_fitted(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=False)
    assert len(result.residuals) == 50
    assert len(result.fitted_values) == 50
    assert len(result.actual_values) == 50


def test_robust_ols(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=True)
    assert "HC1" in result.model_metadata["cov_type"]
    x_coef = next(c for c in result.coefficients if c["variable"] == "x")
    assert x_coef["std_error"] > 0


def test_ols_with_controls(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=["z"], robust=False)
    var_names = [c["variable"] for c in result.coefficients]
    assert "x" in var_names
    assert "z" in var_names


def test_ols_too_few_obs_raises():
    df = pd.DataFrame({"y": [1.0, 2.0], "x": [1.0, 2.0]})
    with pytest.raises(ModelExecutionError, match="Too few observations"):
        run_ols(df, dep_var="y", primary_iv="x", controls=[], robust=False)


def test_ols_significance_markers(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=False)
    x_coef = next(c for c in result.coefficients if c["variable"] == "x")
    # x is a very significant predictor
    assert x_coef["significance"] in ("*", "**", "***")


def test_ols_aic_bic_present(cross_df):
    result = run_ols(cross_df, dep_var="y", primary_iv="x", controls=[], robust=False)
    assert result.fit["aic"] is not None
    assert result.fit["bic"] is not None


# ──────────────────────────────────────────────────────────────────────────────
# Panel models
# ──────────────────────────────────────────────────────────────────────────────

def test_pooled_ols(panel_df_large):
    result = run_panel(
        panel_df_large, dep_var="gdp", primary_iv="internet", controls=[],
        entity_col="country", time_col="year", model_type="pooled_ols",
    )
    assert result.model_metadata["n_entities"] == 5
    assert result.model_metadata["n_time_periods"] == 10
    assert len(result.coefficients) > 0


def test_fixed_effects(panel_df_large):
    result = run_panel(
        panel_df_large, dep_var="gdp", primary_iv="internet", controls=[],
        entity_col="country", time_col="year", model_type="fixed_effects",
    )
    assert result.model_metadata["entity_effects"] is True
    assert result.model_metadata["time_effects"] is False
    # Should have internet coefficient but NOT const (FE absorbs it)
    var_names = [c["variable"] for c in result.coefficients]
    assert "internet" in var_names


def test_random_effects(panel_df_large):
    result = run_panel(
        panel_df_large, dep_var="gdp", primary_iv="internet", controls=[],
        entity_col="country", time_col="year", model_type="random_effects",
    )
    assert result.model_metadata["entity_effects"] is False
    var_names = [c["variable"] for c in result.coefficients]
    assert "internet" in var_names


def test_two_way_fixed_effects(panel_df_large):
    result = run_panel(
        panel_df_large, dep_var="gdp", primary_iv="internet", controls=[],
        entity_col="country", time_col="year", model_type="two_way_fixed_effects",
    )
    assert result.model_metadata["entity_effects"] is True
    assert result.model_metadata["time_effects"] is True


def test_panel_too_few_entities_raises():
    df = pd.DataFrame({
        "country": ["A", "A"],
        "year": [2010, 2011],
        "y": [1.0, 2.0],
        "x": [3.0, 4.0],
    })
    with pytest.raises(ModelExecutionError, match="2 distinct entities"):
        run_panel(df, dep_var="y", primary_iv="x", controls=[], entity_col="country", time_col="year", model_type="fixed_effects")


def test_panel_clustered_se(panel_df_large):
    result = run_panel(
        panel_df_large, dep_var="gdp", primary_iv="internet", controls=[],
        entity_col="country", time_col="year", model_type="fixed_effects",
        cluster_by_entity=True,
    )
    assert "clustered" in result.model_metadata["cov_type"]


# ──────────────────────────────────────────────────────────────────────────────
# Diagnostics
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def ols_with_result(cross_df):
    return run_ols(cross_df, dep_var="y", primary_iv="x", controls=["z"], robust=False)


def test_breusch_pagan(cross_df, ols_with_result):
    exog = ols_with_result.sm_result.model.exog
    resid = np.array(ols_with_result.residuals)
    bp = compute_breusch_pagan(resid, exog)
    assert bp.available
    assert bp.statistic is not None
    assert bp.p_value is not None


def test_jarque_bera(cross_df, ols_with_result):
    resid = np.array(ols_with_result.residuals)
    jb = compute_jarque_bera(resid)
    assert jb.available
    assert jb.statistic is not None


def test_durbin_watson(cross_df, ols_with_result):
    resid = np.array(ols_with_result.residuals)
    dw = compute_durbin_watson(resid)
    assert dw.available
    assert dw.statistic is not None
    assert 0 <= dw.statistic <= 4


def test_vif_calculation(cross_df, ols_with_result):
    exog = ols_with_result.sm_result.model.exog
    var_names = list(ols_with_result.sm_result.model.exog_names)
    vif_results = compute_vif(exog, var_names)
    # Should exclude Intercept
    var_names_vif = [v.variable for v in vif_results]
    assert "Intercept" not in var_names_vif
    assert "x" in var_names_vif
    for v in vif_results:
        assert v.risk_level in ("low", "moderate", "severe", "unknown")


def test_descriptive_stats(cross_df):
    stats = compute_descriptive_stats(cross_df, ["y", "x"])
    assert len(stats) == 2
    y_stat = next(s for s in stats if s.variable == "y")
    assert y_stat.count == 50
    assert y_stat.mean is not None
    assert y_stat.median is not None
    assert y_stat.missing_count == 0


def test_correlation_matrix(cross_df):
    corr = compute_correlation_matrix(cross_df, ["y", "x", "z"])
    assert corr.variables == ["y", "x", "z"]
    assert len(corr.matrix) == 3
    assert len(corr.matrix[0]) == 3
    # Diagonal should be 1.0
    assert corr.matrix[0][0] == pytest.approx(1.0)
    assert corr.matrix[1][1] == pytest.approx(1.0)
