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
| **Multi-model comparison** | Run up to 6 models on the same variables; side-by-side fit metrics and diagnostics |
| **Transparent recommendation** | Multi-criteria scoring (structure, Hausman, heteroskedasticity, parsimony, fit) |
| **Coefficient stability view** | Compare how the primary IV coefficient behaves across specifications |
| **Research report generator** | Deterministic narrative sections — no LLM, no fabricated statistics |
| **Report export** | Markdown, HTML, and JSON artifact with reproducibility metadata |
| **Research planning** | Type a question in natural language; the system proposes variables, models, and transformations |
| **Causal language detection** | Detects "cause/affect/impact" and reframes as association with explicit warning |
| **Absorbed variable transparency** | Two-Way FE reports which variables were absorbed and warns if the primary IV is affected |
| **Exploratory discovery** | Bounded specification search with variable screening, multiple-testing correction (BH/Bonferroni), stability assessment |
| **Multi-criteria finding scoring** | 6-dimension weighted score: corrected support, stability, direction, data quality, diagnostics, fit |
| **Finding-to-plan handoff** | Promote any exploratory finding into a theory-driven research plan with one click |
| **Persistent research workspaces** | SQLite-backed projects that survive server restarts — organize datasets, analyses, and reports under one project |
| **Timeline tracking** | Chronological activity log for every project action — dataset uploads, analyses, comparisons, reports |
| **Artifact history** | Browse all artifacts (datasets, analyses, plans, reports, discoveries) linked to a project |
| **Reproducible bundle export** | Download a ZIP bundle of any project — metadata, artifacts, timeline, and optionally raw data |
| **Restart recovery** | DataFrames cached in memory, lazily reloaded from disk on restart — no data loss |
| **Publication-ready tables** | Academic regression tables (single-model, multi-model comparison, coefficient stability, descriptive stats, diagnostics) with *** significance notation |
| **Academic figures** | Coefficient plot, residual vs fitted, actual vs predicted, correlation heatmap, stability chart — all via matplotlib |
| **DOCX export** | Genuinely editable Word documents with cover page, tables, figures, and professional formatting via python-docx |
| **LaTeX export** | Standalone .tex with tables/, figures/, appendix/ directories — compiles with pdflatex |
| **Methodology appendix** | Auto-generated methodology section with variable selection, model specification, and limitations |
| **Reproducibility appendix** | Dataset checksum, transformation log, model configuration, software versions — all deterministic |
| Results dashboard | Coefficient table, coefficient plot, residual charts, correlation heatmap |
| Reproducible export | Complete JSON artifact including software versions |

---

## Architecture

```
Upload → Profile → Variable Selection → Transformation → Model Run → Results
                 ↘ Discovery → Screening → Specs → Correction → Findings → Plan
```

```
Upload → Profile → Variable Selection → Transformation → Model Run → Results
       ↘ Project Workspace → Datasets → Analyses → Timeline → Export Bundle
```

```
frontend/         Next.js 16 + TypeScript + Tailwind + Recharts
backend/          FastAPI + Pydantic v2 + SQLAlchemy 2.x + pandas + statsmodels + linearmodels
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
- SQLAlchemy 2.x (SQLite persistence)
- python-docx (DOCX export)
- matplotlib (publication figures)
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
│   │   ├── analysis/          # diagnostics.py, model_runner.py, ols_models.py, panel_models.py, model_recommender.py, econometric_rules.py, discovery_*.py
│   │   ├── api/               # datasets.py, analyses.py, projects.py, publication_exports.py
│   │   ├── core/              # config.py, errors.py, logging.py
│   │   ├── models/            # backward-compatible re-export shims
│   │   ├── storage/           # database.py, models.py, repositories.py (SQLite + in-memory cache)
│   │   ├── schemas/           # dataset.py, modeling.py, project.py, common.py
│   │   └── services/          # column_typing.py, data_profiler.py, dataset_service.py, structure_detector.py, transformation_service.py
│   └── tests/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                         # Home: upload + profile dashboard
│   │   ├── datasets/[datasetId]/model/      # Variable selection + model config
│   │   ├── datasets/[datasetId]/discover/   # Exploratory relationship discovery
│   │   ├── analyses/[analysisId]/           # Results dashboard
│   │   ├── projects/                        # Project list, create, detail
│   │   ├── projects/[projectId]/            # Project workspace, datasets, timeline, exports
│   │   └── publication-exports/[exportId]/ # Publication export detail
│   ├── components/
│   │   ├── modeling/                        # VariableRoleSelector, TransformationPanel, ModelConfigurationPanel
│   │   ├── projects/                        # ProjectCard, ProjectForm, ProjectOverview, ProjectTimeline, ArtifactHistoryTable
│   │   ├── publication-exports/             # PublicationExportForm, ExportDownloadActions, ExportStatus, ExportList
│   │   ├── results/                         # CoefficientTable, CoefficientPlot, ResidualPlot, CorrelationHeatmap, DiagnosticsPanel
│   │   └── ui/                              # card, button, badge, table, select
│   ├── lib/                                 # api.ts, utils.ts
│   └── types/                               # dataset.ts, modeling.ts, project.ts, publication_export.ts
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

**Backend** (optional, defaults shown — see `backend/.env.example` for all options):
```
ECOPILOT_DATABASE_URL=sqlite:///./data/ai_econometrics.db
ECOPILOT_DATA_DIR=data
ECOPILOT_UPLOAD_DIR=data/uploads
ECOPILOT_ARTIFACT_DIR=data/artifacts
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

Expected: **267 tests passing**.

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

- Single-user, local SQLite storage — no multi-user or cloud sync
- No authentication or multi-user isolation
- No arbitrary formula editor (variables selected through UI)
- PDF export requires native Pango/Cairo libraries — DOCX and LaTeX available as alternatives
- Hausman test uses pseudo-inverse for robustness — may report unavailable for near-singular matrices
- Two-way fixed effects may absorb variables collinear with entity/time dummies (now reported transparently)

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

## Supported Models (Comparison)

| Model | Library | Use Case |
|---|---|---|
| OLS | statsmodels | Cross-sectional / baseline |
| Robust OLS (HC1) | statsmodels | Heteroskedastic errors |
| Pooled OLS | linearmodels | Panel data, ignoring panel structure |
| Fixed Effects | linearmodels | Time-invariant unobserved heterogeneity |
| Random Effects | linearmodels | Uncorrelated entity effects |
| Two-Way Fixed Effects | linearmodels | Entity + time effects |

## Recommendation Scoring Criteria

The model selection recommendation uses a weighted multi-criteria score:

| Criterion | Weight |
|---|---|
| Structural Compatibility | 25% |
| Hausman Test Guidance | 20% |
| Heteroskedasticity Robustness | 15% |
| Model Fit | 15% |
| Parsimony | 10% |
| Sample Size Adequacy | 10% |
| Estimation Success | 5% |

---

## Roadmap

| Phase | Feature | Status |
|---|---|---|
| Phase 1 | Data upload, profiling, structure detection | ✅ Complete |
| Phase 2 | Variable configuration, data transformations | ✅ Complete |
| Phase 3 | Regression execution, econometric diagnostics | ✅ Complete |
| Phase 4 | Multi-model comparison, transparent recommendation, research report | ✅ Complete |
| Phase 5 | Natural-language research planning, absorbed variable transparency | ✅ Complete |
| Phase 6 | Constrained exploratory relationship discovery | ✅ Complete |
| Phase 7 | Persistent research workspaces and reproducible project storage | ✅ Complete |
| Phase 8 | Publication-ready reporting and advanced academic export | ✅ Complete |
| Phase 9 | Advanced econometric models and causal identification workflows | Future |

---

## Causal Language Disclaimer

> This analysis identifies statistical associations and does not establish causal effects unless additional identification assumptions are justified.
