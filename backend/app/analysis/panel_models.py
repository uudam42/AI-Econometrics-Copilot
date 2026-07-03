"""Panel regression via linearmodels (PooledOLS, PanelOLS, RandomEffects).

All statistical computations are performed by linearmodels and numpy.
This module NEVER fabricates coefficients, standard errors, or test statistics.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS, PooledOLS, RandomEffects

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


def _set_panel_index(
    df: pd.DataFrame, entity_col: str, time_col: str
) -> pd.DataFrame:
    if entity_col not in df.columns:
        raise ModelExecutionError(
            f"Entity column '{entity_col}' does not exist in the processed dataset."
        )
    if time_col not in df.columns:
        raise ModelExecutionError(
            f"Time column '{time_col}' does not exist in the processed dataset."
        )
    return df.set_index([entity_col, time_col])


def _validate_panel(df_panel: pd.DataFrame, dep_var: str, regressors: list[str]) -> None:
    n_entities = df_panel.index.get_level_values(0).nunique()
    n_periods = df_panel.index.get_level_values(1).nunique()
    if n_entities < 2:
        raise ModelExecutionError(
            "Panel regression requires at least 2 distinct entities. "
            f"Found only {n_entities}."
        )
    if n_periods < 2:
        raise ModelExecutionError(
            "Panel regression requires at least 2 distinct time periods. "
            f"Found only {n_periods}."
        )
    for col in [dep_var] + regressors:
        if col not in df_panel.columns:
            raise ModelExecutionError(
                f"Variable '{col}' does not exist in the processed dataset."
            )
        if not pd.api.types.is_numeric_dtype(df_panel[col]):
            raise ModelExecutionError(
                f"Variable '{col}' must be numeric for panel regression."
            )


def _extract_coefficients(result, model_type: str) -> list[dict]:
    coefficients: list[dict] = []
    params = result.params
    try:
        std_errors = result.std_errors
    except Exception:
        std_errors = params * float("nan")
    try:
        tstats = result.tstats
    except Exception:
        tstats = params * float("nan")
    try:
        pvalues = result.pvalues
    except Exception:
        pvalues = params * float("nan")
    try:
        ci = result.conf_int()
        ci_lower = ci.iloc[:, 0]
        ci_upper = ci.iloc[:, 1]
    except Exception:
        ci_lower = params * float("nan")
        ci_upper = params * float("nan")

    for var in params.index:
        p = _safe(pvalues[var])
        coefficients.append({
            "variable": str(var),
            "coefficient": _safe(params[var]),
            "std_error": _safe(std_errors[var]),
            "t_stat": _safe(tstats[var]),
            "p_value": p,
            "ci_lower": _safe(ci_lower[var]),
            "ci_upper": _safe(ci_upper[var]),
            "significance": _significance(p),
        })
    return coefficients


def _get_resids_fitted(result, df_panel: pd.DataFrame, dep_var: str) -> tuple[list[float], list[float], list[float]]:
    try:
        resids = [_safe(v) or 0.0 for v in result.resids.values.tolist()]
    except Exception:
        resids = []
    try:
        fitted = [_safe(v) or 0.0 for v in result.fitted_values.values.tolist()]
    except Exception:
        fitted = []
    try:
        actual = [_safe(v) or 0.0 for v in df_panel[dep_var].values.tolist()]
    except Exception:
        actual = []
    return resids, fitted, actual


@dataclass
class PanelRunResult:
    coefficients: list[dict]
    fit: dict
    residuals: list[float]
    fitted_values: list[float]
    actual_values: list[float]
    formula: str
    model_metadata: dict
    lm_result: Any  # linearmodels result object
    absorbed_variables: list[str] | None = None


def run_panel(
    df: pd.DataFrame,
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    entity_col: str,
    time_col: str,
    model_type: str,
    cluster_by_entity: bool = False,
) -> PanelRunResult:
    """Fit a panel regression model and return structured results."""
    regressors = [primary_iv] + controls

    # Build panel-indexed DataFrame
    analysis_cols = [dep_var] + regressors + [entity_col, time_col]
    unique_cols = list(dict.fromkeys(analysis_cols))
    df_sub = df[unique_cols].copy().dropna(subset=[dep_var] + regressors)
    df_panel = _set_panel_index(df_sub, entity_col, time_col)
    df_panel = df_panel.sort_index()

    _validate_panel(df_panel, dep_var, regressors)

    n_entities = df_panel.index.get_level_values(0).nunique()
    n_periods = df_panel.index.get_level_values(1).nunique()

    y = df_panel[dep_var].astype(float)
    X = df_panel[regressors].astype(float)

    # Determine if we need a constant column
    needs_const = model_type in ("pooled_ols", "random_effects")

    if needs_const:
        X = X.copy()
        X.insert(0, "const", 1.0)

    entity_effects = model_type in ("fixed_effects", "two_way_fixed_effects")
    time_effects = model_type == "two_way_fixed_effects"

    try:
        if model_type == "pooled_ols":
            model = PooledOLS(y, X)
        elif model_type in ("fixed_effects", "two_way_fixed_effects"):
            model = PanelOLS(y, X, entity_effects=entity_effects, time_effects=time_effects, drop_absorbed=True)
        elif model_type == "random_effects":
            model = RandomEffects(y, X)
        else:
            raise ModelExecutionError(f"Unknown panel model type: '{model_type}'.")

        if cluster_by_entity:
            result = model.fit(cov_type="clustered", cluster_entity=True)
        else:
            result = model.fit()

    except ModelExecutionError:
        raise
    except Exception as exc:
        raise ModelExecutionError(
            f"Panel model estimation failed: {exc!s}. "
            "Check that the entity and time columns form a valid panel structure "
            "and that selected variables have sufficient within-entity variation."
        ) from exc

    # Detect absorbed variables: compare input regressors with estimated params
    estimated_params = set(result.params.index.tolist())
    all_input_vars = set(regressors)
    if needs_const:
        all_input_vars.add("const")
    absorbed = sorted(all_input_vars - estimated_params)

    coefficients = _extract_coefficients(result, model_type)
    resids, fitted, actual = _get_resids_fitted(result, df_panel, dep_var)

    # Build fit statistics
    rsq = _safe(getattr(result, "rsquared", None))
    rsq_adj = _safe(getattr(result, "rsquared_adj", None))

    regressors_str = " + ".join(regressors)
    formula = f"{dep_var} ~ {regressors_str}"
    if needs_const:
        formula += " + const"

    fit = {
        "r_squared": rsq,
        "adj_r_squared": rsq_adj,
        "f_statistic": _safe(getattr(result, "f_statistic", {}).get("stat") if hasattr(result, "f_statistic") and isinstance(getattr(result, "f_statistic", None), dict) else getattr(result, "f_statistic", None)),
        "f_pvalue": None,
        "aic": None,
        "bic": None,
        "n_obs": int(result.nobs),
        "formula": formula,
    }

    cov_desc = "clustered (entity)" if cluster_by_entity else "standard"
    metadata: dict = {
        "entity_effects": entity_effects,
        "time_effects": time_effects,
        "cov_type": cov_desc,
        "n_entities": n_entities,
        "n_time_periods": n_periods,
        "is_balanced": bool(
            n_entities * n_periods == int(result.nobs)
        ),
    }

    if absorbed:
        absorbed_reasons = []
        for var in absorbed:
            if entity_effects and time_effects:
                absorbed_reasons.append(
                    f"'{var}' was absorbed (collinear with entity and/or time fixed effects)"
                )
            elif entity_effects:
                absorbed_reasons.append(
                    f"'{var}' was absorbed (collinear with entity fixed effects)"
                )
            else:
                absorbed_reasons.append(f"'{var}' was absorbed")
        metadata["absorbed_variables"] = absorbed
        metadata["absorbed_warnings"] = absorbed_reasons
        primary_iv_absorbed = primary_iv in absorbed
        metadata["primary_iv_absorbed"] = primary_iv_absorbed
        if primary_iv_absorbed:
            metadata["absorbed_critical_warning"] = (
                f"The primary independent variable '{primary_iv}' was absorbed by "
                "the fixed effects. This means the variable has no within-entity "
                "variation and its effect cannot be estimated in this specification."
            )

    return PanelRunResult(
        coefficients=coefficients,
        fit=fit,
        residuals=resids,
        fitted_values=fitted,
        actual_values=actual,
        formula=formula,
        model_metadata=metadata,
        lm_result=result,
        absorbed_variables=absorbed if absorbed else None,
    )


def run_fixed_effects_for_hausman(
    df: pd.DataFrame,
    dep_var: str,
    regressors: list[str],
    entity_col: str,
    time_col: str,
) -> Any:
    """Run FE model and return lm result (for Hausman test)."""
    df_sub = df[[dep_var] + regressors + [entity_col, time_col]].copy()
    df_sub = df_sub.dropna(subset=[dep_var] + regressors)
    df_panel = df_sub.set_index([entity_col, time_col]).sort_index()
    y = df_panel[dep_var].astype(float)
    X = df_panel[regressors].astype(float)
    model = PanelOLS(y, X, entity_effects=True)
    return model.fit()


def run_random_effects_for_hausman(
    df: pd.DataFrame,
    dep_var: str,
    regressors: list[str],
    entity_col: str,
    time_col: str,
) -> Any:
    """Run RE model and return lm result (for Hausman test)."""
    df_sub = df[[dep_var] + regressors + [entity_col, time_col]].copy()
    df_sub = df_sub.dropna(subset=[dep_var] + regressors)
    df_panel = df_sub.set_index([entity_col, time_col]).sort_index()
    y = df_panel[dep_var].astype(float)
    X = df_panel[regressors].astype(float)
    X = X.copy()
    X.insert(0, "const", 1.0)
    model = RandomEffects(y, X)
    return model.fit()
