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

## Phase 5 — Natural-language research question mapping and AI planning layer ✅ Completed

- [x] Accept a user-typed research question (e.g. "Is internet penetration
      associated with GDP per capita?") and map it to candidate variables
- [x] Research question parser: normalize questions, detect causal vs.
      association vs. exploratory intent via keyword patterns
- [x] Economics synonym dictionary: 20+ semantic concepts (GDP, trade,
      education, inflation, etc.) with extensible token-based matching
- [x] Dataset-aware variable matcher: column typing + synonym dictionary +
      token overlap scoring → CandidateVariable suggestions with confidence
      and evidence
- [x] Research planner: orchestrate parser + matcher + structure detection →
      ResearchPlan with candidate variables, transformations, models, ambiguities
- [x] Causal language detection and warning: questions using "cause", "affect",
      "impact", "lead to" flagged with explicit disambiguation
- [x] Suggested transformations: log transform recommended for skewed positives
- [x] Suggested models: rule-based, dataset-structure-aware model ranking
      (FE/RE/Two-Way FE for panel, OLS/Robust for cross-section)
- [x] Plan registry with thread-safe in-memory storage
- [x] `POST /api/plans/generate`, `GET /api/plans/{id}`,
      `POST /api/plans/{id}/approve`, `GET /api/plans/{id}/export/json`
- [x] Absorbed variable transparency: Two-Way FE `drop_absorbed` now reports
      which variables were absorbed, why, and whether the primary IV is affected
- [x] Frontend: `/datasets/[datasetId]/plan` page with ResearchQuestionForm,
      ResearchPlanOverview, CandidateVariableCard, AmbiguityPanel,
      SuggestedModelList, CausalWarningBanner
- [x] "Research Planning →" button added to home page
- [x] 156 backend pytest tests passing (115 Phase 1–4 + 41 Phase 5)

## Phase 6 — Constrained Exploratory Relationship Discovery ✅ Completed

- [x] Two discovery modes: Guided (user specifies outcome) and Open (system selects)
- [x] Variable eligibility screening: entity/time/ID exclusion, constant detection,
      missing rate, near-duplicate detection, quality scoring
- [x] Bounded specification generation: bivariate OLS, controlled robust OLS,
      log-DV variant, panel FE, two-way FE — at most 5 spec types per predictor
- [x] Configurable hard limits: max 30 specs (capped at 100), max 5 outcomes,
      max 10 predictors/outcome, max 4 controls/model
- [x] Statistical execution: OLS, Robust OLS (HC1), PanelOLS (entity FE),
      PanelOLS (two-way FE) with absorbed variable rejection
- [x] Multiple-testing correction: Benjamini-Hochberg FDR (step-up procedure),
      Bonferroni, or no correction (with explicit warning)
- [x] Stability assessment: direction consistency, significance consistency,
      coefficient range, 4-level stability label
- [x] Multi-criteria weighted scoring (6 dimensions): corrected support (25%),
      stability (20%), direction consistency (15%), data quality (15%),
      diagnostics (15%), model fit (10%)
- [x] Support levels: strong (≥70), moderate (≥50), weak (≥30),
      insufficient, not suitable
- [x] Every finding labeled: "Exploratory Finding / Not Causal Evidence /
      Requires Theory-Driven Validation"
- [x] Finding-to-plan handoff: any exploratory finding can be promoted to a
      theory-driven research plan via the existing planning pipeline
- [x] Discovery registry with thread-safe in-memory storage
- [x] `POST /api/discovery/run`, `GET /api/discovery/{id}`,
      `GET /api/discovery/{id}/findings`, `GET /api/discovery/{id}/export/json`,
      `POST /api/discovery/{id}/findings/{fid}/create-plan`
- [x] Frontend: `/datasets/[datasetId]/discover` page with
      DiscoveryConfigurationPanel, EligibilitySummary, ExploratoryFindingsTable,
      FindingScoreCard, MultipleTestingPanel, StabilityPanel, FindingWarnings,
      InvestigateFindingButton
- [x] "Explore Relationships →" button added to home page
- [x] 201 backend pytest tests passing (156 Phase 1–5 + 45 Phase 6)
- [x] TypeScript type-checks pass, Next.js production build succeeds

## Phase 7 — Persistent Research Workspaces and Reproducible Project Storage ✅ Completed

- [x] SQLite persistence via SQLAlchemy 2.x with WAL journal mode
- [x] Repository pattern: in-memory cache + write-through to SQLite
- [x] 8 SQLAlchemy table models: ProjectRow, DatasetRow, AnalysisRow,
      ComparisonRow, PlanRow, ReportRow, DiscoveryRow, TimelineEventRow
- [x] ProjectRepository: create, get, list_all (exclude archived by default),
      update, delete (protected + forced), get_timeline, get_artifacts
- [x] DatasetRepository: create, get (lazy DataFrame reload from disk),
      exists, list_by_project, update_profile, set_project, clear_cache
- [x] AnalysisRepository, ComparisonRepository, PlanRepository,
      ReportRepository, DiscoveryRepository — all with cache + SQLite
- [x] SHA-256 checksums for uploaded dataset files
- [x] Timeline events auto-recorded on artifact creation
- [x] Project domain model: draft → active → archived lifecycle
- [x] Project API endpoints: POST/GET/PATCH/DELETE /api/projects,
      GET timeline, GET artifacts, POST datasets/upload,
      GET export/json, GET export/bundle (ZIP with optional raw data)
- [x] Backward compatibility: old registry modules re-export from repositories,
      existing endpoints work without project_id
- [x] FastAPI lifespan context manager for DB initialization on startup
- [x] Thread-safe repositories with threading.Lock for cache access
- [x] Environment configuration: ECOPILOT_DATABASE_URL, DATA_DIR,
      UPLOAD_DIR, ARTIFACT_DIR — with `.env.example`
- [x] Autouse pytest fixture: temp SQLite database per test, reset engine,
      clear all caches
- [x] Frontend: TypeScript types (project.ts), 7 components
      (ProjectCard, ProjectForm, ProjectOverview, ProjectTimeline,
      ArtifactHistoryTable, ProjectDatasetList, ProjectExportActions,
      ProjectStatusBadge)
- [x] Frontend: 5 pages (projects list, new project, project detail,
      project datasets, project timeline)
- [x] Frontend: 12 API functions added to api.ts
- [x] "Projects" navigation link added to home page
- [x] README.md and README.zh-CN.md updated with Phase 7 features
- [x] 229 backend pytest tests passing (201 Phase 1–6 + 28 Phase 7)
- [x] TypeScript type-checks pass, Next.js production build succeeds

## Phase 8 — Publication-Ready Reporting and Advanced Academic Export ✅ Completed

- [x] Academic regression table generators: single-model, multi-model comparison,
      coefficient stability, descriptive statistics, variable definitions,
      diagnostic summary — all with *** / ** / * significance notation and
      causal language disclaimer
- [x] Publication-ready figure generators via matplotlib (not seaborn):
      coefficient plot with 95% CI, residual vs fitted, actual vs predicted,
      correlation heatmap, coefficient stability chart — PNG output
- [x] DOCX export via python-docx: genuinely editable Word documents with
      cover page, Times New Roman, professional table formatting, embedded
      figures with captions, and causal disclaimer
- [x] LaTeX export: standalone .tex + tables/ + figures/ + appendix/ +
      README.md — compiles with pdflatex using booktabs, graphicx, hyperref
- [x] PDF export: documented placeholder — WeasyPrint requires native
      Pango/Cairo libraries not reliably available; clear error message
- [x] Methodology appendix: auto-generated variable selection, model
      specification, limitations section
- [x] Reproducibility appendix: dataset SHA-256 checksum, transformation log,
      model configuration, software versions — all deterministic
- [x] Publication export orchestration service: coordinates table generators,
      figure generators, appendix, and format-specific exporters
- [x] PublicationExportRow persistence in SQLAlchemy with cache + write-through
- [x] Publication export API endpoints: POST /generate, GET /{id},
      GET /{id}/download/{format}, GET /{id}/export/json,
      GET /by-project/{project_id}
- [x] Timeline event integration: publication_export_created events
- [x] Frontend: TypeScript types (publication_export.ts), 4 API functions,
      4 components (PublicationExportForm, ExportDownloadActions,
      PublicationExportStatus, PublicationExportList), 2 pages
      (project exports, export detail)
- [x] "Publication Exports →" link on project detail page
- [x] Backward compatibility: existing report endpoints unchanged
- [x] README.md and README.zh-CN.md updated with Phase 8 features
- [x] 267 backend pytest tests passing (229 Phase 1–7 + 38 Phase 8)
- [x] TypeScript type-checks pass, Next.js production build succeeds

## Phase 9 — Onboarding, One-Click Startup, and Documentation (In Progress)

- [x] Docker one-command startup: docker-compose.yml with named volumes,
      health checks, CORS and env configuration, .dockerignore files
- [x] Backend and frontend Dockerfiles with health checks
- [x] Local startup scripts: start-local.sh, stop-local.sh, reset-local-data.sh
      (bash) + start-local.ps1, stop-local.ps1, reset-local-data.ps1 (PowerShell)
- [x] Dependency detection (Python 3.10+, Node 18+) with smart install caching
- [x] Makefile with start, stop, test, docker-up, docker-down targets
- [x] Demo project endpoint: POST /api/onboarding/demo-project creates a
      project with World Bank sample dataset pre-loaded
- [x] Onboarding status endpoint: GET /api/onboarding/status reports
      has_projects, has_demo, sample_data_available
- [x] Frontend WelcomeCard: workflow steps, "Try Sample Dataset" button,
      "Create New Project" button
- [x] Projects page empty state with demo project option
- [x] Frontend onboarding types, API functions
- [x] .env.example with all ECOPILOT_ variables documented
- [x] Comprehensive English README rewrite (quick start, Docker, features,
      architecture, tech stack, repo structure, models, diagnostics,
      recommendation scoring, workflow, env vars, tests, deployment,
      reproducibility, publication export, limitations, roadmap)
- [x] Comprehensive Chinese README (structural mirror)
- [x] Bilingual docs: quickstart, user-guide, troubleshooting, deployment
- [x] 274 backend pytest tests passing (267 Phase 1–8 + 7 onboarding)
- [x] TypeScript type-checks pass, Next.js production build succeeds

## Phase 10 — Advanced Econometric Models and Causal Identification Workflows

- [ ] Instrumental variables (2SLS) support
- [ ] Difference-in-differences estimation
- [ ] Regression discontinuity design
- [ ] Synthetic control method
- [ ] Causal graph specification and validation
