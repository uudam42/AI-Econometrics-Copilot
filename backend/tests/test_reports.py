"""Tests for research report generation and export."""
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
    n = 50
    x = rng.uniform(1, 15, n)
    z = rng.uniform(0, 5, n)
    y = 3.0 + 2.5 * x + 0.8 * z + rng.normal(0, 1.0, n)
    buf = io.StringIO()
    pd.DataFrame({"y": y, "x": x, "z": z}).to_csv(buf, index=False)
    return buf.getvalue().encode()


def _make_panel_csv() -> bytes:
    rng = np.random.default_rng(55)
    rows = []
    countries = ["A", "B", "C", "D", "E"]
    for country in countries:
        base = rng.uniform(8, 20)
        for year in range(2012, 2020):
            rows.append({
                "country": country,
                "year": year,
                "gdp": 800 + base * 10 + (year - 2012) * 15 + rng.normal(0, 5),
                "internet": base + (year - 2012) * 1.2 + rng.normal(0, 0.5),
                "urban": 60 + (year - 2012) * 0.3 + rng.normal(0, 1),
            })
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue().encode()


@pytest.fixture()
def cross_analysis_id(client):
    ds_id = client.post(
        "/api/datasets/upload",
        files={"file": ("cross.csv", _make_cross_csv(), "text/csv")},
    ).json()["dataset_id"]
    resp = client.post("/api/analyses/run", json={
        "dataset_id": ds_id,
        "variable_selection": {
            "dataset_id": ds_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": ["z"],
            "entity_column": None,
            "time_column": None,
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    })
    return resp.json()["analysis_id"]


@pytest.fixture()
def comparison_id(client):
    ds_id = client.post(
        "/api/datasets/upload",
        files={"file": ("panel.csv", _make_panel_csv(), "text/csv")},
    ).json()["dataset_id"]
    resp = client.post("/api/comparisons/run", json={
        "dataset_id": ds_id,
        "variable_selection": {
            "dataset_id": ds_id,
            "dependent_variable": "gdp",
            "primary_independent_variable": "internet",
            "control_variables": ["urban"],
            "entity_column": "country",
            "time_column": "year",
        },
        "candidate_models": ["ols", "fixed_effects", "random_effects"],
        "cluster_standard_errors_by_entity": False,
    })
    return resp.json()["comparison_id"]


# ──────────────────────────────────────────────────────────────────────────────
# Report generation from analysis
# ──────────────────────────────────────────────────────────────────────────────

def test_generate_report_from_analysis(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "title": "Test Report",
        "research_question": "Is x associated with y?",
        "significance_level": 0.05,
        "include_appendix": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "report_id" in data
    assert data["source_type"] == "analysis"
    assert data["source_id"] == cross_analysis_id
    assert data["title"] == "Test Report"
    assert data["research_question"] == "Is x associated with y?"


def test_report_contains_markdown(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    data = resp.json()
    md = data["markdown_content"]
    assert len(md) > 200
    assert "# " in md
    assert "## " in md


def test_report_contains_html(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    data = resp.json()
    html = data["html_content"]
    assert "<html" in html
    assert "<table" in html
    assert "<h1" in html


def test_report_has_causal_warning(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"].lower()
    assert "causal" in md


def test_report_no_causal_language(client, cross_analysis_id):
    """The report must not use forbidden causal claims in coefficient interpretations."""
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"].lower()
    # These are direct causal claim phrases (not meta-discussion about causal language)
    for forbidden in ("proves causality", "establishes a causal effect", "guarantees a causal"):
        assert forbidden not in md, f"Forbidden causal claim '{forbidden}' found in report."
    # The word "causes" may appear in the disclaimer section itself (quoted as an example
    # of language we don't use) — that is intentional and acceptable.


def test_report_uses_association_language(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"].lower()
    assert "associated with" in md or "association" in md


def test_non_significant_coefficient_wording(client):
    """A coefficient with p > sig_level must say 'not statistically distinguishable'."""
    rng = np.random.default_rng(99)
    n = 30
    # Create data where relationship is very weak
    x = rng.uniform(0, 1, n)
    y = rng.normal(0, 10, n)  # y is essentially noise, not related to x
    buf = io.StringIO()
    pd.DataFrame({"y": y, "x": x}).to_csv(buf, index=False)
    ds_id = TestClient(app).post(
        "/api/datasets/upload",
        files={"file": ("weak.csv", buf.getvalue().encode(), "text/csv")},
    ).json()["dataset_id"]
    analysis_id = TestClient(app).post("/api/analyses/run", json={
        "dataset_id": ds_id,
        "variable_selection": {
            "dataset_id": ds_id,
            "dependent_variable": "y",
            "primary_independent_variable": "x",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }).json()["analysis_id"]
    resp = TestClient(app).post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"].lower()
    assert "not statistically distinguishable" in md or "not statistically significant" in md.lower()


def test_log_dep_var_interpretation(client):
    """When the dep variable starts with 'log_', interpretation uses percent change."""
    rng = np.random.default_rng(7)
    n = 50
    x = rng.uniform(1, 10, n)
    log_y = 2.0 + 0.5 * x + rng.normal(0, 0.3, n)
    buf = io.StringIO()
    pd.DataFrame({"log_gdp": log_y, "internet": x}).to_csv(buf, index=False)
    ds_id = TestClient(app).post(
        "/api/datasets/upload",
        files={"file": ("logdep.csv", buf.getvalue().encode(), "text/csv")},
    ).json()["dataset_id"]
    an = TestClient(app).post("/api/analyses/run", json={
        "dataset_id": ds_id,
        "variable_selection": {
            "dataset_id": ds_id,
            "dependent_variable": "log_gdp",
            "primary_independent_variable": "internet",
            "control_variables": [],
            "entity_column": None,
            "time_column": None,
        },
        "transformations": [],
        "model_type": "ols",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }).json()["analysis_id"]
    resp = TestClient(app).post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": an,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"].lower()
    assert "%" in md or "percent" in md


def test_appendix_included_when_requested(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": True,
    })
    data = resp.json()
    assert "Appendix" in data["sections_included"]
    assert "Appendix" in data["markdown_content"]


def test_appendix_excluded_when_not_requested(client, cross_analysis_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    data = resp.json()
    assert "Appendix" not in data["sections_included"]


# ──────────────────────────────────────────────────────────────────────────────
# Report generation from comparison
# ──────────────────────────────────────────────────────────────────────────────

def test_generate_report_from_comparison(client, comparison_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "comparison",
        "source_id": comparison_id,
        "title": "Panel Comparison Report",
        "research_question": "Is internet penetration associated with GDP?",
        "significance_level": 0.05,
        "include_appendix": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["source_type"] == "comparison"
    assert data["source_id"] == comparison_id
    assert "Model Comparison" in data["title"] or "Panel Comparison" in data["title"]


def test_comparison_report_contains_stability_section(client, comparison_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "comparison",
        "source_id": comparison_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"]
    assert "Coefficient Stability" in md


def test_comparison_report_has_recommendation_section(client, comparison_id):
    resp = client.post("/api/reports/generate", json={
        "source_type": "comparison",
        "source_id": comparison_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    md = resp.json()["markdown_content"]
    assert "Model Recommendation" in md or "Recommendation" in md


# ──────────────────────────────────────────────────────────────────────────────
# Report retrieval and export
# ──────────────────────────────────────────────────────────────────────────────

def test_get_report_by_id(client, cross_analysis_id):
    post_resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    rid = post_resp.json()["report_id"]
    get_resp = client.get(f"/api/reports/{rid}")
    assert get_resp.status_code == 200
    assert get_resp.json()["report_id"] == rid


def test_report_not_found_returns_404(client):
    resp = client.get("/api/reports/nonexistent-report-id")
    assert resp.status_code == 404


def test_markdown_export_returns_plain_text(client, cross_analysis_id):
    post_resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    rid = post_resp.json()["report_id"]
    md_resp = client.get(f"/api/reports/{rid}/markdown")
    assert md_resp.status_code == 200
    assert "text/markdown" in md_resp.headers.get("content-type", "")
    assert "# " in md_resp.text


def test_html_export_returns_html(client, cross_analysis_id):
    post_resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    rid = post_resp.json()["report_id"]
    html_resp = client.get(f"/api/reports/{rid}/html")
    assert html_resp.status_code == 200
    assert "<html" in html_resp.text


def test_json_export_complete_artifact(client, cross_analysis_id):
    post_resp = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    rid = post_resp.json()["report_id"]
    json_resp = client.get(f"/api/reports/{rid}/export/json").json()
    assert "report_id" in json_resp
    assert "markdown_content" in json_resp
    assert "html_content" in json_resp
    assert "disclaimer" in json_resp
    assert "writing_rules_version" in json_resp


def test_artifact_persistence(client, cross_analysis_id):
    """The same report_id should always return the same content."""
    post = client.post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": cross_analysis_id,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    rid = post.json()["report_id"]
    first = client.get(f"/api/reports/{rid}").json()
    second = client.get(f"/api/reports/{rid}").json()
    assert first["markdown_content"] == second["markdown_content"]


def test_unavailable_diagnostic_handled_gracefully(client):
    """Report must gracefully handle diagnostics that are not available."""
    rng = np.random.default_rng(33)
    rows = []
    for country in ["C1", "C2", "C3"]:
        base = rng.uniform(5, 15)
        for year in range(2015, 2021):
            rows.append({
                "country": country,
                "year": year,
                "gdp": 500 + base * 10 + rng.normal(0, 5),
                "internet": base + rng.normal(0, 0.5),
            })
    buf = io.StringIO()
    pd.DataFrame(rows).to_csv(buf, index=False)
    ds_id = TestClient(app).post(
        "/api/datasets/upload",
        files={"file": ("panel2.csv", buf.getvalue().encode(), "text/csv")},
    ).json()["dataset_id"]
    an = TestClient(app).post("/api/analyses/run", json={
        "dataset_id": ds_id,
        "variable_selection": {
            "dataset_id": ds_id,
            "dependent_variable": "gdp",
            "primary_independent_variable": "internet",
            "control_variables": [],
            "entity_column": "country",
            "time_column": "year",
        },
        "transformations": [],
        "model_type": "fixed_effects",
        "include_intercept": True,
        "robust_standard_errors": False,
        "cluster_standard_errors_by_entity": False,
    }).json()["analysis_id"]
    # Report must not fail even when BP test is unavailable for panel
    resp = TestClient(app).post("/api/reports/generate", json={
        "source_type": "analysis",
        "source_id": an,
        "significance_level": 0.05,
        "include_appendix": False,
    })
    assert resp.status_code == 200
    assert len(resp.json()["markdown_content"]) > 100
