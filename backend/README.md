# Backend — AI Econometrics Copilot

FastAPI service for dataset upload, data quality profiling, and dataset
structure detection (Phase 1). See [../docs/architecture.md](../docs/architecture.md)
and [../docs/api.md](../docs/api.md) for details.

## Setup

```bash
uv venv .venv --python 3.12   # or: python3 -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt   # or: pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

- API: `http://localhost:8000/api`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Test

```bash
python -m pytest -q
```

## Configuration

Environment variables (prefix `ECOPILOT_`), see `app/core/config.py`:

| Variable | Default | Meaning |
|---|---|---|
| `ECOPILOT_UPLOAD_DIR` | `storage/uploads` | Where uploaded files are persisted |
| `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` | `52428800` (50 MB) | Upload size limit |
| `ECOPILOT_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `ECOPILOT_OUTLIER_IQR_MULTIPLIER` | `1.5` | IQR outlier multiplier |
| `ECOPILOT_OUTLIER_ZSCORE_THRESHOLD` | `3.0` | Z-score outlier threshold |
| `ECOPILOT_HIGH_SKEW_THRESHOLD` | `1.0` | Skewness threshold for transform suggestions |
| `ECOPILOT_VIF_WARNING_THRESHOLD` | `5.0` | VIF "moderate risk" threshold |
| `ECOPILOT_VIF_SEVERE_THRESHOLD` | `10.0` | VIF "severe risk" threshold |
| `ECOPILOT_HETEROSKEDASTICITY_ALPHA` | `0.05` | Breusch-Pagan significance level |

## Directory layout

```
app/
├── main.py         FastAPI app + middleware + exception handlers
├── core/           config, logging, error types
├── api/            HTTP routers
├── schemas/        Pydantic request/response models
├── services/       dataset ingestion, column typing, profiling, structure detection
├── models/         in-process dataset registry
└── analysis/       reserved interfaces for the future AI planning/discovery layer
tests/               pytest suite
```
