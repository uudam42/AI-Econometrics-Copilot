"""Econometric diagnostics computed by statsmodels, scipy, and linearmodels.

All test statistics are computed by statistical libraries.
This module NEVER fabricates p-values or test outcomes.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson

from app.analysis.econometric_rules import vif_risk_level
from app.schemas.modeling import (
    CorrelationMatrixResult,
    DescriptiveStats,
    DiagnosticTestResult,
    HausmanTestResult,
    VIFResult,
)


def _safe(v) -> float | None:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Descriptive statistics
# ──────────────────────────────────────────────────────────────────────────────

def compute_descriptive_stats(df: pd.DataFrame, columns: list[str]) -> list[DescriptiveStats]:
    results: list[DescriptiveStats] = []
    for col in columns:
        if col not in df.columns:
            continue
        s = df[col]
        num = s.dropna()
        skew = _safe(num.skew()) if pd.api.types.is_numeric_dtype(s) else None
        results.append(DescriptiveStats(
            variable=col,
            count=int(num.count()),
            mean=_safe(num.mean()) if pd.api.types.is_numeric_dtype(s) else None,
            std=_safe(num.std()) if pd.api.types.is_numeric_dtype(s) else None,
            min=_safe(num.min()) if pd.api.types.is_numeric_dtype(s) else None,
            q25=_safe(num.quantile(0.25)) if pd.api.types.is_numeric_dtype(s) else None,
            median=_safe(num.median()) if pd.api.types.is_numeric_dtype(s) else None,
            q75=_safe(num.quantile(0.75)) if pd.api.types.is_numeric_dtype(s) else None,
            max=_safe(num.max()) if pd.api.types.is_numeric_dtype(s) else None,
            missing_count=int(s.isna().sum()),
            skewness=skew,
        ))
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Correlation matrix
# ──────────────────────────────────────────────────────────────────────────────

def compute_correlation_matrix(df: pd.DataFrame, columns: list[str]) -> CorrelationMatrixResult:
    numeric_cols = [c for c in columns if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return CorrelationMatrixResult(variables=[], matrix=[])

    corr = df[numeric_cols].corr()
    matrix: list[list[float | None]] = []
    for row_col in numeric_cols:
        row: list[float | None] = []
        for col_col in numeric_cols:
            row.append(_safe(corr.loc[row_col, col_col]))
        matrix.append(row)

    return CorrelationMatrixResult(variables=numeric_cols, matrix=matrix)


# ──────────────────────────────────────────────────────────────────────────────
# VIF
# ──────────────────────────────────────────────────────────────────────────────

def compute_vif(exog: np.ndarray, variable_names: list[str]) -> list[VIFResult]:
    """Compute VIF for each regressor (excluding the intercept column)."""
    if exog.shape[1] < 2:
        return []

    results: list[VIFResult] = []
    for i, name in enumerate(variable_names):
        if name in ("Intercept", "const", "intercept"):
            continue
        try:
            vif = float(variance_inflation_factor(exog, i))
        except Exception:
            vif = float("nan")

        if math.isnan(vif) or math.isinf(vif):
            risk = "unknown"
            interp = "VIF could not be computed for this variable."
        else:
            risk = vif_risk_level(vif)
            if risk == "severe":
                interp = f"VIF = {vif:.2f}: High multicollinearity warning."
            elif risk == "moderate":
                interp = f"VIF = {vif:.2f}: Moderate multicollinearity may be present."
            else:
                interp = f"VIF = {vif:.2f}: Low multicollinearity concern."

        results.append(VIFResult(
            variable=name,
            vif=vif if not (math.isnan(vif) or math.isinf(vif)) else -1.0,
            risk_level=risk,
            interpretation=interp,
        ))
    return results


# ──────────────────────────────────────────────────────────────────────────────
# Breusch-Pagan heteroskedasticity test
# ──────────────────────────────────────────────────────────────────────────────

def compute_breusch_pagan(resid: np.ndarray, exog: np.ndarray) -> DiagnosticTestResult:
    name = "Breusch-Pagan Heteroskedasticity Test"
    try:
        lm, lm_p, _, _ = het_breuschpagan(resid, exog)
        lm = _safe(lm)
        lm_p = _safe(lm_p)
        if lm_p is not None and lm_p < 0.05:
            interp = (
                f"Evidence of heteroskedasticity was detected (LM statistic = {lm:.3f}, "
                f"p-value = {lm_p:.4f}). Consider using heteroskedasticity-robust "
                "standard errors."
            )
        else:
            interp = (
                f"No significant heteroskedasticity detected "
                f"(LM statistic = {lm:.3f}, p-value = {lm_p:.4f})."
                if lm is not None and lm_p is not None
                else "Breusch-Pagan test inconclusive."
            )
        return DiagnosticTestResult(
            name=name, statistic=lm, p_value=lm_p, interpretation=interp
        )
    except Exception as exc:
        return DiagnosticTestResult(
            name=name,
            statistic=None,
            p_value=None,
            interpretation=f"Test could not be computed: {exc!s}",
            available=False,
            unavailable_reason=str(exc),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Jarque-Bera residual normality test
# ──────────────────────────────────────────────────────────────────────────────

def compute_jarque_bera(resid: np.ndarray) -> DiagnosticTestResult:
    name = "Jarque-Bera Residual Normality Test"
    try:
        jb_stat, jb_p = scipy_stats.jarque_bera(resid)[:2]
        jb_stat = _safe(jb_stat)
        jb_p = _safe(jb_p)
        if jb_p is not None and jb_p < 0.05:
            interp = (
                f"Residuals may not be normally distributed "
                f"(JB statistic = {jb_stat:.3f}, p-value = {jb_p:.4f}). "
                "Note: residual normality is not required for unbiased OLS coefficients, "
                "but may affect small-sample inference."
            )
        else:
            interp = (
                f"No strong evidence against residual normality "
                f"(JB statistic = {jb_stat:.3f}, p-value = {jb_p:.4f})."
                if jb_stat is not None and jb_p is not None
                else "Jarque-Bera test inconclusive."
            )
        return DiagnosticTestResult(
            name=name, statistic=jb_stat, p_value=jb_p, interpretation=interp
        )
    except Exception as exc:
        return DiagnosticTestResult(
            name=name,
            statistic=None,
            p_value=None,
            interpretation=f"Test could not be computed: {exc!s}",
            available=False,
            unavailable_reason=str(exc),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Durbin-Watson autocorrelation statistic
# ──────────────────────────────────────────────────────────────────────────────

def compute_durbin_watson(resid: np.ndarray) -> DiagnosticTestResult:
    name = "Durbin-Watson Autocorrelation Statistic"
    try:
        dw = _safe(durbin_watson(resid))
        if dw is None:
            interp = "Durbin-Watson statistic could not be computed."
        elif dw < 1.5:
            interp = (
                f"Durbin-Watson = {dw:.3f}: Possible positive first-order autocorrelation. "
                "Consider clustering standard errors or using a model that accounts for "
                "serial correlation."
            )
        elif dw > 2.5:
            interp = (
                f"Durbin-Watson = {dw:.3f}: Possible negative first-order autocorrelation."
            )
        else:
            interp = (
                f"Durbin-Watson = {dw:.3f}: Near 2, no strong evidence of "
                "first-order autocorrelation."
            )
        return DiagnosticTestResult(
            name=name, statistic=dw, p_value=None, interpretation=interp
        )
    except Exception as exc:
        return DiagnosticTestResult(
            name=name,
            statistic=None,
            p_value=None,
            interpretation=f"Test could not be computed: {exc!s}",
            available=False,
            unavailable_reason=str(exc),
        )


# ──────────────────────────────────────────────────────────────────────────────
# Hausman test (FE vs RE)
# ──────────────────────────────────────────────────────────────────────────────

def compute_hausman(fe_result: Any, re_result: Any) -> HausmanTestResult:
    """Compare FE and RE coefficient vectors.

    Uses a robust implementation with pseudo-inverse to handle near-singular
    covariance matrices.
    """
    try:
        # Align parameters on common variables (exclude const from RE params)
        fe_params = fe_result.params
        re_params = re_result.params.drop("const", errors="ignore")

        common = fe_params.index.intersection(re_params.index)
        if len(common) == 0:
            return HausmanTestResult(
                available=False,
                unavailable_reason="No common regressors between FE and RE estimates.",
            )

        b_fe = fe_params[common].values
        b_re = re_params[common].values

        # Covariance matrices — cov_params returns the full matrix
        try:
            V_fe = fe_result.cov.loc[common, common].values
        except Exception:
            V_fe = np.diag(fe_result.std_errors[common].values ** 2)

        try:
            re_cov = re_result.cov.drop("const", errors="ignore")
            re_cov = re_cov.drop("const", axis=1, errors="ignore")
            V_re = re_cov.loc[common, common].values
        except Exception:
            V_re = np.diag(re_result.std_errors[common].values ** 2)

        diff = b_fe - b_re
        V_diff = V_fe - V_re

        # Use pseudo-inverse for numerical robustness
        V_diff_inv = np.linalg.pinv(V_diff)
        stat = float(diff @ V_diff_inv @ diff)

        if math.isnan(stat) or math.isinf(stat) or stat < 0:
            return HausmanTestResult(
                available=False,
                unavailable_reason=(
                    "Hausman test statistic is numerically unstable. "
                    "The covariance matrix difference is not positive semi-definite."
                ),
            )

        k = len(common)
        from scipy.stats import chi2
        p_value = float(1 - chi2.cdf(stat, df=k))

        if p_value < 0.05:
            recommendation = (
                "The Hausman test provides evidence favouring Fixed Effects over "
                "Random Effects (p < 0.05). Under the test's assumptions, the "
                "null hypothesis that Random Effects is consistent is rejected."
            )
        else:
            recommendation = (
                "The Hausman test does not reject the null hypothesis that "
                "Random Effects is consistent (p ≥ 0.05). Random Effects may be "
                "preferred for efficiency under this specification."
            )

        return HausmanTestResult(
            available=True,
            statistic=_safe(stat),
            degrees_of_freedom=k,
            p_value=_safe(p_value),
            recommendation=recommendation,
        )

    except Exception as exc:
        return HausmanTestResult(
            available=False,
            unavailable_reason=f"Hausman test could not be computed: {exc!s}",
        )
