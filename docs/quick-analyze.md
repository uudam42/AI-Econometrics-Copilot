# Quick Analyze

[中文版](quick-analyze.zh-CN.md)

Quick Analyze is a four-stage guided workflow that takes you from a raw data file to a full econometric analysis result without requiring any prior knowledge of statistics or econometrics.

---

## When to use Quick Analyze

| Situation | Recommendation |
|-----------|---------------|
| You have an Excel or CSV file and want an instant result | Quick Analyze |
| You have a specific research question | Quick Analyze (enter your question at upload) |
| You need full control over model specification | Advanced Workflow (Projects) |
| You want to compare multiple models | Advanced Workflow (Projects) |

---

## The four stages

### Stage 1 — Upload

Drag and drop your file, or click **Choose file** to open a file picker.

- Supported formats: `.csv`, `.xlsx`, `.xls`
- Maximum recommended size: 50 MB
- The file is stored locally; nothing is sent to external servers

Optionally enter a **research question** (e.g. "Does GDP growth affect unemployment?") to help the AI select an appropriate model.

Click **Upload & Analyse** to proceed.

### Stage 2 — Planning (automatic)

The system profiles your data and generates an analysis plan:

- Detects panel vs. cross-sectional vs. time-series structure
- Identifies numeric and categorical columns
- Selects a recommended model (OLS, Fixed Effects, Random Effects, or Log-OLS)
- Proposes a dependent variable and a set of independent variables

This stage runs automatically in a few seconds.

### Stage 3 — Review & Confirm

Inspect the proposed plan before committing:

| Field | What it means |
|-------|---------------|
| **Recommended model** | The statistical model the AI selected |
| **Dependent variable** | The outcome you are trying to explain |
| **Independent variables** | The factors used to explain the outcome |
| **Analysis intent** | Exploratory or causal |

You can change the **dependent variable** and **independent variables** using the dropdowns. The recommended model cannot be changed here; use the Advanced Workflow for full control.

Click **Confirm & Run Analysis** to proceed.

### Stage 4 — Results

Results are displayed in three sections:

#### Plain-English summary

A non-technical explanation of what the analysis found, including:
- Whether the independent variables collectively explain the outcome
- Which specific variables have a statistically significant effect
- Any data quality warnings (multicollinearity, heteroscedasticity, non-normality)

#### Diagnostic table

| Diagnostic | Threshold | Meaning |
|------------|-----------|---------|
| R² | higher is better | Proportion of variance explained |
| VIF (max) | < 10 (warning ≥ 5) | Multicollinearity |
| Breusch-Pagan p-value | > 0.05 good | Homoscedasticity test |
| Jarque-Bera p-value | > 0.05 good | Normality of residuals |

#### Causal interpretation warning

If the analysis intent is **exploratory**, a yellow banner reminds you that correlation does not imply causation. Causal claims require an appropriate study design (natural experiment, IV, DiD, etc.).

---

## Next actions after results

From the results page you can:

- **Export results** — download a Word, Markdown, or PDF report
- **Open in Projects** — open the analysis in the full Projects workflow for deeper investigation
- **Start over** — upload a different file

---

## Supported models

| Model | When it is chosen |
|-------|------------------|
| OLS (Ordinary Least Squares) | Cross-sectional data, continuous outcome |
| Log-OLS | Cross-sectional, skewed outcome (log-transform applied) |
| Fixed Effects (FE) | Panel data, unit-specific unobserved heterogeneity |
| Random Effects (RE) | Panel data, random individual effects |

The model is selected automatically based on data structure detection. You can override the choice in the Advanced Workflow.

---

## Troubleshooting

**Upload fails with "Unsupported file type"**
Only `.csv`, `.xlsx`, and `.xls` files are accepted. Convert your file to one of these formats.

**Planning stage shows "Could not detect structure"**
The dataset must have at least two numeric columns. Ensure column headers are in the first row.

**Results show very low R²**
The chosen independent variables may not explain the dependent variable well. Try the Advanced Workflow to experiment with different model specifications.

**"Potential multicollinearity" warning**
Two or more independent variables are highly correlated. Consider removing one of the correlated variables.

---

## Frequently asked questions

**Can I use Quick Analyze for causal inference?**
Quick Analyze provides correlation-based analysis and will display a warning when causal interpretation is attempted. True causal inference (DiD, IV, RD) is available in the Advanced Workflow.

**Is my data uploaded to the cloud?**
No. All data is processed locally on your computer. Nothing is sent to external servers.

**Can I re-run Quick Analyze on the same file?**
Yes. Each upload creates a new session. Previous sessions are visible in Projects.
