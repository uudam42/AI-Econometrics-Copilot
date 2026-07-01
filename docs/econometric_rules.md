# Econometric Rules

This document is the human-readable counterpart to
`backend/app/analysis/econometric_rules.py` and `backend/app/core/config.py`.
If a threshold changes, update both the code and this file in the same change.

## When to suggest a log transform

A numeric column is suggested for a **natural log transform** when:

- All observed values are strictly positive, **and**
- Sample skewness (`scipy.stats.skew`) exceeds `high_skew_threshold` (default **1.0**)

Rationale: log transforms stabilize variance and reduce the influence of large
values for positive, right-skewed economic variables (income, GDP, prices).
They are not applied automatically — this is a suggestion surfaced in the
Data Quality Report; the user chooses whether to apply it.

If a column is skewed but contains zero or negative values, log transform is
not suggested (undefined for ≤ 0); **winsorization** is suggested instead.

## Outlier detection

Two methods are computed, in this priority order:

1. **IQR method** (primary): values outside `[Q1 - k·IQR, Q3 + k·IQR]` where
   `k = outlier_iqr_multiplier` (default **1.5**).
2. **Z-score method** (fallback): used only when IQR is degenerate (IQR = 0,
   e.g. many repeated values) but the column still has non-zero variance.
   Threshold: `|z| > outlier_zscore_threshold` (default **3.0**).

The report always states which method produced the reported outlier count.

## When to suggest fixed effects

Fixed effects (entity, or two-way entity+time) are suggested when the
structure detector identifies **panel data**: more than one entity, observed
over more than one time period (see `should_recommend_fixed_effects` in
`econometric_rules.py`). Two-way fixed effects are additionally suggested for
common cross-entity shocks (e.g. macroeconomic events affecting all countries
in a given year).

## When to suggest robust / clustered standard errors

Robust (heteroskedasticity-consistent) standard errors are suggested when the
**Breusch-Pagan test** p-value is below `heteroskedasticity_alpha` (default
**0.05**). For panel models, standard errors clustered by entity are the
default recommendation once heteroskedasticity or within-entity correlation is
suspected — this is a recommendation surfaced to the user, never applied
silently.

## VIF thresholds

Variance Inflation Factor risk levels (`vif_risk_level` in
`econometric_rules.py`):

| VIF | Risk level | Guidance |
|---|---|---|
| < 5 | low | No action needed |
| 5 – 10 | moderate | Flag possible multicollinearity; consider dropping/combining variables |
| ≥ 10 | severe | Strong multicollinearity; coefficients likely unstable |

The system never auto-drops a variable for collinearity — it only surfaces
the risk level and the affected variable pair(s).

## Hausman test applicability

The Hausman test is only run when **both** fixed effects and random effects
models can be estimated for the same specification. If random effects
estimation fails (e.g. non-panel data, insufficient within/between variation),
the Hausman test is skipped and the report states why, rather than silently
omitting it.

## Panel balance

A panel is reported as **balanced** when every entity has the same number of
observed time periods as every other entity (`group_sizes == time_period_count`
for all entities); otherwise it is reported **unbalanced**. Both balanced and
unbalanced panels are supported by fixed/random effects estimation in later
phases — balance only affects interpretation, not eligibility.

## Causal interpretation limits

The system never asserts causality. Report language always uses "is
associated with" / "suggests a relationship with" / "should not be
interpreted as causal," and every report includes the mandatory disclaimer:

> This analysis identifies statistical associations and does not establish
> causal effects unless additional identification assumptions are justified.

Exploratory findings from the future Discovery Engine must additionally be
labeled `Exploratory finding`, `Not causal evidence`, and
`Requires theory-driven validation` (see `discovery_engine.py`).
