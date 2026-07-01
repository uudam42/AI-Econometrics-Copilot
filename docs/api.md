# API Reference

Base path: `/api` (e.g. `http://localhost:8000/api`). Interactive OpenAPI docs
are auto-served by FastAPI at `/docs` and `/openapi.json`.

## Error format

All errors share one envelope, so the frontend never has to parse a Python
traceback:

```json
{
  "error": {
    "code": "unsupported_file_type",
    "message": "File type '.txt' is not supported. Allowed types: .csv, .xlsx, .xls.",
    "details": { "filename": "data.txt" }
  }
}
```

| HTTP status | `error.code` | Meaning |
|---|---|---|
| 404 | `dataset_not_found` | No dataset with the given id |
| 413 | `file_too_large` | Upload exceeds `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` (default 50 MB) |
| 415 | `unsupported_file_type` | Extension not in `.csv`, `.xlsx`, `.xls` |
| 422 | `validation_error` | Empty file, unparseable file, empty dataset |
| 500 | `internal_error` | Unexpected server error (logged server-side; no traceback leaked) |

## Endpoints (implemented in this build)

### `POST /api/datasets/upload`

Multipart form upload, field name `file`. Returns a `DatasetOverviewResponse`:
filename, row/column counts, per-column type + role hints, first 10 rows,
upload timestamp.

### `GET /api/datasets/{dataset_id}`

Returns a lightweight `DatasetSummary` (id, filename, shape, column names,
uploaded_at). Used to confirm a dataset still exists without re-fetching the
full preview.

### `GET /api/datasets/{dataset_id}/overview`

Same payload as the upload response — lets the frontend re-fetch the overview
(e.g. after a refresh) without re-uploading.

### `GET /api/datasets/{dataset_id}/profile`

Returns `DatasetProfileResponse`:

```json
{
  "dataset_id": "...",
  "quality": {
    "n_rows": 300,
    "n_columns": 9,
    "duplicate_row_count": 0,
    "duplicate_row_rate": 0.0,
    "constant_columns": [],
    "potential_id_columns": [],
    "potential_time_columns": ["year"],
    "potential_categorical_columns": ["country"],
    "columns": [
      {
        "column": "gdp_per_capita",
        "missing_rate": 0.0,
        "outlier_count": 4,
        "outlier_method": "IQR",
        "skewness": 2.1,
        "suggested_transformation": "log",
        "reason": "Variable is positive and heavily right-skewed."
      }
    ]
  },
  "structure": {
    "dataset_type": "panel",
    "entity_column": "country",
    "time_column": "year",
    "is_balanced_panel": true,
    "entity_count": 20,
    "time_period_count": 15,
    "explanation": "Detected repeated 'country' observations across 15 distinct values of 'year' ..."
  }
}
```

## Endpoints reserved for later phases (documented, not yet implemented)

These are named in the product spec's API list but require the modeling
engine (Phase 2) and report generator (Phase 3):

- `POST /api/datasets/{dataset_id}/transform` — apply a cleaning/transformation
  step and append to the transformation log
- `POST /api/models/run` — execute OLS / robust OLS / pooled OLS / fixed
  effects / random effects
- `GET /api/models/{model_id}` — fetch a stored model result
- `GET /api/models/{model_id}/diagnostics` — VIF, Breusch-Pagan, Hausman,
  Durbin-Watson, residual normality
- `GET /api/models/{model_id}/report` — rule-driven HTML/Markdown report
- `GET /api/models/{model_id}/export/json` — JSON analysis artifact
