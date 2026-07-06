"""Tests for onboarding and demo project endpoints."""
from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLE_XLSX = PROJECT_ROOT / "sample_data" / "world_bank_panel_sample.xlsx"


class TestOnboardingStatus:
    def test_status_returns_ok(self, client):
        resp = client.get("/api/onboarding/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "has_projects" in data
        assert "has_demo" in data
        assert "sample_data_available" in data

    def test_status_reflects_new_project(self, client):
        client.post("/api/projects", json={
            "title": "Test Project",
            "description": "Not a demo",
        })
        resp = client.get("/api/onboarding/status")
        data = resp.json()
        assert data["has_projects"] is True

    def test_status_detects_demo_tag(self, client):
        client.post("/api/projects", json={
            "title": "Demo",
            "tags": ["demo"],
        })
        resp = client.get("/api/onboarding/status")
        data = resp.json()
        assert data["has_demo"] is True


class TestDemoProject:
    def test_create_demo_project(self, client, tmp_path):
        sample_dir = tmp_path / "sample_data"
        sample_dir.mkdir()
        src = SAMPLE_XLSX
        if src.exists():
            shutil.copy(src, sample_dir / "world_bank_panel_sample.xlsx")
            sample_path = sample_dir / "world_bank_panel_sample.xlsx"
        else:
            pytest.skip("Sample dataset not available in test environment")

        with patch("app.api.onboarding.SAMPLE_DATA_LOCATIONS", [sample_path]):
            resp = client.post("/api/onboarding/demo-project")

        assert resp.status_code == 200
        data = resp.json()
        assert "project_id" in data
        assert "dataset_id" in data
        assert data["title"] == "Demo: World Bank Panel Analysis"
        assert "Demo project created" in data["message"]

        proj_resp = client.get(f"/api/projects/{data['project_id']}")
        assert proj_resp.status_code == 200
        proj = proj_resp.json()
        assert proj["default_dataset_id"] == data["dataset_id"]
        assert "demo" in proj["tags"]

    def test_create_demo_no_sample_data(self, client):
        with patch("app.api.onboarding.SAMPLE_DATA_LOCATIONS", [Path("/nonexistent/file.xlsx")]):
            resp = client.post("/api/onboarding/demo-project")
        assert resp.status_code == 404
        assert "Sample dataset not found" in resp.json()["detail"]

    def test_demo_project_has_dataset(self, client, tmp_path):
        sample_dir = tmp_path / "sample_data"
        sample_dir.mkdir()
        src = SAMPLE_XLSX
        if not src.exists():
            pytest.skip("Sample dataset not available in test environment")
        shutil.copy(src, sample_dir / "world_bank_panel_sample.xlsx")

        with patch("app.api.onboarding.SAMPLE_DATA_LOCATIONS", [sample_dir / "world_bank_panel_sample.xlsx"]):
            resp = client.post("/api/onboarding/demo-project")

        data = resp.json()
        ds_resp = client.get(f"/api/datasets/{data['dataset_id']}")
        assert ds_resp.status_code == 200
        ds = ds_resp.json()
        assert ds["n_rows"] > 0
        assert ds["n_columns"] > 0

    def test_demo_updates_onboarding_status(self, client, tmp_path):
        sample_dir = tmp_path / "sample_data"
        sample_dir.mkdir()
        src = SAMPLE_XLSX
        if not src.exists():
            pytest.skip("Sample dataset not available in test environment")
        shutil.copy(src, sample_dir / "world_bank_panel_sample.xlsx")

        with patch("app.api.onboarding.SAMPLE_DATA_LOCATIONS", [sample_dir / "world_bank_panel_sample.xlsx"]):
            client.post("/api/onboarding/demo-project")

        status = client.get("/api/onboarding/status").json()
        assert status["has_projects"] is True
        assert status["has_demo"] is True
