from __future__ import annotations

from tests.conftest import df_to_csv_bytes, df_to_xlsx_bytes


def test_upload_csv_returns_overview(client, panel_df):
    content = df_to_csv_bytes(panel_df)
    response = client.post(
        "/api/datasets/upload", files={"file": ("panel.csv", content, "text/csv")}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "panel.csv"
    assert body["n_rows"] == len(panel_df)
    assert body["n_columns"] == len(panel_df.columns)
    assert len(body["preview_rows"]) == min(10, len(panel_df))
    assert {c["name"] for c in body["column_types"]} == set(panel_df.columns)


def test_upload_excel_returns_overview(client, panel_df):
    content = df_to_xlsx_bytes(panel_df)
    response = client.post(
        "/api/datasets/upload",
        files={"file": ("panel.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["n_rows"] == len(panel_df)


def test_upload_rejects_unsupported_extension(client):
    response = client.post(
        "/api/datasets/upload", files={"file": ("data.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_upload_rejects_empty_file(client):
    response = client.post(
        "/api/datasets/upload", files={"file": ("data.csv", b"", "text/csv")}
    )
    assert response.status_code == 422


def test_get_dataset_after_upload(client, panel_df):
    content = df_to_csv_bytes(panel_df)
    upload = client.post(
        "/api/datasets/upload", files={"file": ("panel.csv", content, "text/csv")}
    )
    dataset_id = upload.json()["dataset_id"]

    response = client.get(f"/api/datasets/{dataset_id}")
    assert response.status_code == 200
    assert response.json()["dataset_id"] == dataset_id


def test_get_unknown_dataset_returns_404(client):
    response = client.get("/api/datasets/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "dataset_not_found"


def test_profile_endpoint_returns_quality_and_structure(client, panel_df):
    content = df_to_csv_bytes(panel_df)
    upload = client.post(
        "/api/datasets/upload", files={"file": ("panel.csv", content, "text/csv")}
    )
    dataset_id = upload.json()["dataset_id"]

    response = client.get(f"/api/datasets/{dataset_id}/profile")
    assert response.status_code == 200
    body = response.json()
    assert body["quality"]["n_rows"] == len(panel_df)
    assert body["structure"]["dataset_type"] == "panel"
    assert body["structure"]["entity_column"] == "country"
    assert body["structure"]["time_column"] == "year"
