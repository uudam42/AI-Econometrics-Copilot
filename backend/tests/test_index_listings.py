"""Integration tests for the global index list endpoints (GET /api/datasets,
GET /api/analyses, GET /api/reports) that back the frontend index pages."""
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


def _make_cross_csv() -> bytes:
    rng = np.random.default_rng(11)
    n = 40
    x = rng.uniform(1, 10, n)
    y = 2.0 + 3.0 * x + rng.normal(0, 0.5, n)
    z = rng.uniform(0, 5, n)
    buf = io.StringIO()
    pd.DataFrame({"y": y, "x": x, "z": z}).to_csv(buf, index=False)
    return buf.getvalue().encode()


@pytest.fixture()
def dataset_id(client):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("cross.csv", _make_cross_csv(), "text/csv")},
    )
    assert resp.status_code == 200
    return resp.json()["dataset_id"]


def _run_analysis(client, dataset_id: str) -> str:
    payload = {
        "dataset_id": dataset_id,
        "variable_selection": {
            "dataset_id": dataset_id,
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
    return resp.json()["analysis_id"]


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/datasets
# ──────────────────────────────────────────────────────────────────────────────

def test_list_datasets_empty(client):
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_datasets_returns_uploaded(client, dataset_id):
    resp = client.get("/api/datasets")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["dataset_id"] == dataset_id
    assert item["filename"] == "cross.csv"
    assert item["n_rows"] == 40
    assert item["n_columns"] == 3
    assert item["uploaded_at"] is not None


def test_list_datasets_newest_first(client):
    ids = []
    for name in ["a.csv", "b.csv"]:
        resp = client.post(
            "/api/datasets/upload",
            files={"file": (name, _make_cross_csv(), "text/csv")},
        )
        assert resp.status_code == 200
        ids.append(resp.json()["dataset_id"])

    resp = client.get("/api/datasets")
    items = resp.json()
    assert len(items) == 2
    returned_ids = [i["dataset_id"] for i in items]
    assert set(returned_ids) == set(ids)


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/analyses
# ──────────────────────────────────────────────────────────────────────────────

def test_list_analyses_empty(client):
    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_analyses_returns_run(client, dataset_id):
    analysis_id = _run_analysis(client, dataset_id)

    resp = client.get("/api/analyses")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["analysis_id"] == analysis_id
    assert item["dataset_id"] == dataset_id
    assert item["model_type"] == "ols"
    assert item["dependent_variable"] == "y"
    assert item["r_squared"] is not None
    assert item["created_at"] is not None


# ──────────────────────────────────────────────────────────────────────────────
# GET /api/reports
# ──────────────────────────────────────────────────────────────────────────────

def test_list_reports_empty(client):
    resp = client.get("/api/reports")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_reports_returns_generated(client, dataset_id):
    analysis_id = _run_analysis(client, dataset_id)

    gen = client.post(
        "/api/reports/generate",
        json={"source_type": "analysis", "source_id": analysis_id},
    )
    assert gen.status_code == 200
    report_id = gen.json()["report_id"]

    resp = client.get("/api/reports")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["report_id"] == report_id
    assert item["source_type"] == "analysis"
    assert item["source_id"] == analysis_id
    assert item["title"]
    assert item["created_at"] is not None
