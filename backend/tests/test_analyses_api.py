"""Integration tests for the analyses API endpoints."""
from __future__ import annotations

import io
import json

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _make_panel_csv() -> bytes:
    rng = np.random.default_rng(99)
    rows = []
    countries = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    for country in countries:
        base_internet = rng.uniform(5, 20)  # entity-specific base
        for year in range(2010, 2018):
            internet = base_internet + (year - 2010) * 2 + rng.normal(0, 0.5)
            rows.append({
                "country": country,
                "year": year,
                "gdp": 1000.0 + base_internet * 10 + (year - 2010) * 30 + rng.normal(0, 10),
                "internet": internet,
                "urbanization": 50.0 + (year - 2010) + rng.normal(0, 1),
            })
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue().encode()


def _make_cross_csv() -> bytes:
    rng = np.random.default_rng(7)
    n = 40
    x = rng.uniform(1, 10, n)
    y = 2.0 + 3.0 * x + rng.normal(0, 0.5, n)
    z = rng.uniform(0, 5, n)
    buf = io.StringIO()
    pd.DataFrame({"y": y, "x": x, "z": z}).to_csv(buf, index=False)
    return buf.getvalue().encode()


@pytest.fixture()
def panel_dataset_id(client):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("panel.csv", _make_panel_csv(), "text/csv")},
    )
    assert resp.status_code == 200
    return resp.json()["dataset_id"]


@pytest.fixture()
def cross_dataset_id(client):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("cross.csv", _make_cross_csv(), "text/csv")},
    )
    assert resp.status_code == 200
    return resp.json()["dataset_id"]


# ──────────────────────────────────────────────────────────────────────────────
# OLS
# ──────────────────────────────────────────────────────────────────────────────

def test_run_ols(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    resp = client.post("/api/analyses/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_id" in data
    assert data["model_type"] == "ols"
    assert len(data["coefficients"]) >= 2


def test_run_robust_ols(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": ["z"],
        },
        "transformations": [],
        "model_type": "robust_ols",
        "include_intercept": True,
        "robust_standard_errors": True,
        "cluster_standard_errors_by_entity": False,
    }
    resp = client.post("/api/analyses/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_type"] == "robust_ols"


def test_get_analysis_by_id(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    run_resp = client.post("/api/analyses/run", json=payload)
    analysis_id = run_resp.json()["analysis_id"]

    get_resp = client.get(f"/api/analyses/{analysis_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["analysis_id"] == analysis_id


def test_get_diagnostics(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": ["z"],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    analysis_id = client.post("/api/analyses/run", json=payload).json()["analysis_id"]
    diag_resp = client.get(f"/api/analyses/{analysis_id}/diagnostics")
    assert diag_resp.status_code == 200
    data = diag_resp.json()
    assert "vif" in data
    assert "breusch_pagan" in data
    assert "jarque_bera" in data
    assert "durbin_watson" in data
    assert "correlation_matrix" in data


def test_export_json(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    analysis_id = client.post("/api/analyses/run", json=payload).json()["analysis_id"]
    export_resp = client.get(f"/api/analyses/{analysis_id}/export/json")
    assert export_resp.status_code == 200
    data = export_resp.json()
    assert "software_versions" in data
    assert "pandas" in data["software_versions"]
    assert "disclaimer" in data


def test_analysis_not_found(client):
    resp = client.get("/api/analyses/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


def test_duplicate_variable_rejection(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "y",  # same as dep var!
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    resp = client.post("/api/analyses/run", json=payload)
    assert resp.status_code == 422


# ──────────────────────────────────────────────────────────────────────────────
# Panel models
# ──────────────────────────────────────────────────────────────────────────────

def _panel_payload(dataset_id, model_type, controls=None):
    return {
        "dataset_id": dataset_id,
        "variable_selection": {
            "dataset_id": dataset_id,
            "dependent_variable": "gdp",
            "primary_independent_variable": "internet",
            "control_variables": controls or [],
            "entity_column": "country",
            "time_column": "year",
        },
        "transformations": [],
        "model_type": model_type,
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }


def test_pooled_ols_api(client, panel_dataset_id):
    resp = client.post("/api/analyses/run", json=_panel_payload(panel_dataset_id, "pooled_ols"))
    assert resp.status_code == 200
    assert resp.json()["model_type"] == "pooled_ols"


def test_fixed_effects_api(client, panel_dataset_id):
    resp = client.post("/api/analyses/run", json=_panel_payload(panel_dataset_id, "fixed_effects"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_metadata"]["entity_effects"] is True


def test_random_effects_api(client, panel_dataset_id):
    resp = client.post("/api/analyses/run", json=_panel_payload(panel_dataset_id, "random_effects"))
    assert resp.status_code == 200


def test_two_way_fixed_effects_api(client, panel_dataset_id):
    resp = client.post("/api/analyses/run", json=_panel_payload(panel_dataset_id, "two_way_fixed_effects"))
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_metadata"]["time_effects"] is True


def test_fixed_effects_with_hausman_diagnostic(client, panel_dataset_id):
    payload = _panel_payload(panel_dataset_id, "fixed_effects")
    analysis_id = client.post("/api/analyses/run", json=payload).json()["analysis_id"]
    diag = client.get(f"/api/analyses/{analysis_id}/diagnostics").json()
    hausman = diag["hausman"]
    # Hausman test should have been attempted
    assert "available" in hausman


# ──────────────────────────────────────────────────────────────────────────────
# Transformations in analysis run
# ──────────────────────────────────────────────────────────────────────────────

def test_run_with_log_transform(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "log_y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [
            {"operation": "log_transform", "columns": ["y"], "parameters": {}},
        ],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    resp = client.post("/api/analyses/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transformation_log"]) == 1
    assert data["transformation_log"][0]["operation"] == "log_transform"


def test_analysis_includes_disclaimer(client, cross_dataset_id):
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    resp = client.post("/api/analyses/run", json=payload)
    data = resp.json()
    assert "disclaimer" in data
    assert len(data["disclaimer"]) > 10


def test_analysis_artifact_creation(client, cross_dataset_id):
    """Verify that analysis_id is stable and retrievable from both result and diagnostics."""
    payload = {
        "dataset_id": cross_dataset_id,
        "variable_selection": {
            "dataset_id": cross_dataset_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }
    analysis_id = client.post("/api/analyses/run", json=payload).json()["analysis_id"]
    assert client.get(f"/api/analyses/{analysis_id}").status_code == 200
    assert client.get(f"/api/analyses/{analysis_id}/diagnostics").status_code == 200
    assert client.get(f"/api/analyses/{analysis_id}/export/json").status_code == 200
