# Development Plan

## Phase 1 — Data upload and profiling (this build)

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
- [x] Backend unit tests (pytest)
- [x] Reserved interfaces for the future AI planning layer (mocked)

## Phase 2 — Model execution and diagnostics

- [ ] Variable role selection UI (dependent/independent/controls/entity/time)
      with user override of rule-based suggestions
- [ ] Cleaning & transformation execution (log, winsorize, standardize,
      median/mean imputation, drop duplicates/missing) + transformation log
- [ ] OLS and robust-SE OLS via `statsmodels`
- [ ] Pooled OLS, entity FE, random effects, two-way FE via `linearmodels`
- [ ] Clustered standard errors by entity
- [ ] Diagnostics: VIF, Breusch-Pagan, Durbin-Watson, residual normality,
      Hausman test (when both FE and RE are estimable)
- [ ] `POST /api/models/run`, `GET /api/models/{id}`,
      `GET /api/models/{id}/diagnostics`

## Phase 3 — Report generation and model comparison

- [ ] `ModelScoringService`: compare a bounded set of user/system-selected
      models on adjusted R², AIC/BIC, VIF, heteroskedasticity, diagnostics
- [ ] Rule-driven explanation generator (no external LLM call) covering
      dataset summary, cleaning steps, model formula, coefficient
      interpretation, diagnostics summary, limitations, causal-language guard
- [ ] Report export: HTML, Markdown, JSON artifact
      (`GET /api/models/{id}/report`, `/export/json`)
- [ ] End-to-end demo using `sample_data/world_bank_panel_sample.xlsx`

## Phase 4 — AI planning layer

- [ ] Wire `variable_semantics.py` to a real semantic-role suggestion model
      (still rule-checkable; suggestions only, never auto-applied)
- [ ] Wire `model_planner.py` to propose a small, ranked set of candidate
      specifications for user review, replacing the current mock

## Phase 5 — Autonomous Econometric Discovery Engine

- [ ] Implement `discovery_engine.py`: bounded candidate dependent-variable
      discovery, plausible independent/control filtering, limited candidate
      model generation, multiple-testing correction
- [ ] Every finding labeled `Exploratory finding`, `Not causal evidence`,
      `Requires theory-driven validation`
- [ ] Explicitly no unconstrained/exhaustive search over all variable
      combinations
