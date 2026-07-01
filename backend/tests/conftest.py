from __future__ import annotations

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
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
