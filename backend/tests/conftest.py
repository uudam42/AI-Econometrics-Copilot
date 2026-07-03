from __future__ import annotations

import io
import os
import tempfile

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _temp_db(tmp_path):
    """Use a temporary SQLite database and upload dir for each test."""
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()

    os.environ["ECOPILOT_DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["ECOPILOT_DATA_DIR"] = str(tmp_path)
    os.environ["ECOPILOT_UPLOAD_DIR"] = str(upload_dir)
    os.environ["ECOPILOT_ARTIFACT_DIR"] = str(artifact_dir)

    from app.core.config import Settings
    import app.core.config as config_mod
    config_mod.settings = Settings()

    from app.storage.database import reset_engine, init_db
    reset_engine()
    init_db()

    from app.storage.repositories import (
        project_repository,
        dataset_repository,
        analysis_repository,
        comparison_repository,
        plan_repository,
        report_repository,
        discovery_repository,
    )
    dataset_repository._cache.clear()
    analysis_repository._cache.clear()
    comparison_repository._cache.clear()
    plan_repository._cache.clear()
    report_repository._cache.clear()
    discovery_repository._cache.clear()

    yield

    reset_engine()


@pytest.fixture()
def client() -> TestClient:
    from app.main import app
    return TestClient(app)


@pytest.fixture()
def panel_df() -> pd.DataFrame:
    rows = []
    for country in ["Alandia", "Borovia", "Casteria"]:
        for year in range(2010, 2016):
            rows.append(
                {
                    "country": country,
                    "year": year,
                    "gdp_per_capita": 1000 + year + hash(country) % 100,
                    "internet_users": 10 + (year - 2010) * 5,
                }
            )
    return pd.DataFrame(rows)


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def df_to_xlsx_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()
