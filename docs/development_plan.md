# Development Plan

## Phase 1 — Data upload and profiling ✅ Completed

- [x] Monorepo scaffolding (frontend, backend, sample_data, docs)
- [x] FastAPI backend: config, logging, unified error handling
- [x] CSV / Excel upload with validation
- [x] Rule-based column type + role-hint inference
- [x] `DatasetProfiler`: missing values, duplicates, constants, outliers
      (IQR + Z-score), skewness/kurtosis, transformation suggestions
- [x] Rule-driven panel / time-series / cross-sectional structure detection
- [x] Next.js dashboard: overview, column types, data preview, structure,
      missing-value chart, column quality table
- [x] Sample World Bank–style panel dataset
- [x] Backend unit tests (pytest, 23 tests)
- [x] Reserved interfaces for the future AI planning layer (mocked)

## Phase 2 — Variable configuration and transformation execution ✅ Completed

- [x] Variable role selection UI (dependent / primary IV / controls / entity / time)
      with rule-based pre-fill and full user override
- [x] `TransformationPanel`: drop duplicates, drop missing rows, median/mean
      imputation, winsorize (configurable percentiles), log transform (new col),
      standardize (z-score, new col) + transformation log
- [x] `POST /api/datasets/{id}/transform` — preview transformation on stored copy

## Phase 3 — Regression execution and diagnostics ✅ Completed

- [x] OLS and Robust OLS (HC1) via `statsmodels`
- [x] Pooled OLS, Entity Fixed Effects, Random Effects, Two-Way Fixed Effects
      via `linearmodels`
- [x] Clustered standard errors by entity
- [x] Diagnostics: VIF, Breusch-Pagan, Jarque-Bera, Durbin-Watson, Hausman test
- [x] Correlation matrix, descriptive statistics for model variables
- [x] `POST /api/analyses/run`, `GET /api/analyses/{id}`,
      `GET /api/analyses/{id}/diagnostics`, `GET /api/analyses/{id}/report`,
      `GET /api/analyses/{id}/export/json`
- [x] Rule-based model recommendation (no LLM)
- [x] Full analysis results page: coefficient table, coefficient plot (95% CI),
      residual-vs-fitted chart, actual-vs-predicted chart, correlation heatmap,
      diagnostics cards, transformation log
- [x] Reproducible JSON export artifact with software versions
- [x] 76 backend pytest tests (all passing)

## Phase 4 — Multi-model comparison, transparent recommendation, research report ✅ Completed

- [x] Multi-model comparison engine: run up to 6 models on the same variable
      selection and processed dataset; per-model failures captured without
      cancelling the full comparison
- [x] Compatible model filter: panel models marked unavailable when no entity/time
      columns are configured
- [x] Standardized comparison metrics: R², Adj. R², Within/Between/Overall R² (panel),
      AIC, BIC, N, entity/period counts, SE type, VIF summary, Hausman p-value
- [x] Transparent multi-criteria scoring (7 weighted criteria):
      structural compatibility (25%), Hausman guidance (20%), heteroskedasticity
      robustness (15%), model fit (15%), parsimony (10%), sample size (10%),
      estimation success (5%)
- [x] Coefficient stability view: primary IV coefficient across all completed models
      with direction, CI, and significance
- [x] `POST /api/comparisons/run`, `GET /api/comparisons/{id}`,
      `GET /api/comparisons/{id}/export/json`
- [x] Rule-driven research report generator (no LLM): deterministic narrative
      covering 14 required sections — metadata, variables, transformations,
      regression table, coefficient interpretation (including log-dep-var % change),
      diagnostics, causal warning, reproducibility
- [x] Report export: Markdown, self-contained HTML, JSON artifact
- [x] `POST /api/reports/generate`, `GET /api/reports/{id}`,
      `GET /api/reports/{id}/markdown`, `GET /api/reports/{id}/html`,
      `GET /api/reports/{id}/export/json`
- [x] Frontend: `/datasets/[id]/compare`, `/comparisons/[id]`, `/reports/[id]`
- [x] Frontend components: ModelComparisonTable, ModelRecommendationCard,
      ModelScoreBreakdown, CoefficientStabilityTable, ResearchReportViewer,
      ReportMetadataPanel, ReportExportActions
- [x] 115 backend pytest tests passing (76 Phase 1–3 + 39 Phase 4)

## Phase 5 — Natural-language research question mapping and AI planning layer

- [ ] Accept a user-typed research question (e.g. "Is internet penetration
      associated with GDP per capita?") and map it to candidate variables
- [ ] Wire `variable_semantics.py` to a real semantic-role suggestion model
      (suggestions only, never auto-applied)
- [ ] Wire `model_planner.py` to propose a small, ranked set of candidate
      specifications for user review

## Phase 6 — Autonomous Econometric Discovery Engine

- [ ] Implement `discovery_engine.py`: bounded candidate DV discovery,
      plausible IV/control filtering, limited candidate model generation,
      multiple-testing correction
- [ ] Every finding labeled `Exploratory finding / Not causal evidence /
      Requires theory-driven validation`
- [ ] Explicitly no unconstrained/exhaustive search over all variable combinations
