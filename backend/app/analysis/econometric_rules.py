"""Centralized, documented econometric decision rules.

This module is the single source of truth for thresholds and recommendation
text used across the profiler, diagnostics, and model scoring services, so
that `docs/econometric_rules.md` and the code never drift apart.

Nothing here performs estimation — it only encodes *when* to recommend an
action, given numbers already computed by pandas/scipy/statsmodels/linearmodels.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class RuleRecommendation:
    triggered: bool
    message: str


def should_recommend_log_transform(skewness: float, all_positive: bool) -> RuleRecommendation:
    triggered = all_positive and skewness > settings.high_skew_threshold
    return RuleRecommendation(
        triggered=triggered,
        message=(
            "Variable is positive and heavily right-skewed; a natural log transform "
            "may stabilize variance and improve linearity."
            if triggered
            else "No log transform recommended."
        ),
    )


def should_recommend_robust_se(breusch_pagan_p_value: float) -> RuleRecommendation:
    triggered = breusch_pagan_p_value < settings.heteroskedasticity_alpha
    return RuleRecommendation(
        triggered=triggered,
        message=(
            "Evidence of heteroskedasticity was detected (Breusch-Pagan "
            f"p-value < {settings.heteroskedasticity_alpha}); use heteroskedasticity-robust "
            "standard errors."
            if triggered
            else "No significant heteroskedasticity detected at the configured alpha level."
        ),
    )


def vif_risk_level(vif: float) -> str:
    if vif >= settings.vif_severe_threshold:
        return "severe"
    if vif >= settings.vif_warning_threshold:
        return "moderate"
    return "low"


def should_recommend_fixed_effects(entity_count: int, time_period_count: int) -> RuleRecommendation:
    triggered = entity_count > 1 and time_period_count > 1
    return RuleRecommendation(
        triggered=triggered,
        message=(
            "Panel structure detected (multiple entities observed over multiple periods); "
            "entity fixed effects can absorb time-invariant unobserved heterogeneity."
            if triggered
            else "Panel structure not detected; fixed effects are not applicable."
        ),
    )


CAUSAL_LANGUAGE_DISCLAIMER = (
    "This analysis identifies statistical associations and does not establish "
    "causal effects unless additional identification assumptions are justified."
)
