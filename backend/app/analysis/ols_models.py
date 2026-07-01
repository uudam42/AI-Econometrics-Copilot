"""OLS and Robust-OLS estimation via statsmodels.

All regression coefficients, standard errors, and test statistics are computed
by statsmodels. This module NEVER fabricates statistical values.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.regression.linear_model import RegressionResultsWrapper

from app.core.errors import ModelExecutionError


def _safe(v) -> float | None:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def _significance(p: float | None) -> str:
    if p is None:
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def _sanitize_col(name: str) -> str:
    """Replace characters invalid for patsy/statsmodels formula identifiers."""
    return name.replace(" ", "_").replace("-", "_").replace(".", "_")


def _build_formula(dep: str, regressors: list[str]) -> tuple[str, dict[str, str]]:
    """Return (formula_string, {original_name: safe_name}) mapping."""
    name_map: dict[str, str] = {}
    safe_vars: list[str] = []
    for col in [dep] + regressors:
        safe = _sanitize_col(col)
        name_map[col] = safe
        safe_vars.append(safe)

    safe_dep = name_map[dep]
    safe_regressors = [name_map[r] for r in regressors]
    formula = f"{safe_dep} ~ {' + '.join(safe_regressors)}"
    return formula, name_map


@dataclass
class OLSRunResult:
    coefficients: list[dict]
    fit: dict
    residuals: list[float]
    fitted_values: list[float]
    actual_values: list[float]
    formula: str
    model_metadata: dict
    sm_result: RegressionResultsWrapper


def run_ols(
    df: pd.DataFrame,
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    robust: bool = False,
) -> OLSRunResult:
    """Fit OLS (or Robust OLS with HC1 errors) and return structured results."""
    regressors = [primary_iv] + controls

    # Build a renamed copy to avoid patsy quoting issues
    formula, name_map = _build_formula(dep_var, regressors)
    df_safe = df[[dep_var] + regressors].copy().rename(columns=name_map)

    # Drop rows missing any modeling variable
    n_before = len(df_safe)
    df_safe = df_safe.dropna()
    n_after = len(df_safe)

    if n_after < len(regressors) + 2:
        raise ModelExecutionError(
            f"Too few observations ({n_after}) to fit the model after dropping "
            "rows with missing values. At minimum, the number of observations "
            "must exceed the number of regressors."
        )

    try:
        model = smf.ols(formula, data=df_safe)
        result = model.fit(cov_type="HC1") if robust else model.fit()
    except Exception as exc:
        raise ModelExecutionError(
            f"OLS estimation failed: {exc!s}. "
            "Check for perfect multicollinearity or insufficient variation in regressors."
        ) from exc

    # Reverse name map for display
    rev_map = {v: k for k, v in name_map.items()}

    coefficients: list[dict] = []
    for var_safe in result.params.index:
        var_display = rev_map.get(var_safe, var_safe)
        ci = result.conf_int().loc[var_safe]
        p = _safe(result.pvalues[var_safe])
        coefficients.append({
            "variable": var_display,
            "coefficient": _safe(result.params[var_safe]),
            "std_error": _safe(result.bse[var_safe]),
            "t_stat": _safe(result.tvalues[var_safe]),
            "p_value": p,
            "ci_lower": _safe(ci.iloc[0]),
            "ci_upper": _safe(ci.iloc[1]),
            "significance": _significance(p),
        })

    fit = {
        "r_squared": _safe(result.rsquared),
        "adj_r_squared": _safe(result.rsquared_adj),
        "f_statistic": _safe(result.fvalue),
        "f_pvalue": _safe(result.f_pvalue),
        "aic": _safe(result.aic),
        "bic": _safe(result.bic),
        "n_obs": int(result.nobs),
        "formula": formula.replace(name_map.get(dep_var, dep_var), dep_var),
    }

    # Replace safe names back in displayed formula
    display_formula = formula
    for orig, safe in name_map.items():
        display_formula = display_formula.replace(safe, orig)

    fit["formula"] = display_formula

    resid = [_safe(v) or 0.0 for v in result.resid.tolist()]
    fitted = [_safe(v) or 0.0 for v in result.fittedvalues.tolist()]
    actual = [_safe(v) or 0.0 for v in df_safe[name_map[dep_var]].tolist()]

    cov_type = "HC1 (heteroskedasticity-robust)" if robust else "OLS (non-robust)"
    metadata = {
        "cov_type": cov_type,
        "n_dropped_rows": n_before - n_after,
    }

    return OLSRunResult(
        coefficients=coefficients,
        fit=fit,
        residuals=resid,
        fitted_values=fitted,
        actual_values=actual,
        formula=display_formula,
        model_metadata=metadata,
        sm_result=result,
    )
