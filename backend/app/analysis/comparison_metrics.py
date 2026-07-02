"""Build standardized comparison metric dicts from model run results."""
from __future__ import annotations

import math

from app.analysis.ols_models import OLSRunResult
from app.analysis.panel_models import PanelRunResult
from app.schemas.comparison import DiagnosticSummary, ModelFitSummary
from app.schemas.modeling import (
    DiagnosticTestResult,
    HausmanTestResult,
    ModelType,
    VIFResult,
)


def _safe(v) -> float | None:
    try:
        f = float(v)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def ols_fit_summary(run: OLSRunResult) -> ModelFitSummary:
    f = run.fit
    return ModelFitSummary(
        r_squared=_safe(f.get("r_squared")),
        adj_r_squared=_safe(f.get("adj_r_squared")),
        aic=_safe(f.get("aic")),
        bic=_safe(f.get("bic")),
        f_statistic=_safe(f.get("f_statistic")),
        n_obs=f.get("n_obs"),
    )


def panel_fit_summary(run: PanelRunResult) -> ModelFitSummary:
    f = run.fit
    meta = run.model_metadata
    lm = run.lm_result

    within_r2 = _safe(getattr(lm, "rsquared", None))
    try:
        between_r2 = _safe(lm.rsquared_between)
    except AttributeError:
        between_r2 = None
    try:
        overall_r2 = _safe(lm.rsquared_overall)
    except AttributeError:
        overall_r2 = None

    return ModelFitSummary(
        r_squared=_safe(f.get("r_squared")),
        adj_r_squared=_safe(f.get("adj_r_squared")),
        within_r_squared=within_r2,
        between_r_squared=between_r2,
        overall_r_squared=overall_r2,
        f_statistic=_safe(f.get("f_statistic")),
        n_obs=f.get("n_obs"),
        n_entities=meta.get("n_entities"),
        n_time_periods=meta.get("n_time_periods"),
    )


def build_diagnostic_summary(
    vif_results: list[VIFResult],
    bp: DiagnosticTestResult | None,
    hausman: HausmanTestResult | None,
    dw: DiagnosticTestResult | None,
) -> DiagnosticSummary:
    max_vif: float | None = None
    if vif_results:
        valid_vifs = [v.vif for v in vif_results if v.vif > 0]
        max_vif = _safe(max(valid_vifs)) if valid_vifs else None

    hetero: bool | None = None
    if bp is not None and bp.available and bp.p_value is not None:
        hetero = bp.p_value < 0.05

    hausman_rejects: bool | None = None
    hausman_p: float | None = None
    if hausman is not None and hausman.available and hausman.p_value is not None:
        hausman_rejects = hausman.p_value < 0.05
        hausman_p = _safe(hausman.p_value)

    dw_stat: float | None = None
    if dw is not None and dw.available and dw.statistic is not None:
        dw_stat = _safe(dw.statistic)

    return DiagnosticSummary(
        max_vif=max_vif,
        heteroskedasticity_detected=hetero,
        hausman_rejects_re=hausman_rejects,
        hausman_p_value=hausman_p,
        durbin_watson=dw_stat,
    )
