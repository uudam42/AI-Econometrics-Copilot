# User Guide

[中文版](user-guide.zh-CN.md)

## Overview

AI Econometrics Copilot guides you through a structured econometric research workflow:

1. **Upload** — Import your dataset (CSV or Excel)
2. **Profile** — Automatic data quality and structure analysis
3. **Plan** — Natural language research question → recommended approach
4. **Configure** — Select variables, roles, and transformations
5. **Run** — Execute regressions with full diagnostic output
6. **Compare** — Side-by-side model comparison with recommendation
7. **Report** — Generate reproducible reports and publication exports

---

## Projects

### Creating a Project

1. Navigate to **Projects** → **New Project**
2. Fill in title, description, and research question
3. Add tags for organization (e.g., `panel-data`, `trade`)
4. Click **Create**

### Demo Project

Click **Try Sample Dataset** on the home page or projects page. This creates a project with the World Bank panel dataset pre-loaded and a research question pre-filled.

### Project Workspace

Each project has:
- **Overview** — project metadata, default dataset, quick links
- **Datasets** — upload and manage datasets within the project
- **Timeline** — chronological log of all project activity
- **Exports** — publication-ready document generation

---

## Datasets

### Supported Formats

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- Maximum size: 50 MB

### Data Profiling

After upload, the system automatically:
- Counts rows and columns
- Infers column types (numeric, categorical, date, identifier)
- Detects missing values, outliers, and skewness
- Identifies panel, time-series, or cross-sectional structure
- Suggests appropriate transformations

### Structure Detection

The detector identifies:
- **Panel data** — multiple entities observed over multiple time periods
- **Time series** — single entity over time
- **Cross-sectional** — multiple entities at one point in time

Detection uses data patterns, not column names alone.

---

## Research Planning

1. Navigate to a dataset's **Research Planning** page
2. Type a research question in natural language (e.g., "How does trade openness affect GDP growth?")
3. The system proposes:
   - Dependent and independent variables
   - Recommended model types based on data structure
   - Suggested transformations
4. Review and approve the plan, or modify as needed
5. An approved plan can guide the modeling step

**Causal language detection:** If your question uses causal language ("causes", "affects", "impacts"), the system reframes it as an association and adds an explicit warning.

---

## Variable Configuration

### Variable Roles

| Role | Purpose |
|---|---|
| Dependent | Outcome variable (Y) |
| Primary IV | Main explanatory variable of interest |
| Controls | Additional regressors to reduce omitted variable bias |
| Entity ID | Panel entity identifier (country, firm, etc.) |
| Time | Time period identifier (year, quarter, etc.) |

### Pre-filling

The system pre-fills variable roles based on column types and data structure. You can override any assignment.

### Transformations

Available transformations:
- **Log** — for right-skewed variables (requires positive values)
- **Winsorize** — cap extreme values at specified percentiles
- **Standardize** — zero mean, unit variance
- **Imputation** — fill missing values (mean, median, or forward-fill)
- **Drop missing** — remove rows with missing values
- **Drop duplicates** — remove duplicate rows

---

## Model Execution

### Available Models

| Model | When to Use |
|---|---|
| OLS | Cross-sectional data, baseline specification |
| Robust OLS (HC1) | When Breusch-Pagan indicates heteroskedasticity |
| Pooled OLS | Panel data without entity effects |
| Fixed Effects | Panel data with time-invariant unobserved heterogeneity |
| Random Effects | Panel data when entity effects are uncorrelated with regressors |
| Two-Way FE | Panel data with both entity and time effects |

### Diagnostics

Every analysis includes:
- **VIF** — variance inflation factor for multicollinearity (warning > 5, severe > 10)
- **Breusch-Pagan** — heteroskedasticity test
- **Jarque-Bera** — residual normality
- **Durbin-Watson** — first-order autocorrelation
- **Hausman test** — FE vs RE selection (panel models only)

### Results Dashboard

After running an analysis:
- Coefficient table with standard errors, t-statistics, p-values, and significance stars
- Coefficient plot (forest plot)
- Residual vs fitted values plot
- Actual vs predicted scatter
- Correlation heatmap
- Model fit metrics (R², adjusted R², F-statistic)

---

## Model Comparison

1. Navigate to **Compare Models** from any dataset page
2. Select up to 6 model types to compare
3. The system runs all models on the same variables and presents:
   - Side-by-side coefficient tables
   - Fit metrics comparison (R², AIC, BIC)
   - Coefficient stability view — how the primary IV behaves across specifications
   - Transparent recommendation with multi-criteria scoring

### Recommendation Criteria

| Criterion | Weight |
|---|---|
| Structural Compatibility | 25% |
| Hausman Test | 20% |
| Heteroskedasticity Robustness | 15% |
| Model Fit | 15% |
| Parsimony | 10% |
| Sample Size | 10% |
| Estimation Success | 5% |

---

## Exploratory Discovery

For hypothesis generation (not confirmation):

1. Navigate to **Explore Relationships** from a dataset page
2. The system runs a bounded specification search:
   - Screens potential variables
   - Tests multiple specifications
   - Applies multiple-testing correction (Benjamini-Hochberg or Bonferroni)
   - Assesses stability across specifications
3. Findings are scored on 6 dimensions (corrected support, stability, direction consistency, data quality, diagnostics, fit)
4. Promote any finding to a theory-driven research plan with one click

---

## Reports and Exports

### Research Report

Generate a deterministic narrative report from any analysis:
- Executive summary
- Methodology section
- Results with formatted coefficient tables
- Diagnostic interpretation
- Limitations and caveats
- Available in Markdown, HTML, and JSON

### Publication Export

Generate academic documents:
- **DOCX** — Word document with cover page, Times New Roman, formatted tables, embedded figures
- **LaTeX** — Standalone .tex with tables/, figures/, appendix/ directories
- **Markdown** — Academic tables with *** significance notation
- **JSON** — Structured export for programmatic use

Each export includes:
- Publication-ready regression tables
- Academic figures (coefficient plot, residuals, correlation heatmap)
- Methodology appendix
- Reproducibility appendix (dataset checksum, software versions, transformation log)

### Reproducibility

Every analysis artifact includes:
- Complete model configuration
- Dataset SHA-256 checksum
- Transformation log with row counts
- Software library versions
- Timestamp

---

## Keyboard and Navigation

- **Home** → dataset upload and profiling
- **Projects** → project list and workspace
- Each project page has links to datasets, timeline, and exports
- Analysis results link to comparison and report generation
