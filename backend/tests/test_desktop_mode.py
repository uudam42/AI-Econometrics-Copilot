"""Tests for desktop mode configuration and sidecar compatibility."""
from __future__ import annotations

import os

import pytest


class TestDesktopModeConfig:
    def test_dynamic_port_env_var(self):
        port = int(os.environ.get("AI_ECONOMETRICS_PORT", "8000"))
        assert isinstance(port, int)
        assert 1 <= port <= 65535

    def test_desktop_mode_flag(self):
        val = os.environ.get("AI_ECONOMETRICS_DESKTOP_MODE", "false")
        assert val in ("true", "false")

    def test_explicit_data_dir_config(self, client, tmp_path):
        os.environ["ECOPILOT_DATA_DIR"] = str(tmp_path)
        from app.core.config import Settings
        s = Settings()
        assert str(s.data_dir) == str(tmp_path)

    def test_explicit_database_url(self, tmp_path):
        db_path = tmp_path / "test.db"
        url = f"sqlite:///{db_path}"
        os.environ["ECOPILOT_DATABASE_URL"] = url
        from app.core.config import Settings
        s = Settings()
        assert s.database_url == url

    def test_explicit_upload_dir(self, tmp_path):
        uploads = tmp_path / "my_uploads"
        uploads.mkdir()
        os.environ["ECOPILOT_UPLOAD_DIR"] = str(uploads)
        from app.core.config import Settings
        s = Settings()
        assert str(s.upload_dir) == str(uploads)

    def test_explicit_artifact_dir(self, tmp_path):
        artifacts = tmp_path / "my_artifacts"
        artifacts.mkdir()
        os.environ["ECOPILOT_ARTIFACT_DIR"] = str(artifacts)
        from app.core.config import Settings
        s = Settings()
        assert str(s.artifact_dir) == str(artifacts)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "app" in data
        assert "version" in data

    def test_health_includes_app_name(self, client):
        resp = client.get("/health")
        assert resp.json()["app"] == "AI Econometrics Copilot"


class TestDataPersistence:
    def test_upload_dir_created(self, client, tmp_path):
        from app.core.config import settings
        assert settings.upload_dir.exists()

    def test_database_accessible(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200

    def test_desktop_cors_origin(self, tmp_path):
        os.environ["ECOPILOT_CORS_ORIGINS"] = '["http://tauri.localhost"]'
        from app.core.config import Settings
        s = Settings()
        assert "http://tauri.localhost" in s.cors_origins


class TestExportPathSafety:
    def test_artifact_dir_is_separate(self, client, tmp_path):
        from app.core.config import settings
        assert settings.artifact_dir != settings.upload_dir
