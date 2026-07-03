"""Tests for persistent project workspaces, restart recovery, and bundle export."""
from __future__ import annotations

import io
import json
import zipfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from tests.conftest import df_to_csv_bytes


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

class TestProjectCRUD:
    def test_create_project(self, client: TestClient):
        resp = client.post("/api/projects", json={
            "title": "GDP Study",
            "description": "Test project",
            "research_question": "Does trade affect GDP?",
            "tags": ["macro", "trade"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "GDP Study"
        assert data["status"] == "draft"
        assert data["tags"] == ["macro", "trade"]
        assert data["project_id"]

    def test_list_projects(self, client: TestClient):
        client.post("/api/projects", json={"title": "P1"})
        client.post("/api/projects", json={"title": "P2"})
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_project(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Fetch Me"})
        pid = create.json()["project_id"]
        resp = client.get(f"/api/projects/{pid}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Fetch Me"

    def test_get_project_not_found(self, client: TestClient):
        resp = client.get("/api/projects/nonexistent")
        assert resp.status_code == 404

    def test_update_project(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Original"})
        pid = create.json()["project_id"]
        resp = client.patch(f"/api/projects/{pid}", json={
            "title": "Updated",
            "status": "active",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated"
        assert resp.json()["status"] == "active"

    def test_archive_project(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "To Archive"})
        pid = create.json()["project_id"]
        resp = client.patch(f"/api/projects/{pid}", json={"status": "archived"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "archived"

    def test_archived_excluded_by_default(self, client: TestClient):
        c1 = client.post("/api/projects", json={"title": "Active"}).json()
        c2 = client.post("/api/projects", json={"title": "Archived"}).json()
        client.patch(f"/api/projects/{c2['project_id']}", json={"status": "archived"})
        resp = client.get("/api/projects")
        ids = [p["project_id"] for p in resp.json()]
        assert c1["project_id"] in ids
        assert c2["project_id"] not in ids

    def test_archived_included_when_requested(self, client: TestClient):
        c2 = client.post("/api/projects", json={"title": "Archived2"}).json()
        client.patch(f"/api/projects/{c2['project_id']}", json={"status": "archived"})
        resp = client.get("/api/projects?include_archived=true")
        ids = [p["project_id"] for p in resp.json()]
        assert c2["project_id"] in ids


# ---------------------------------------------------------------------------
# Project deletion
# ---------------------------------------------------------------------------

class TestProjectDeletion:
    def test_delete_empty_project(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Empty"})
        pid = create.json()["project_id"]
        resp = client.delete(f"/api/projects/{pid}")
        assert resp.status_code == 200
        assert client.get(f"/api/projects/{pid}").status_code == 404

    def test_delete_with_artifacts_rejected(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Has Data"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        csv_bytes = df_to_csv_bytes(df)
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        resp = client.delete(f"/api/projects/{pid}")
        assert resp.status_code == 409

    def test_force_delete_with_artifacts(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Force Delete"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        csv_bytes = df_to_csv_bytes(df)
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        resp = client.delete(f"/api/projects/{pid}?force=true")
        assert resp.status_code == 200
        assert client.get(f"/api/projects/{pid}").status_code == 404


# ---------------------------------------------------------------------------
# Project-aware dataset upload
# ---------------------------------------------------------------------------

class TestProjectDatasets:
    def test_upload_to_project(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "With Data"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        csv_bytes = df_to_csv_bytes(df)
        resp = client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("sample.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "sample.csv"
        assert data["n_rows"] == 3

    def test_upload_to_nonexistent_project_fails(self, client: TestClient):
        df = pd.DataFrame({"a": [1]})
        resp = client.post(
            "/api/projects/nonexistent/datasets/upload",
            files={"file": ("x.csv", df_to_csv_bytes(df), "text/csv")},
        )
        assert resp.status_code == 404

    def test_dataset_in_artifacts(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Artifacts"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [10, 20], "y": [30, 40]})
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("data.csv", df_to_csv_bytes(df), "text/csv")},
        )
        resp = client.get(f"/api/projects/{pid}/artifacts")
        assert resp.status_code == 200
        assert len(resp.json()["datasets"]) == 1


# ---------------------------------------------------------------------------
# Persistence across restart simulation
# ---------------------------------------------------------------------------

class TestRestartRecovery:
    def test_dataset_survives_cache_clear(self, client: TestClient):
        df = pd.DataFrame({"col_a": [1, 2, 3], "col_b": [4, 5, 6]})
        csv_bytes = df_to_csv_bytes(df)
        resp = client.post(
            "/api/datasets/upload",
            files={"file": ("persist.csv", csv_bytes, "text/csv")},
        )
        dataset_id = resp.json()["dataset_id"]

        from app.storage.repositories import dataset_repository
        dataset_repository.clear_cache()

        resp2 = client.get(f"/api/datasets/{dataset_id}/overview")
        assert resp2.status_code == 200
        assert resp2.json()["n_rows"] == 3

    def test_analysis_survives_cache_clear(self, client: TestClient):
        df = pd.DataFrame({
            "gdp": range(50, 100),
            "trade": range(100, 150),
        })
        upload = client.post(
            "/api/datasets/upload",
            files={"file": ("analysis_test.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]

        run_resp = client.post("/api/analyses/run", json={
            "dataset_id": did,
            "variable_selection": {
                "dataset_id": did,
                "dependent_variable": "gdp",
                "primary_independent_variable": "trade",
                "control_variables": [],
            },
            "model_type": "ols",
            "transformations": [],
        })
        assert run_resp.status_code == 200
        aid = run_resp.json()["analysis_id"]

        from app.storage.repositories import analysis_repository
        analysis_repository._cache.clear()

        resp2 = client.get(f"/api/analyses/{aid}")
        assert resp2.status_code == 200
        assert resp2.json()["analysis_id"] == aid

    def test_plan_survives_cache_clear(self, client: TestClient):
        df = pd.DataFrame({
            "country": ["A"] * 10 + ["B"] * 10,
            "year": list(range(2000, 2010)) * 2,
            "gdp_per_capita": range(20),
            "internet_users": range(20, 40),
        })
        upload = client.post(
            "/api/datasets/upload",
            files={"file": ("plan_test.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]

        plan_resp = client.post("/api/plans/generate", json={
            "dataset_id": did,
            "research_question": "Does internet usage affect GDP?",
        })
        assert plan_resp.status_code == 200
        plan_id = plan_resp.json()["plan_id"]

        from app.storage.repositories import plan_repository
        plan_repository._cache.clear()

        resp2 = client.get(f"/api/plans/{plan_id}")
        assert resp2.status_code == 200
        assert resp2.json()["plan_id"] == plan_id

    def test_comparison_survives_cache_clear(self, client: TestClient):
        df = pd.DataFrame({
            "gdp": range(50, 100),
            "trade": range(100, 150),
        })
        upload = client.post(
            "/api/datasets/upload",
            files={"file": ("comp_test.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]

        comp_resp = client.post("/api/comparisons/run", json={
            "dataset_id": did,
            "variable_selection": {
                "dataset_id": did,
                "dependent_variable": "gdp",
                "primary_independent_variable": "trade",
                "control_variables": [],
            },
            "candidate_models": ["ols", "robust_ols"],
            "transformations": [],
        })
        assert comp_resp.status_code == 200
        cid = comp_resp.json()["comparison_id"]

        from app.storage.repositories import comparison_repository
        comparison_repository._cache.clear()

        resp2 = client.get(f"/api/comparisons/{cid}")
        assert resp2.status_code == 200
        assert resp2.json()["comparison_id"] == cid

    def test_report_survives_cache_clear(self, client: TestClient):
        df = pd.DataFrame({
            "gdp": range(50, 100),
            "trade": range(100, 150),
        })
        upload = client.post(
            "/api/datasets/upload",
            files={"file": ("report_test.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]

        run_resp = client.post("/api/analyses/run", json={
            "dataset_id": did,
            "variable_selection": {
                "dataset_id": did,
                "dependent_variable": "gdp",
                "primary_independent_variable": "trade",
                "control_variables": [],
            },
            "model_type": "ols",
            "transformations": [],
        })
        aid = run_resp.json()["analysis_id"]

        report_resp = client.post("/api/reports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
        })
        assert report_resp.status_code == 200
        rid = report_resp.json()["report_id"]

        from app.storage.repositories import report_repository
        report_repository._cache.clear()

        resp2 = client.get(f"/api/reports/{rid}")
        assert resp2.status_code == 200
        assert resp2.json()["report_id"] == rid


# ---------------------------------------------------------------------------
# Timeline and artifacts
# ---------------------------------------------------------------------------

class TestTimeline:
    def test_timeline_records_events(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Timeline Test"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": range(50), "y": range(50, 100)})
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("tl.csv", df_to_csv_bytes(df), "text/csv")},
        )
        resp = client.get(f"/api/projects/{pid}/timeline")
        assert resp.status_code == 200
        events = resp.json()
        assert len(events) >= 1
        assert events[0]["event_type"] == "dataset_uploaded"

    def test_timeline_for_nonexistent_project(self, client: TestClient):
        resp = client.get("/api/projects/nonexistent/timeline")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# JSON export and ZIP bundle
# ---------------------------------------------------------------------------

class TestExport:
    def test_json_export(self, client: TestClient):
        create = client.post("/api/projects", json={
            "title": "Export Test",
            "research_question": "Does X affect Y?",
        })
        pid = create.json()["project_id"]
        resp = client.get(f"/api/projects/{pid}/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project"]["title"] == "Export Test"
        assert "disclaimer" in data

    def test_bundle_export_no_raw_data(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Bundle Test"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("b.csv", df_to_csv_bytes(df), "text/csv")},
        )
        resp = client.get(f"/api/projects/{pid}/export/bundle")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/zip"
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        assert "project.json" in names
        assert "README.md" in names
        assert not any(n.startswith("raw_data/") for n in names)

    def test_bundle_export_with_raw_data(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Raw Bundle"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("raw.csv", df_to_csv_bytes(df), "text/csv")},
        )
        resp = client.get(f"/api/projects/{pid}/export/bundle?include_raw_data=true")
        assert resp.status_code == 200
        zf = zipfile.ZipFile(io.BytesIO(resp.content))
        names = zf.namelist()
        assert any(n.startswith("raw_data/") for n in names)


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_legacy_upload_still_works(self, client: TestClient):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        resp = client.post(
            "/api/datasets/upload",
            files={"file": ("legacy.csv", df_to_csv_bytes(df), "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["filename"] == "legacy.csv"

    def test_legacy_analysis_still_works(self, client: TestClient):
        df = pd.DataFrame({"gdp": range(50, 100), "trade": range(100, 150)})
        upload = client.post(
            "/api/datasets/upload",
            files={"file": ("compat.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]
        resp = client.post("/api/analyses/run", json={
            "dataset_id": did,
            "variable_selection": {
                "dataset_id": did,
                "dependent_variable": "gdp",
                "primary_independent_variable": "trade",
                "control_variables": [],
            },
            "model_type": "ols",
            "transformations": [],
        })
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Storage safety
# ---------------------------------------------------------------------------

class TestStorageSafety:
    def test_missing_file_returns_storage_error(self, client: TestClient):
        df = pd.DataFrame({"a": [1], "b": [2]})
        resp = client.post(
            "/api/datasets/upload",
            files={"file": ("safe.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = resp.json()["dataset_id"]

        from app.storage.repositories import dataset_repository
        record = dataset_repository.get(did)
        record.original_path.unlink()
        dataset_repository._cache.pop(did, None)

        resp2 = client.get(f"/api/datasets/{did}/overview")
        assert resp2.status_code == 500
        assert "missing" in resp2.json()["error"]["message"].lower()

    def test_dataset_ownership_via_artifacts(self, client: TestClient):
        create = client.post("/api/projects", json={"title": "Ownership"})
        pid = create.json()["project_id"]
        df = pd.DataFrame({"x": [1], "y": [2]})
        upload = client.post(
            f"/api/projects/{pid}/datasets/upload",
            files={"file": ("own.csv", df_to_csv_bytes(df), "text/csv")},
        )
        did = upload.json()["dataset_id"]

        artifacts = client.get(f"/api/projects/{pid}/artifacts").json()
        ds_ids = [d["dataset_id"] for d in artifacts["datasets"]]
        assert did in ds_ids
