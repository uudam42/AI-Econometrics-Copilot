# Architecture

## Overview

AI Econometrics Copilot separates three concerns strictly:

1. **Understanding & explanation** (rule-driven today; AI-assisted in later
   phases) — column typing, structure detection, transformation suggestions,
   report narration.
2. **Computation** — pandas / numpy / scipy / statsmodels / linearmodels.
   Every number shown to the user is produced here. Nothing is computed by an
   LLM.
3. **User judgment** — variable role selection, which model to run, whether to
   apply a suggested transformation. The system recommends; the user decides.

## Frontend architecture

- **Next.js App Router**, TypeScript, single-page dashboard (`app/page.tsx`)
  driving client-side state for the current dataset.
- `lib/api.ts` is the only module that talks to the backend; it centralizes
  the base URL (`NEXT_PUBLIC_API_BASE_URL`) and error unwrapping
  (`ApiError`, mirroring the backend's unified error envelope).
- `types/dataset.ts` mirrors the backend Pydantic schemas by hand. Because
  both are small and change together, this is kept manual rather than
  code-generated for Phase 1; a future phase may generate this from the
  OpenAPI schema FastAPI already exposes at `/openapi.json`.
- `components/ui/*` are minimal, dependency-free primitives in the shadcn/ui
  style (Card, Badge, Button, Table) so the design system has no external
  registry dependency yet.
- Charts use Recharts (`components/charts/*`); Python-side plotting
  (matplotlib) is reserved for static report export only, per product
  requirements — the live UI never renders server-rendered images.

## Backend architecture

```
backend/app/
├── main.py          FastAPI app: CORS, exception handlers, router registration
├── core/            config (Settings), logging, error types + handlers
├── api/             HTTP routers (datasets.py)
├── schemas/         Pydantic request/response models
├── services/        business logic: dataset_service, column_typing,
│                    data_profiler, structure_detector
├── models/          in-process dataset registry (see below)
└── analysis/        reserved interfaces for the future AI planning layer
```

Business logic lives in `services/`, never in the API layer — routers only
translate HTTP <-> service calls and are kept thin and testable in isolation
from FastAPI's request/response cycle.

### Dataset storage (Phase 1)

There is no database yet. `app.models.dataset_registry.DatasetRegistry` is an
in-process, thread-safe dictionary mapping `dataset_id -> DatasetRecord`
(filename, original file path under `storage/uploads/`, the parsed
`pandas.DataFrame`, upload timestamp). This is sufficient for a single-process
demo deployment. A future phase should replace this with a persistent store
(e.g. Postgres for metadata + object storage for files) without changing the
service-layer interfaces, since routers only depend on `registry.get(...)`.

## Analysis pipeline (Phase 1 scope)

```
Upload (CSV/XLSX)
  → dataset_service.ingest_upload()      validate extension/size, parse, register
  → column_typing.infer_all_column_types() rule-based dtype + role-hint inference
  → data_profiler.profile_dataset()       missing/duplicate/outlier/skew analysis
  → structure_detector.detect_structure() panel / time-series / cross-sectional
```

Every step above is a pure function over a `pandas.DataFrame` and is unit
tested independently (see `backend/tests/`).

## Data flow

```
Browser                     FastAPI                      pandas/scipy
  |  POST /datasets/upload    |                                |
  |--------------------------->|  ingest_upload()               |
  |                            |------------------------------->|
  |                            |  DataFrame in DatasetRegistry   |
  |  <- DatasetOverviewResponse|<--------------------------------|
  |                            |                                |
  |  GET /datasets/{id}/profile|                                |
  |--------------------------->|  profile_dataset() + detect_structure()
  |                            |------------------------------->|
  |  <- DatasetProfileResponse |<--------------------------------|
```

## Model execution flow (Phase 2, not yet implemented)

Reserved: `POST /api/models/run` will take a dependent variable, independent
variable, controls, and an explicit estimator (OLS / robust OLS / pooled OLS /
fixed effects / random effects), delegate to `statsmodels`/`linearmodels`, and
return a structured `ModelResult` (coefficients, standard errors, fit
statistics) plus a `DiagnosticsReport`. The router will remain a thin
translation layer, matching the Phase 1 pattern above.

## Reproducibility design

- The original uploaded file is preserved on disk (`storage/uploads/<uuid>.<ext>`)
  and never mutated in place.
- All cleaning/transformation operations (Phase 3) are additive: they produce
  a `processed_dataframe` plus an ordered `transformation_log`, while
  `dataframe` (original) is retained on the same `DatasetRecord`.
- All statistical results are recomputed from the stored DataFrame on each
  request rather than cached/mutated, so profile and diagnostics endpoints are
  idempotent and safe to re-run.
- Thresholds that drive recommendations (outlier method, skew cutoff, VIF
  cutoffs, alpha) are centralized in `app/core/config.py` and
  `app/analysis/econometric_rules.py`, not scattered as magic numbers, so a
  report generated today can be explained by inspecting one place.
