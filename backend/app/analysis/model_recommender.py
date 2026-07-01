"""Rule-driven model recommendation.

Recommendations are based on dataset structure, diagnostic results, and
configured variables. No LLM is involved. The user retains final judgement.
"""
from __future__ import annotations

from app.schemas.modeling import (
    DiagnosticTestResult,
    HausmanTestResult,
    ModelRecommendation,
    ModelType,
)


def recommend_model(
    *,
    has_entity_column: bool,
    has_time_column: bool,
    n_entities: int | None,
    n_periods: int | None,
    breusch_pagan: DiagnosticTestResult | None,
    hausman: HausmanTestResult | None,
    n_obs: int,
    cluster_by_entity: bool,
) -> ModelRecommendation:
    """Return a rule-based model recommendation."""
    reasons: list[str] = []
    warnings: list[str] = []

    is_panel = has_entity_column and has_time_column
    recommended: ModelType

    if is_panel and n_entities and n_periods and n_entities > 1 and n_periods > 1:
        # Panel data path
        if hausman and hausman.available and hausman.p_value is not None:
            if hausman.p_value < 0.05:
                recommended = "fixed_effects"
                confidence = "medium"
                reasons.append(
                    "Panel structure detected with multiple entities and time periods."
                )
                reasons.append(
                    "The Hausman test favours Fixed Effects over Random Effects "
                    "at the 5% significance level."
                )
                reasons.append(
                    "Entity Fixed Effects can account for time-invariant unobserved "
                    "heterogeneity across entities."
                )
                if cluster_by_entity:
                    reasons.append(
                        "Clustered standard errors by entity are enabled, which is "
                        "appropriate for panel data with within-entity correlation."
                    )
            else:
                recommended = "random_effects"
                confidence = "medium"
                reasons.append(
                    "Panel structure detected with multiple entities and time periods."
                )
                reasons.append(
                    "The Hausman test does not reject Random Effects at the 5% level; "
                    "Random Effects may be preferred for efficiency."
                )
        else:
            recommended = "fixed_effects"
            confidence = "low"
            reasons.append(
                "Panel structure detected with multiple entities and time periods."
            )
            reasons.append(
                "Fixed Effects is a conservative default for panel data "
                "when Hausman test results are unavailable."
            )
            warnings.append(
                "Run both Fixed Effects and Random Effects and consider running the "
                "Hausman test to choose between them."
            )

        if n_entities and n_periods and n_entities * n_periods != n_obs:
            warnings.append(
                "The panel appears to be unbalanced (some entity-period cells are missing). "
                "Interpret R² and fit statistics accordingly."
            )
    else:
        # Cross-sectional or time-series path
        if breusch_pagan and breusch_pagan.available and breusch_pagan.p_value is not None:
            if breusch_pagan.p_value < 0.05:
                recommended = "robust_ols"
                confidence = "medium"
                reasons.append(
                    "The Breusch-Pagan test detects heteroskedasticity; "
                    "Robust OLS with HC1 standard errors is recommended."
                )
            else:
                recommended = "ols"
                confidence = "medium"
                reasons.append(
                    "No significant heteroskedasticity detected; OLS is appropriate."
                )
        else:
            recommended = "ols"
            confidence = "low"
            reasons.append("Cross-sectional or time-series data detected.")
            reasons.append("OLS is the default baseline model.")
            warnings.append(
                "Consider running the Breusch-Pagan test to check for heteroskedasticity "
                "and switching to Robust OLS if detected."
            )

    warnings.append(
        "This recommendation reflects statistical associations and should not be "
        "interpreted as causal evidence without additional identification assumptions."
    )

    return ModelRecommendation(
        recommended_model=recommended,
        confidence=confidence,
        reasons=reasons,
        warnings=warnings,
    )
