"""Transparent multi-criteria model selection service.

The recommended model is chosen based on a documented scoring framework, not
solely on fit statistics. Every criterion is recorded so the recommendation
is traceable.
"""
from __future__ import annotations

from typing import Any

from app.schemas.comparison import (
    ModelComparisonEntry,
    ModelScoreComponent,
    ModelSelectionRecommendation,
)
from app.schemas.modeling import ModelType

_MODEL_LABELS: dict[ModelType, str] = {
    "ols": "OLS",
    "robust_ols": "Robust OLS (HC1)",
    "pooled_ols": "Pooled OLS",
    "fixed_effects": "Fixed Effects",
    "random_effects": "Random Effects",
    "two_way_fixed_effects": "Two-Way Fixed Effects",
}

_COMPLEXITY_RANK: dict[ModelType, int] = {
    "ols": 1,
    "robust_ols": 2,
    "pooled_ols": 3,
    "random_effects": 4,
    "fixed_effects": 5,
    "two_way_fixed_effects": 6,
}

# ──────────────────────────────────────────────────────────────────────────────
# Individual scoring criteria (each 0–100, weighted)
# ──────────────────────────────────────────────────────────────────────────────

def _score_structural_compatibility(
    model_type: ModelType,
    has_entity: bool,
    has_time: bool,
) -> tuple[int, str]:
    """Structural fit (25 pts weight)."""
    is_panel = has_entity and has_time
    panel_models = {"pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"}
    if is_panel and model_type in panel_models:
        return 100, "Panel data detected; this panel model accounts for the data structure."
    if is_panel and model_type not in panel_models:
        return 30, (
            "Panel data detected but this model ignores the panel structure. "
            "Cross-sectional OLS on pooled panel data may yield biased standard errors."
        )
    if not is_panel and model_type not in panel_models:
        return 100, "Cross-sectional data; this model is structurally appropriate."
    return 0, "Panel model requested but no valid entity/time columns are configured."


def _score_hausman(
    model_type: ModelType,
    hausman_rejects: bool | None,
) -> tuple[int, str]:
    """Hausman test guidance (20 pts weight — only relevant for panel)."""
    panel_models = {"pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"}
    if model_type not in panel_models:
        return 50, "Hausman test not relevant for this model type."
    if hausman_rejects is None:
        return 40, "Hausman test result unavailable; cannot score FE vs RE preference."
    if hausman_rejects:
        if model_type in ("fixed_effects", "two_way_fixed_effects"):
            return 100, (
                "Hausman test rejects Random Effects consistency; Fixed Effects is preferred."
            )
        if model_type == "random_effects":
            return 10, (
                "Hausman test rejects Random Effects consistency; FE may be preferred."
            )
        return 50, "Hausman test favours Fixed Effects; Pooled OLS is a simpler alternative."
    else:
        if model_type == "random_effects":
            return 100, (
                "Hausman test does not reject Random Effects; RE may be preferred for efficiency."
            )
        if model_type in ("fixed_effects", "two_way_fixed_effects"):
            return 60, (
                "Hausman test does not reject Random Effects; FE is still consistent but may "
                "lose efficiency relative to RE under its assumptions."
            )
        return 50, "Hausman test consistent with Random Effects; Pooled OLS is simplest."


def _score_heteroskedasticity(
    model_type: ModelType,
    hetero_detected: bool | None,
    cluster_se: bool,
) -> tuple[int, str]:
    """Standard error robustness (15 pts weight)."""
    if hetero_detected is None:
        return 50, "Heteroskedasticity test not available."
    if hetero_detected:
        if model_type == "robust_ols":
            return 100, "Robust OLS with HC1 standard errors is appropriate when heteroskedasticity is detected."
        if cluster_se:
            return 90, "Clustered standard errors mitigate heteroskedasticity and within-group correlation."
        if model_type in ("fixed_effects", "two_way_fixed_effects", "random_effects", "pooled_ols"):
            return 60, (
                "Panel model detected heteroskedasticity; consider enabling clustered standard errors."
            )
        return 20, "Heteroskedasticity detected but standard errors are not adjusted."
    else:
        if model_type in ("ols", "pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"):
            return 100, "No significant heteroskedasticity; standard errors are appropriate."
        return 80, "Robust standard errors add safety margin when heteroskedasticity is not rejected."


def _score_parsimony(
    model_type: ModelType,
    competing_completed: list[ModelType],
    fit_gain_negligible: bool,
) -> tuple[int, str]:
    """Parsimony / complexity (10 pts weight)."""
    rank = _COMPLEXITY_RANK.get(model_type, 3)
    if not fit_gain_negligible:
        return max(20, 100 - (rank - 1) * 10), "Model complexity is offset by meaningful fit improvement."
    return max(20, 100 - (rank - 1) * 15), (
        "When fit gain across specifications is marginal, a simpler model is generally preferable."
    )


def _score_fit(
    model_type: ModelType,
    r_squared: float | None,
    adj_r_squared: float | None,
    aic: float | None,
    competing_aics: list[float | None],
) -> tuple[int, str]:
    """Fit quality (15 pts weight — used cautiously; never sole criterion)."""
    if adj_r_squared is None and r_squared is None:
        return 50, "Fit statistics not available for this model."

    ref = adj_r_squared or r_squared or 0.0
    if ref >= 0.7:
        return 90, f"Model fit is strong (R² ≈ {ref:.2f})."
    if ref >= 0.5:
        return 70, f"Model fit is moderate (R² ≈ {ref:.2f})."
    if ref >= 0.3:
        return 50, f"Model fit is limited (R² ≈ {ref:.2f}); consider whether key controls are missing."
    return 30, f"Model fit is low (R² ≈ {ref:.2f}); additional explanatory variables may be needed."


def _score_sample_size(n_obs: int | None) -> tuple[int, str]:
    """Observation count (10 pts weight)."""
    if n_obs is None:
        return 50, "Observation count unavailable."
    if n_obs >= 200:
        return 100, f"Large sample (n = {n_obs}) supports reliable inference."
    if n_obs >= 50:
        return 70, f"Moderate sample (n = {n_obs}); estimates are generally reliable."
    if n_obs >= 20:
        return 40, f"Small sample (n = {n_obs}); interpret confidence intervals cautiously."
    return 10, f"Very small sample (n = {n_obs}); inference may be unreliable."


def _score_estimation_success(completed: bool) -> tuple[int, str]:
    """Estimation success (5 pts weight)."""
    if completed:
        return 100, "Model estimation completed without errors."
    return 0, "Model estimation failed or was unavailable."


# ──────────────────────────────────────────────────────────────────────────────
# Main recommendation function
# ──────────────────────────────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "structural": 0.25,
    "hausman": 0.20,
    "heteroskedasticity": 0.15,
    "fit": 0.15,
    "parsimony": 0.10,
    "sample_size": 0.10,
    "estimation_success": 0.05,
}


def score_model(
    entry: ModelComparisonEntry,
    *,
    has_entity: bool,
    has_time: bool,
    hausman_rejects: bool | None,
    hetero_detected: bool | None,
    cluster_se: bool,
    all_completed: list[ModelType],
) -> tuple[int, list[ModelScoreComponent]]:
    """Return (weighted_score_0_to_100, score_component_list)."""
    m = entry.model_type
    completed = entry.status == "completed"
    fm = entry.fit_metrics
    dm = entry.diagnostic_summary

    # Determine if fit gain is negligible (within 0.02 adj R²)
    my_r2 = fm.adj_r_squared or fm.r_squared if fm else None
    other_r2s = []
    fit_gain_negligible = True
    if my_r2 is not None and my_r2 > 0:
        fit_gain_negligible = False

    strukt_s, strukt_e = _score_structural_compatibility(m, has_entity, has_time)
    hausman_s, hausman_e = _score_hausman(m, hausman_rejects)
    hetero_s, hetero_e = _score_heteroskedasticity(m, hetero_detected, cluster_se)
    parsimony_s, parsimony_e = _score_parsimony(m, all_completed, fit_gain_negligible)
    fit_s, fit_e = _score_fit(m, my_r2, my_r2, fm.aic if fm else None, [])
    sample_s, sample_e = _score_sample_size(fm.n_obs if fm else None)
    success_s, success_e = _score_estimation_success(completed)

    components = [
        ModelScoreComponent(
            criterion="Structural Compatibility",
            score=strukt_s,
            weight=_WEIGHTS["structural"],
            explanation=strukt_e,
        ),
        ModelScoreComponent(
            criterion="Hausman Test Guidance",
            score=hausman_s,
            weight=_WEIGHTS["hausman"],
            explanation=hausman_e,
        ),
        ModelScoreComponent(
            criterion="Heteroskedasticity Robustness",
            score=hetero_s,
            weight=_WEIGHTS["heteroskedasticity"],
            explanation=hetero_e,
        ),
        ModelScoreComponent(
            criterion="Model Fit",
            score=fit_s,
            weight=_WEIGHTS["fit"],
            explanation=fit_e,
        ),
        ModelScoreComponent(
            criterion="Parsimony",
            score=parsimony_s,
            weight=_WEIGHTS["parsimony"],
            explanation=parsimony_e,
        ),
        ModelScoreComponent(
            criterion="Sample Size Adequacy",
            score=sample_s,
            weight=_WEIGHTS["sample_size"],
            explanation=sample_e,
        ),
        ModelScoreComponent(
            criterion="Estimation Success",
            score=success_s,
            weight=_WEIGHTS["estimation_success"],
            explanation=success_e,
        ),
    ]

    weighted = sum(c.score * c.weight for c in components)
    return int(round(weighted)), components


def select_recommended_model(
    entries: list[ModelComparisonEntry],
    *,
    has_entity: bool,
    has_time: bool,
    cluster_se: bool,
) -> ModelSelectionRecommendation:
    """Score all completed models and return a transparent recommendation."""
    from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER

    completed_entries = [e for e in entries if e.status == "completed"]
    if not completed_entries:
        first = entries[0] if entries else None
        fallback_type: ModelType = first.model_type if first else "ols"
        return ModelSelectionRecommendation(
            recommended_model=fallback_type,
            confidence="low",
            score=0,
            reasons=["No models completed successfully; recommendation is not reliable."],
            warnings=[CAUSAL_LANGUAGE_DISCLAIMER],
            score_breakdown=[],
            alternative_models=[],
        )

    # Gather shared diagnostic context from the first completed model
    hausman_rejects: bool | None = None
    hetero_detected: bool | None = None
    for e in completed_entries:
        if e.diagnostic_summary:
            if e.diagnostic_summary.hausman_rejects_re is not None and hausman_rejects is None:
                hausman_rejects = e.diagnostic_summary.hausman_rejects_re
            if e.diagnostic_summary.heteroskedasticity_detected is not None and hetero_detected is None:
                hetero_detected = e.diagnostic_summary.heteroskedasticity_detected

    all_completed_types = [e.model_type for e in completed_entries]

    scored: list[tuple[int, ModelComparisonEntry, list[ModelScoreComponent]]] = []
    for entry in completed_entries:
        s, comps = score_model(
            entry,
            has_entity=has_entity,
            has_time=has_time,
            hausman_rejects=hausman_rejects,
            hetero_detected=hetero_detected,
            cluster_se=cluster_se,
            all_completed=all_completed_types,
        )
        scored.append((s, entry, comps))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_score, best_entry, best_comps = scored[0]

    # Confidence based on score margin
    if len(scored) > 1:
        margin = best_score - scored[1][0]
        confidence: str = "high" if margin >= 15 else "medium" if margin >= 5 else "low"
    else:
        confidence = "medium"

    # Build reasons from top-scoring components (score >= 70)
    reasons: list[str] = [c.explanation for c in best_comps if c.score >= 70]
    if not reasons:
        reasons = [best_comps[0].explanation] if best_comps else ["Highest overall score across all criteria."]

    warnings: list[str] = []
    if hetero_detected and best_entry.model_type not in ("robust_ols",) and not cluster_se:
        warnings.append(
            "Heteroskedasticity was detected. Consider enabling clustered or robust standard errors."
        )
    if has_entity and has_time and best_entry.model_type in ("ols", "robust_ols"):
        warnings.append(
            "Panel data is available but the recommended model ignores the panel structure. "
            "Consider panel models if within-entity variation is the focus."
        )
    warnings.append(
        "The estimated relationships should not be interpreted as causal without "
        "a valid identification strategy."
    )

    alternatives: list[dict[str, str]] = []
    for s, e, _ in scored[1:3]:
        label = _MODEL_LABELS.get(e.model_type, e.model_type)
        alternatives.append({"model_type": e.model_type, "model_label": label, "score": str(s),
                              "reason": f"Score: {s}/100."})

    return ModelSelectionRecommendation(
        recommended_model=best_entry.model_type,
        confidence=confidence,
        score=best_score,
        reasons=reasons,
        warnings=warnings,
        score_breakdown=best_comps,
        alternative_models=alternatives,
    )
