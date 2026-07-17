<img width="1672" height="941" alt="econometricsFlag" src="https://github.com/user-attachments/assets/3971eb69-4ce1-4160-8f41-5fb5f857fc7a" />


[中文文档](README.zh-CN.md)

# AI Econometrics Copilot

An explainable, reproducible econometric modeling platform for economic research.
AI understands and recommends — Python statistical libraries do all real computation — users retain final research judgement.

> **Core Principle:** LLMs never generate regression coefficients, p-values, R², or significance conclusions. All statistical values are computed by `statsmodels`, `linearmodels`, `pandas`, `numpy`, and `scipy`.

---

## Getting Started

### Option 1 — Windows Desktop (easiest)

Download the installer from [Releases](https://github.com/uudam42/AI-Econometrics-Copilot/releases) → install → open → click **Analyse My Excel / CSV**.

Or use the one-line PowerShell downloader:

```powershell
irm https://raw.githubusercontent.com/uudam42/AI-Econometrics-Copilot/main/installer_downloader/downloader.ps1 | iex
```

No Docker, Python, Node.js, or browser required. All data stays on the local computer.

### Option 2 — Docker (cross-platform)

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000). Backend API docs at [http://localhost:8000/docs](http://localhost:8000/docs).

Data persists in a named Docker volume (`ai_econometrics_data`). To reset:

```bash
docker compose down -v
```

### Option 3 — Local Development

```bash
bash scripts/start-local.sh       # macOS / Linux
powershell scripts/start-local.ps1  # Windows
```

Or use Make:

```bash
make start    # start both services
make stop     # stop both services
make test     # run backend tests + frontend lint + typecheck
```

<details>
<summary>Manual setup (backend + frontend separately)</summary>

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).
</details>

> For non-technical users, use the Windows installer or downloader.
> Docker and source-code setup are intended for developers.

---

## Prerequisites

- Python 3.10+ (3.12 recommended)
- Node.js 18+ (20 recommended)
- Docker + Docker Compose (for one-command startup)

---

## Key Features

| Feature | Description |
|---|---|
| Quick Analyze | Four-stage guided workflow: upload → auto-plan → confirm → plain-language results |
| Bilingual UI | One-click English / 中文 language switcher, persisted across sessions |
| Windows desktop app | Standalone Tauri installer — no Docker, Python, Node.js, or browser required |
| Dataset upload | CSV, Excel (.xlsx/.xls), up to 50 MB |
| Data profiling | Missing values, outliers, skewness, transformation suggestions |
| Structure detection | Panel / time-series / cross-sectional (rule-based, never name-only) |
| Variable role selection | Dependent, primary IV, controls, entity ID, time — with rule-based pre-fill |
| Data transformations | Log, winsorize, standardize, imputation, drop duplicates/missing |
| OLS regression | Ordinary and HC1-robust standard errors via `statsmodels` |
| Panel regression | Pooled OLS, Fixed Effects, Random Effects, Two-Way FE via `linearmodels` |
| Clustered SE | Clustered by entity for panel models |
| Diagnostics | VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, Hausman test |
| Multi-model comparison | Up to 6 models on the same variables; side-by-side fit metrics |
| Transparent recommendation | Multi-criteria scoring (structure, Hausman, heteroskedasticity, parsimony, fit) |
| Coefficient stability | Compare how the primary IV coefficient behaves across specifications |
| Research report generator | Deterministic narrative — no LLM, no fabricated statistics |
| Report export | Markdown, HTML, JSON with reproducibility metadata |
| Research planning | Natural language question → proposed variables, models, transformations |
| Causal language detection | Detects "cause/affect/impact" and reframes as association |
| Absorbed variable transparency | Two-Way FE reports which variables were absorbed |
| Exploratory discovery | Bounded specification search with multiple-testing correction (BH/Bonferroni) |
| Finding-to-plan handoff | Promote any exploratory finding into a research plan |
| Persistent workspaces | SQLite-backed projects that survive restarts |
| Timeline tracking | Chronological activity log for every project action |
| Publication-ready tables | Academic regression tables with *** significance notation |
| Academic figures | Coefficient plot, residual, actual vs predicted, heatmap, stability chart |
| DOCX export | Editable Word documents with cover page, tables, figures |
| LaTeX export | Standalone .tex with tables/, figures/, appendix/ directories |
| Methodology appendix | Auto-generated methodology, variable selection, limitations |
| Reproducibility appendix | Dataset checksum, transformation log, software versions |
| Demo project | One-click sample dataset with World Bank panel data |
| Global index pages | Browse all datasets, analyses, and reports across the workspace |

---

## Architecture

```
Upload → Profile → Variable Selection → Transformation → Model Run → Results
       ↘ Discovery → Screening → Specs → Correction → Findings → Plan
       ↘ Project Workspace → Datasets → Analyses → Timeline → Export Bundle
```

**Separation of concerns:**
- `app/services/` — pure data functions (profiling, structure detection, transformations)
- `app/analysis/` — statistical computation wrappers (OLS, panel, diagnostics)
- `app/api/` — thin HTTP routing, no business logic
- `app/schemas/` — Pydantic models shared between layers
- `app/storage/` — SQLite persistence + in-memory cache
- `app/reports/` — publication export generators (tables, figures, DOCX, LaTeX)

---

## Technology Stack

**Backend:**
- Python 3.12, FastAPI, Pydantic v2, pydantic-settings
- pandas, numpy, scipy
- statsmodels (OLS, diagnostics), linearmodels (panel regression)
- SQLAlchemy 2.x (SQLite persistence)
- python-docx (DOCX export), matplotlib (figures)
- openpyxl (Excel support)
- pytest, httpx

**Frontend:**
- Next.js 16, React 19, TypeScript 5
- Tailwind CSS v4, Recharts v3
- lucide-react

**Infrastructure:**
- Docker, Docker Compose
- SQLite (file-based, zero configuration)

---

## Repository Structure

```
ai-econometrics-copilot/
├── backend/
│   ├── app/
│   │   ├── analysis/       # OLS, panel models, diagnostics, discovery, recommender
│   │   ├── api/            # REST endpoints: datasets, analyses, projects, onboarding
│   │   ├── core/           # config, errors, logging
│   │   ├── reports/        # academic tables, figures, DOCX, LaTeX, appendix
│   │   ├── schemas/        # Pydantic models
│   │   ├── services/       # profiling, structure detection, transformations
│   │   └── storage/        # SQLite models, repositories, database engine
│   ├── tests/              # 310 tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                # Next.js pages (incl. /quick-analyze and index pages)
│   ├── components/         # UI components (modeling, results, projects, onboarding)
│   ├── lib/                # API client, i18n (EN / zh-CN), utils
│   ├── types/              # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── desktop/
│   ├── scripts/            # PowerShell / batch build helpers
│   └── src-tauri/          # Tauri 2.x Rust shell (menu, sidecar lifecycle, IPC)
├── installer_downloader/   # One-line PowerShell installer downloader
├── sample_data/            # World Bank panel sample dataset
├── scripts/                # start, stop, reset scripts (sh + ps1)
├── docs/                   # architecture, API, econometric rules, bilingual guides
├── docker-compose.yml
├── Makefile
└── .env.example
```

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

## Recommendation Scoring

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

## Example Workflow

1. Open the app — first-time users see a welcome card with workflow steps
2. Click **Try Sample Dataset** to create a demo project with World Bank data
3. Review the dataset profile — panel detected (20 entities × 15 periods)
4. Click **Configure & Run Model →**
5. Variable roles are pre-filled: `gdp_per_capita` as outcome, `internet_users` as explanatory
6. Optionally apply log transform for right-skewed variables
7. Select **Fixed Effects** (recommended for panel data)
8. Enable clustered standard errors by entity
9. Click **Run Analysis →**
10. View coefficient table, significance stars, diagnostics, residual plots
11. Compare specifications via **Compare Models**
12. Generate a research report or publication-ready export (DOCX/LaTeX)
13. Export reproducible JSON artifact

---

## Environment Variables

All backend variables use the `ECOPILOT_` prefix. See [`.env.example`](.env.example) for a complete list.

| Variable | Default | Purpose |
|---|---|---|
| `ECOPILOT_DATABASE_URL` | `sqlite:///./data/ai_econometrics.db` | Database connection |
| `ECOPILOT_DATA_DIR` | `data` | Base data directory |
| `ECOPILOT_UPLOAD_DIR` | `data/uploads` | Uploaded file storage |
| `ECOPILOT_ARTIFACT_DIR` | `data/artifacts` | Generated artifact storage |
| `ECOPILOT_CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed CORS origins |
| `ECOPILOT_MAX_UPLOAD_SIZE_BYTES` | `52428800` (50 MB) | Upload size limit |
| `ECOPILOT_LOG_LEVEL` | `INFO` | Logging level |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api` | Frontend API endpoint |

---

## Running Tests

```bash
# Backend (310 tests)
cd backend
source .venv/bin/activate
python -m pytest -q

# Frontend type check + lint
cd frontend
npx tsc --noEmit
npm run lint
npm run build

# Desktop (Rust unit tests)
cd desktop/src-tauri
cargo test
```

Or with Make:
```bash
make test
```

---

## Docker Deployment

```bash
docker compose up --build -d
```

- Backend: port 8000 with health check (`/health`)
- Frontend: port 3000 with health check
- Data persists in `ai_econometrics_data` named volume
- Frontend waits for backend to be healthy before starting

```bash
docker compose down      # stop, keep data
docker compose down -v   # stop and delete all data
```

---

## Reproducibility Design

Every analysis stores a complete record:
- Original dataset metadata and SHA-256 checksum
- Every transformation applied (with row counts before/after)
- Exact model formula and configuration
- All coefficients, standard errors, p-values, and diagnostics
- Software library versions and timestamps

Export via `GET /api/analyses/{id}/export/json` or as a project ZIP bundle.

---

## Publication Export

Generate publication-ready documents from any analysis, comparison, or report:

- **DOCX** — Times New Roman, formatted tables, embedded figures, cover page
- **LaTeX** — Standalone .tex with proper escaping, compiles with `pdflatex`
- **Markdown** — Academic-style tables with significance stars
- **JSON** — Structured artifact for programmatic access

PDF export is a documented placeholder — DOCX and LaTeX are fully functional alternatives.

---

## Standalone Windows Desktop Application

A standalone Windows desktop version is available — no Docker, Python, Node.js, or browser required.

**For end users:**
1. Download the installer (`.msi` or `Setup.exe`) from Releases
2. Install the application
3. Open **AI Econometrics Copilot** from the Start Menu
4. All data stays on the local computer in `%LOCALAPPDATA%\AI Econometrics Copilot\`

**For developers building the installer:**
```powershell
# Prerequisites: Rust, Node.js 18+, Python 3.10+
.\desktop\scripts\build-desktop.ps1
```

See [`desktop/README.md`](desktop/README.md) for full build instructions.

**Desktop technology:** Tauri 2.x + embedded FastAPI sidecar (PyInstaller) + static Next.js frontend.

**Not yet available:**
- macOS or Linux desktop packages
- Automatic updates
- Code signing (unsigned builds trigger Windows SmartScreen warnings)

---

## Quick Analyze

**Quick Analyze** is a four-stage guided workflow that takes you from a raw data file to a full econometric result — no statistics background required.

**How to use:**
1. On the home page, click **Analyse My Excel / CSV** (works in both desktop and browser)
2. Upload a CSV or Excel file, optionally enter a research question
3. Review the auto-generated plan (recommended model, dependent and independent variables)
4. Confirm to run the analysis and read the plain-language summary

**What it does automatically:**
- Detects data structure (panel / cross-sectional / time-series)
- Recommends an appropriate model (OLS, Fixed Effects, Random Effects, Log-OLS)
- Generates a jargon-free plain-language interpretation
- Computes diagnostics (VIF, Breusch-Pagan, Jarque-Bera)

**Note:** Quick Analyze provides association analysis. For causal inference, use the Advanced Workflow (Projects).

Full guide: [`docs/quick-analyze.md`](docs/quick-analyze.md)

---

## Interface Language (English / 中文)

The UI ships with a built-in language switcher (🌐 button in the page header):

- **English** and **Simplified Chinese (简体中文)** dictionaries
- Choice persists across sessions (localStorage)
- Browsers with a Chinese system language default to Chinese automatically
- Works in both the web app and the Windows desktop app

Implementation: client-side React context ([`frontend/lib/i18n.tsx`](frontend/lib/i18n.tsx)) — compatible with the static export required by the Tauri desktop build.

---

## Current Limitations

- Single-user, local SQLite storage — no multi-user or cloud sync
- No authentication or authorization
- No arbitrary formula editor (variables selected through UI)
- PDF export requires Pango/Cairo native libraries — DOCX and LaTeX available as alternatives
- Hausman test uses pseudo-inverse — may report unavailable for near-singular matrices
- Two-way fixed effects may absorb variables collinear with entity/time dummies (reported transparently)
- Windows desktop build is unsigned — SmartScreen warnings expected

---

## Roadmap

| Phase | Feature | Status |
|---|---|---|
| Phase 1 | Data upload, profiling, structure detection | Complete |
| Phase 2 | Variable configuration, data transformations | Complete |
| Phase 3 | Regression execution, econometric diagnostics | Complete |
| Phase 4 | Multi-model comparison, recommendation, reports | Complete |
| Phase 5 | Research planning, absorbed variable transparency | Complete |
| Phase 6 | Constrained exploratory relationship discovery | Complete |
| Phase 7 | Persistent research workspaces | Complete |
| Phase 8 | Publication-ready reporting and academic export | Complete |
| Phase 9 | Onboarding, one-click startup, documentation | Complete |
| Phase 10 | Standalone Windows desktop application | Complete |
| Phase 11 | Quick Analyze, desktop polish, bilingual UI, documentation | In Progress |
| Phase 12 | Advanced econometric models and causal workflows | Future |

---

## Causal Language Disclaimer

> This analysis identifies statistical associations and does not establish causal effects unless additional identification assumptions are justified.

---

## License

MIT
