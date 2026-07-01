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

## Phase 4 — Rule-based report generation and model comparison

- [ ] `ModelScoringService`: compare a bounded set of models on adj. R², AIC/BIC,
      VIF, heteroskedasticity, diagnostics summary
- [ ] Rule-driven narrative report generator (no external LLM) covering dataset
      summary, cleaning steps, formula, coefficient interpretation, diagnostics,
      causal-language guard
- [ ] Report export: HTML, Markdown
- [ ] Side-by-side model comparison table

## Phase 5 — AI planning layer

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
