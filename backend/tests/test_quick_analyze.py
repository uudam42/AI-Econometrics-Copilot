"""Tests for the Quick Analyze workflow.

Covers:
- Upload → session created at 'uploaded'
- Plan → session advances to 'awaiting_confirmation' with recommendation
- Confirm → session advances to 'complete' with BeginnerSummary
- Error paths: missing variables, unknown session
- Summary generator rules via integration: significance, causal warning,
  diagnostics card statuses
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode()


def _cross_section_df(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n = 80
    edu = rng.normal(12, 3, n)
    income = 5000 + 800 * edu + rng.normal(0, 1000, n)
    age = rng.integers(22, 65, n).astype(float)
    return pd.DataFrame({"income": income, "education": edu, "age": age})


def _upload_and_plan(
    client: TestClient,
    df: pd.DataFrame,
    question: str,
) -> tuple[str, dict]:
    up = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("data.csv", _csv_bytes(df), "text/csv")},
        data={"research_question": question},
    )
    assert up.status_code == 200, up.text
    sid = up.json()["session_id"]
    plan = client.post(f"/api/quick-analyze/{sid}/plan")
    assert plan.status_code == 200, plan.text
    return sid, plan.json()["recommendation"]


# ---------------------------------------------------------------------------
# Stage 1 — upload
# ---------------------------------------------------------------------------

def test_upload_returns_session(client: TestClient):
    df = _cross_section_df()
    resp = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("data.csv", _csv_bytes(df), "text/csv")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stage"] == "uploaded"
    assert "session_id" in body
    assert body["n_rows"] == 80
    assert body["n_columns"] == 3


def test_upload_with_question(client: TestClient):
    df = _cross_section_df()
    resp = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("data.csv", _csv_bytes(df), "text/csv")},
        data={"research_question": "Does education affect income?"},
    )
    assert resp.status_code == 200
    assert resp.json()["stage"] == "uploaded"


def test_upload_invalid_extension_is_rejected(client: TestClient):
    resp = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code in (400, 415, 422, 500)


# ---------------------------------------------------------------------------
# Stage 2 — plan
# ---------------------------------------------------------------------------

def test_plan_produces_recommendation(client: TestClient):
    df = _cross_section_df()
    up = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("data.csv", _csv_bytes(df), "text/csv")},
        data={"research_question": "Does education affect income?"},
    )
    assert up.status_code == 200
    sid = up.json()["session_id"]

    resp = client.post(f"/api/quick-analyze/{sid}/plan")
    assert resp.status_code == 200
    body = resp.json()
    assert body["stage"] == "awaiting_confirmation"
    rec = body["recommendation"]
    assert "outcome_variable" in rec
    assert "recommended_model" in rec
    assert isinstance(rec["why_reasons"], list)


def test_plan_unknown_session_returns_error(client: TestClient):
    resp = client.post("/api/quick-analyze/nonexistent-id/plan")
    assert resp.status_code in (404, 422, 500)


# ---------------------------------------------------------------------------
# Stage 3 — confirm and run
# ---------------------------------------------------------------------------

def test_confirm_produces_summary(client: TestClient):
    df = _cross_section_df()
    sid, _ = _upload_and_plan(client, df, "Does education affect income?")

    body = {
        "dependent_variable": "income",
        "primary_independent_variable": "education",
        "control_variables": ["age"],
        "entity_column": None,
        "time_column": None,
        "model_type": "ols",
        "apply_log_transform_to": [],
        "analysis_intent": "association",
    }
    resp = client.post(f"/api/quick-analyze/{sid}/confirm", json=body)
    assert resp.status_code == 200, resp.text
    result = resp.json()
    assert result["stage"] == "complete"
    assert "analysis_id" in result

    summary = result["summary"]
    assert "headline" in summary
    assert "main_finding" in summary
    assert isinstance(summary["is_significant"], bool)
    assert "causal_warning" in summary
    assert "association" in summary["causal_warning"].lower()

    ds = summary["diagnostics_status"]
    assert ds["causal_interpretation"] == "Association only"
    assert ds["model_fit"] in ("Available", "Limited")
    assert ds["heteroskedasticity"] in (
        "Not detected",
        "Detected — robust standard errors recommended",
    )


def test_confirm_with_log_transform(client: TestClient):
    """Log transform on income (positive values) should not crash."""
    df = _cross_section_df()
    # ensure income is strictly positive
    df["income"] = df["income"].abs() + 1
    sid, _ = _upload_and_plan(client, df, "Does education affect income?")

    body = {
        "dependent_variable": "income",
        "primary_independent_variable": "education",
        "control_variables": [],
        "entity_column": None,
        "time_column": None,
        "model_type": "ols",
        "apply_log_transform_to": ["income"],
        "analysis_intent": "association",
    }
    resp = client.post(f"/api/quick-analyze/{sid}/confirm", json=body)
    assert resp.status_code == 200, resp.text


def test_confirm_missing_dependent_returns_error(client: TestClient):
    df = _cross_section_df()
    sid, _ = _upload_and_plan(client, df, "Does education affect income?")
    body = {
        "dependent_variable": "nonexistent_col",
        "primary_independent_variable": "education",
        "control_variables": [],
        "entity_column": None,
        "time_column": None,
        "model_type": "ols",
        "apply_log_transform_to": [],
        "analysis_intent": "association",
    }
    resp = client.post(f"/api/quick-analyze/{sid}/confirm", json=body)
    assert resp.status_code in (400, 422, 500)


# ---------------------------------------------------------------------------
# Session detail
# ---------------------------------------------------------------------------

def test_get_session_returns_detail(client: TestClient):
    df = _cross_section_df()
    sid, _ = _upload_and_plan(client, df, "Does education affect income?")
    resp = client.get(f"/api/quick-analyze/{sid}")
    assert resp.status_code == 200
    body = resp.json()
    assert "session" in body
    assert body["session"]["session_id"] == sid


def test_get_session_unknown_returns_error(client: TestClient):
    resp = client.get("/api/quick-analyze/no-such-id")
    assert resp.status_code in (404, 422, 500)


# ---------------------------------------------------------------------------
# Causal-warning rule — always present
# ---------------------------------------------------------------------------

def test_causal_warning_always_present(client: TestClient):
    df = _cross_section_df()
    sid, _ = _upload_and_plan(client, df, "Does education affect income?")

    body = {
        "dependent_variable": "income",
        "primary_independent_variable": "education",
        "control_variables": [],
        "entity_column": None,
        "time_column": None,
        "model_type": "ols",
        "apply_log_transform_to": [],
        "analysis_intent": "association",
    }
    resp = client.post(f"/api/quick-analyze/{sid}/confirm", json=body)
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert summary["causal_warning"]
    assert len(summary["causal_warning"]) > 10


# ---------------------------------------------------------------------------
# Exploratory (no research question)
# ---------------------------------------------------------------------------

def test_plan_exploratory_succeeds(client: TestClient):
    df = _cross_section_df()
    up = client.post(
        "/api/quick-analyze/upload",
        files={"file": ("data.csv", _csv_bytes(df), "text/csv")},
    )
    assert up.status_code == 200
    sid = up.json()["session_id"]
    resp = client.post(f"/api/quick-analyze/{sid}/plan")
    assert resp.status_code == 200
    assert resp.json()["stage"] == "awaiting_confirmation"
