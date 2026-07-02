"""Tests for multi-model comparison engine and model selection service."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_panel_csv() -> bytes:
    rng = np.random.default_rng(42)
    rows = []
    countries = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]
    for country in countries:
        base = rng.uniform(5, 25)
        for year in range(2010, 2018):
            rows.append({
                "country": country,
                "year": year,
                "gdp": 500.0 + base * 15 + (year - 2010) * 20 + rng.normal(0, 8),
                "internet": base + (year - 2010) * 1.5 + rng.normal(0, 0.8),
                "urban": 55.0 + (year - 2010) * 0.5 + rng.normal(0, 1.5),
            })
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue().encode()


def _make_cross_csv() -> bytes:
    rng = np.random.default_rng(7)
    n = 60
    x = rng.uniform(1, 10, n)
    z = rng.uniform(0, 5, n)
    y = 2.0 + 3.0 * x + 0.5 * z + rng.normal(0, 0.8, n)
    buf = io.StringIO()
    pd.DataFrame({"y": y, "x": x, "z": z}).to_csv(buf, index=False)
    return buf.getvalue().encode()


@pytest.fixture()
def panel_id(client):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("panel.csv", _make_panel_csv(), "text/csv")},
    )
    assert resp.status_code == 200
    return resp.json()["dataset_id"]


@pytest.fixture()
def cross_id(client):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("cross.csv", _make_cross_csv(), "text/csv")},
    )
    assert resp.status_code == 200
    return resp.json()["dataset_id"]


def _var_sel(dataset_id, dep="gdp", iv="internet", controls=None, entity="country", time="year"):
    return {
        "dataset_id": dataset_id,
        "dependent_variable": dep,
        "primary_independent_variable": iv,
        "control_variables": controls or [],
        "entity_column": entity,
        "time_column": time,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Compatible model selection rules
# ──────────────────────────────────────────────────────────────────────────────

def test_cross_section_only_offers_ols_models(client, cross_id):
    """Panel models must be unavailable when no entity/time columns are set."""
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols", "fixed_effects", "random_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    statuses = {m["model_type"]: m["status"] for m in data["models"]}
    assert statuses["ols"] == "completed"
    assert statuses["robust_ols"] == "completed"
    assert statuses["fixed_effects"] == "unavailable"
    assert statuses["random_effects"] == "unavailable"


def test_panel_data_offers_all_models(client, panel_id):
    """All six models must attempt to run on valid panel data."""
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["ols", "robust_ols", "pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    model_types = {m["model_type"] for m in data["models"]}
    assert "ols" in model_types
    assert "fixed_effects" in model_types
    assert "random_effects" in model_types


# ──────────────────────────────────────────────────────────────────────────────
# Comparison execution — multiple models
# ──────────────────────────────────────────────────────────────────────────────

def test_comparison_basic_structure(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": ["z"],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "comparison_id" in data
    assert "models" in data
    assert "recommendation" in data
    assert "coefficient_stability" in data
    assert "disclaimer" in data
    assert len(data["models"]) == 2


def test_all_completed_models_have_fit_metrics(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    for m in data["models"]:
        if m["status"] == "completed":
            assert m["fit_metrics"] is not None
            assert m["fit_metrics"]["n_obs"] is not None
            assert m["fit_metrics"]["r_squared"] is not None


def test_panel_comparison_completed(client, panel_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["pooled_ols", "fixed_effects", "random_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    completed = [m for m in data["models"] if m["status"] == "completed"]
    assert len(completed) >= 2


def test_panel_comparison_has_entity_and_time_period_counts(client, panel_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["fixed_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    fe = next(m for m in data["models"] if m["model_type"] == "fixed_effects")
    if fe["status"] == "completed":
        fm = fe["fit_metrics"]
        assert fm["n_entities"] is not None
        assert fm["n_time_periods"] is not None


def test_comparison_preserves_unavailable_reason(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "pooled_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    pooled = next(m for m in data["models"] if m["model_type"] == "pooled_ols")
    assert pooled["status"] == "unavailable"
    assert pooled["reason"] is not None
    assert len(pooled["reason"]) > 0


# ──────────────────────────────────────────────────────────────────────────────
# Coefficient stability
# ──────────────────────────────────────────────────────────────────────────────

def test_coefficient_stability_populated(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    stability = data["coefficient_stability"]
    assert len(stability) == 2
    for entry in stability:
        assert entry["coefficient"] is not None
        assert entry["direction"] in ("positive", "negative", "zero", "unavailable")
        assert "significance" in entry


def test_coefficient_stability_direction_matches_sign(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    entry = data["coefficient_stability"][0]
    coeff = entry["coefficient"]
    if coeff is not None and coeff > 1e-10:
        assert entry["direction"] == "positive"
    elif coeff is not None and coeff < -1e-10:
        assert entry["direction"] == "negative"


# ──────────────────────────────────────────────────────────────────────────────
# Model selection recommendation
# ──────────────────────────────────────────────────────────────────────────────

def test_recommendation_present_with_score(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    rec = data["recommendation"]
    assert rec["recommended_model"] in ("ols", "robust_ols")
    assert 0 <= rec["score"] <= 100
    assert rec["confidence"] in ("high", "medium", "low")
    assert len(rec["reasons"]) > 0
    assert len(rec["score_breakdown"]) > 0


def test_recommendation_score_breakdown_criteria(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    criteria = {c["criterion"] for c in data["recommendation"]["score_breakdown"]}
    assert "Structural Compatibility" in criteria
    assert "Model Fit" in criteria
    assert "Sample Size Adequacy" in criteria


def test_panel_recommendation_prefers_panel_model(client, panel_id):
    """With panel data, the recommendation should prefer a panel model over plain OLS."""
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["ols", "fixed_effects", "random_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    rec = data["recommendation"]
    assert rec["recommended_model"] != "ols", (
        "With valid panel data, the recommendation should prefer a panel model."
    )


def test_causal_warning_in_recommendation(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols"],
        "cluster_standard_errors_by_entity": False,
    })
    data = resp.json()
    all_warnings = " ".join(data["recommendation"]["warnings"]).lower()
    assert "causal" in all_warnings or "association" in all_warnings


# ──────────────────────────────────────────────────────────────────────────────
# GET and export endpoints
# ──────────────────────────────────────────────────────────────────────────────

def test_get_comparison_by_id(client, cross_id):
    post_resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols"],
        "cluster_standard_errors_by_entity": False,
    })
    cid = post_resp.json()["comparison_id"]
    get_resp = client.get(f"/api/comparisons/{cid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["comparison_id"] == cid


def test_comparison_not_found_returns_404(client):
    resp = client.get("/api/comparisons/nonexistent-id")
    assert resp.status_code == 404


def test_export_json_structure(client, cross_id):
    post_resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols", "robust_ols"],
        "cluster_standard_errors_by_entity": False,
    })
    cid = post_resp.json()["comparison_id"]
    export = client.get(f"/api/comparisons/{cid}/export/json").json()
    assert "comparison_id" in export
    assert "model_results" in export
    assert "recommendation" in export
    assert "software_versions" in export
    assert "pandas" in export["software_versions"]
    assert "disclaimer" in export


def test_clustered_se_comparison(client, panel_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["fixed_effects"],
        "cluster_standard_errors_by_entity": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    fe = next(m for m in data["models"] if m["model_type"] == "fixed_effects")
    if fe["status"] == "completed":
        assert "clustered" in (fe["standard_error_type"] or "").lower()


def test_two_way_fe_comparison(client, panel_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": panel_id,
        "variable_selection": _var_sel(panel_id),
        "candidate_models": ["two_way_fixed_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 200
    twfe = next(m for m in resp.json()["models"] if m["model_type"] == "two_way_fixed_effects")
    assert twfe["status"] in ("completed", "failed")


def test_duplicate_variable_returns_422(client, cross_id):
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": cross_id,
        "variable_selection": {
            "dataset_id": cross_id,
            "dependent_variable": "y",
            "primary_independent_variable": "y",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "candidate_models": ["ols"],
        "cluster_standard_errors_by_entity": False,
    })
    assert resp.status_code == 422
