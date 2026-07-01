# AI Econometrics Copilot

An explainable AI-assisted econometric modeling platform for economic research.

一个面向经济学研究的、可解释且可复现的 AI 计量建模与分析平台。

Researchers, students, and analysts upload a dataset; the system understands its
structure, profiles data quality, helps configure variable roles, runs *real*
statistical models (OLS, panel fixed/random effects), runs standard
econometric diagnostics, and produces an explainable, reproducible report —
without ever asking a language model to invent a coefficient or p-value.

```
AI  → understands, plans, explains, recommends
Python (pandas / statsmodels / linearmodels) → computes
User → keeps final variable and modeling judgment
```

## Status: Phase 1 (this build)

This build implements **Step 1 (project scaffolding)** and **Step 2 (upload +
data profiling)** of the MVP plan in [docs/development_plan.md](docs/development_plan.md).
See "Implemented in this build" below for the exact feature list.

## Features

### Implemented in this build

- CSV / Excel (`.csv`, `.xlsx`, `.xls`) upload with type/size/content validation
- Automatic dataset preview (row/column counts, dtypes, first 10 rows)
- Rule-based column role inference (Potential Outcome / Explanatory / Control /
  Entity ID / Time Variable / Categorical), exposed as hints, never enforced
- `DatasetProfiler`: missing values, duplicate rows, constant columns, IQR and
  Z-score outlier detection, skewness/kurtosis, zero/negative ratios, and
  explainable transformation suggestions (e.g. log transform)
- Rule-driven panel / time-series / cross-sectional structure detection
  (balanced/unbalanced panel, entity & time column identification)
- Academic-styled Next.js dashboard: dataset overview, column types, data
  preview, detected structure, missing-value chart, column quality table
- Reserved (not yet wired) interfaces for the future AI planning / discovery
  layer: `variable_semantics.py`, `model_planner.py`, `discovery_engine.py`,
  `econometric_rules.py`
- Backend unit tests (pytest) covering upload, column typing, profiling, and
  structure detection

### Not yet implemented (future phases)

- OLS / robust OLS / panel fixed & random effects execution and diagnostics
  (VIF, Breusch-Pagan, Hausman, Durbin-Watson) — Phase 2
- Cleaning/transformation execution + transformation log — Phase 2/3
- Model comparison & recommendation service — Phase 3
- Rule-based report generation (HTML/Markdown/JSON export) — Phase 3
- Autonomous Econometric Discovery Engine — Phase 5 (interfaces only, mocked)

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router), TypeScript, React, Tailwind CSS, shadcn/ui-style components, Recharts |
| Backend | Python, FastAPI, Pydantic |
| Analysis | pandas, numpy, scipy, statsmodels, linearmodels, scikit-learn, openpyxl |

## Project layout

```
ai-econometrics-copilot/
├── frontend/        Next.js app (dashboard UI)
├── backend/          FastAPI app (upload, profiling, structure detection)
├── sample_data/       Synthetic World Bank–style panel dataset
├── docs/               architecture / API / rules / roadmap docs
└── docker-compose.yml
```

## Running locally

### Backend

```bash
cd backend
uv venv .venv --python 3.12   # or: python3 -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt   # or: pip install -r requirements.txt
cp ../.env.example .env   # optional, defaults work out of the box
uvicorn app.main:app --reload --port 8000
```

The API is served at `http://localhost:8000/api`, health check at
`http://localhost:8000/health`, interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
npm run dev
```

Visit `http://localhost:3000`.

### Sample workflow

1. Start both servers above.
2. Open the frontend and upload [`sample_data/world_bank_panel_sample.xlsx`](sample_data/world_bank_panel_sample.xlsx).
3. Review the Dataset Overview, Column Types, and Data Preview cards.
4. Review the Detected Structure card — it should identify a **balanced panel**
   of 20 countries over 15 years (`country` × `year`).
5. Review the Data Quality Summary — missing values in `education_spending`,
   `employment_rate`, `trade_openness`, and outliers/log-transform suggestions
   for `gdp_per_capita`.

Default demo research question (for the modeling phase, not yet implemented):
*Is internet penetration associated with GDP per capita across countries over time?*

## Testing

```bash
cd backend
source .venv/bin/activate
python -m pytest -q
```

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

## Screenshots

_Placeholder — add dashboard screenshots here once the UI is finalized._

## Documentation

- [docs/architecture.md](docs/architecture.md) — frontend/backend architecture, data flow, reproducibility design
- [docs/api.md](docs/api.md) — REST API reference
- [docs/econometric_rules.md](docs/econometric_rules.md) — thresholds and rules used by the profiler/diagnostics
- [docs/development_plan.md](docs/development_plan.md) — phased roadmap

## Roadmap

See [docs/development_plan.md](docs/development_plan.md) for the full phase breakdown
(Phase 1: upload & profiling → Phase 2: modeling & diagnostics → Phase 3: reporting
→ Phase 4: AI planning layer → Phase 5: autonomous discovery engine).

## Disclaimer

This platform identifies statistical associations. It does not establish
causal effects unless additional identification assumptions are explicitly
justified by the researcher.
