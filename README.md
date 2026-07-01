[中文文档](README.zh-CN.md)

# AI Econometrics Copilot

An explainable, reproducible econometric modeling platform for economic research.
AI understands and recommends — Python statistical libraries do all real computation — users retain final research judgement.

> **Principle:** LLMs never generate regression coefficients, p-values, R², or significance conclusions. All statistical values are computed by `statsmodels`, `linearmodels`, `pandas`, `numpy`, and `scipy`.

---

## Key Features

| Feature | Description |
|---|---|
| Dataset upload | CSV, Excel (.xlsx/.xls), up to 50 MB |
| Data profiling | Missing values, outliers, skewness, transformation suggestions |
| Structure detection | Panel / time-series / cross-sectional (rule-based, never name-only) |
| Variable role selection | Dependent, primary IV, controls, entity ID, time — with rule-based pre-fill |
| Data transformations | Log, winsorize, standardize, imputation, drop duplicates/missing |
| OLS regression | Ordinary and HC1-robust standard errors via `statsmodels` |
| Panel regression | Pooled OLS, Fixed Effects, Random Effects, Two-Way FE via `linearmodels` |
| Clustered SE | Clustered by entity for panel models |
| Diagnostics | VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, Hausman test |
| Model recommendation | Rule-driven suggestions (no LLM) |
| Results dashboard | Coefficient table, coefficient plot, residual charts, correlation heatmap |
| Reproducible export | Complete JSON artifact including software versions |

---

## Architecture

```
Upload → Profile → Variable Selection → Transformation → Model Run → Results
```

```
frontend/         Next.js 16 + TypeScript + Tailwind + Recharts
backend/          FastAPI + Pydantic v2 + pandas + statsmodels + linearmodels
sample_data/      World Bank–style synthetic panel (20 countries × 15 years)
docs/             Architecture, API reference, econometric rules, dev plan
```

**Separation of concerns:**
- `app/services/` — pure data functions (profiling, structure detection, transformations)
- `app/analysis/` — statistical computation wrappers (OLS, panel, diagnostics)
- `app/api/` — thin HTTP routing, no business logic
- `app/schemas/` — Pydantic models shared between layers

---

## Technology Stack

**Backend**
- Python 3.12+
- FastAPI, Pydantic v2, pydantic-settings
- pandas, numpy, scipy
- statsmodels (OLS, diagnostics)
- linearmodels (panel regression)
- openpyxl (Excel support)
- pytest, httpx

**Frontend**
- Next.js 16, React 19, TypeScript 5
- Tailwind CSS v4
- Recharts v3
- lucide-react

---

## Repository Structure

```
ai-econometrics-copilot/
├── backend/
│   ├── app/
│   │   ├── analysis/          # diagnostics.py, model_runner.py, ols_models.py, panel_models.py, model_recommender.py, econometric_rules.py
│   │   ├── api/               # datasets.py, analyses.py
│   │   ├── core/              # config.py, errors.py, logging.py
│   │   ├── models/            # dataset_registry.py, analysis_registry.py
│   │   ├── schemas/           # dataset.py, modeling.py, common.py
│   │   └── services/          # column_typing.py, data_profiler.py, dataset_service.py, structure_detector.py, transformation_service.py
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                         # Home: upload + profile dashboard
│   │   ├── datasets/[datasetId]/model/      # Variable selection + model config
│   │   └── analyses/[analysisId]/           # Results dashboard
│   ├── components/
│   │   ├── modeling/                        # VariableRoleSelector, TransformationPanel, ModelConfigurationPanel
│   │   ├── results/                         # CoefficientTable, CoefficientPlot, ResidualPlot, CorrelationHeatmap, DiagnosticsPanel
│   │   └── ui/                              # card, button, badge, table, select
│   ├── lib/                                 # api.ts, utils.ts
│   └── types/                               # dataset.ts, modeling.ts
├── sample_data/
│   └── world_bank_panel_sample.xlsx
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── econometric_rules.md
│   └── development_plan.md
└── scripts/
    └── generate_sample_data.py
```

---

## Prerequisites

- Python 3.12+
- Node.js 20+
- `uv` (recommended) or `pip`

---

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Or with `uv`:
```bash
cd backend
uv sync
```

---

## Frontend Setup

```bash
cd frontend
npm install
```

---

## Environment Variables

**Backend** (optional, defaults shown):
```
ECOPILOT_CORS_ORIGINS=["http://localhost:3000"]
ECOPILOT_MAX_UPLOAD_SIZE_BYTES=52428800
ECOPILOT_LOG_LEVEL=INFO
```

**Frontend** (optional):
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

---

## How to Run Locally

**Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## How to Run Tests

```bash
cd backend
python -m pytest -q
```

Expected: **76 tests passing**.

Frontend type check:
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## Example Workflow

1. Upload `sample_data/world_bank_panel_sample.xlsx`
2. Review dataset profile — panel detected (20 entities × 15 periods)
3. Click **Configure & Run Model →**
4. Variable roles are pre-filled: `gdp_per_capita` as outcome, `internet_users` as explanatory
5. Optionally add log transform for right-skewed variables
6. Select **Fixed Effects** (recommended for panel data)
7. Enable clustered standard errors by entity
8. Click **Run Analysis →**
9. View coefficient table, significance stars, Hausman test, VIF, residual plots
10. Export reproducible JSON artifact

---

## Supported Models

| Model | Library | Use Case |
|---|---|---|
| OLS | statsmodels | Cross-sectional / baseline |
| Robust OLS (HC1) | statsmodels | Heteroskedastic errors |
| Pooled OLS | linearmodels | Panel data, ignoring panel structure |
| Fixed Effects | linearmodels | Time-invariant unobserved heterogeneity |
| Random Effects | linearmodels | Uncorrelated entity effects |
| Two-Way Fixed Effects | linearmodels | Entity + time effects |

---

## Supported Diagnostics

| Diagnostic | Purpose |
|---|---|
| VIF | Multicollinearity check (threshold: 5 / 10) |
| Breusch-Pagan | Heteroskedasticity test |
| Jarque-Bera | Residual normality test |
| Durbin-Watson | First-order autocorrelation |
| Hausman Test | FE vs RE selection (panel data) |
| Correlation Matrix | Pearson correlation heatmap |
| Descriptive Statistics | Per-variable summary |

---

## Current Limitations

- In-process storage only (no database) — data is lost on server restart
- No authentication or multi-user isolation
- No arbitrary formula editor (variables selected through UI)
- No LaTeX/PDF report export
- Hausman test uses pseudo-inverse for robustness — may report unavailable for near-singular matrices
- Two-way fixed effects automatically drops absorbed variables (linearmodels `drop_absorbed=True`)

---

## Reproducibility Design

Every `POST /api/analyses/run` stores a complete analysis record including:
- Original dataset metadata
- Every transformation applied (with row counts before/after)
- Exact model formula
- All coefficients and diagnostics
- Software library versions
- Timestamp

Export via `GET /api/analyses/{id}/export/json`.

---

## Roadmap

- **Phase 4:** Rule-based narrative report generation, model comparison table
- **Phase 5:** AI planning layer — semantic variable role suggestion, candidate model proposals
- **Phase 6:** Autonomous discovery engine with bounded search and multiple-testing correction

---

## Causal Language Disclaimer

> This analysis identifies statistical associations and does not establish causal effects unless additional identification assumptions are justified.
