"""Deterministic plain-language summary generator for Quick Analyze results.

No LLM is used. All text is derived from actual model outputs using fixed
templates and rule-based logic. Caution language is always present.
"""
from __future__ import annotations

from app.schemas.modeling import AnalysisResult, ModelDiagnosticsResponse
from app.schemas.quick_analyze import BeginnerSummary, DiagnosticsStatusCard

_MODEL_LABELS = {
    "ols": "Ordinary Least Squares (OLS)",
    "robust_ols": "Robust OLS with heteroskedasticity-consistent standard errors",
    "pooled_ols": "Pooled OLS",
    "fixed_effects": "Fixed Effects",
    "random_effects": "Random Effects",
    "two_way_fixed_effects": "Two-Way Fixed Effects",
}

_CAUSAL_WARNING = (
    "This result reflects a statistical association under the selected model and "
    "assumptions. It should not be interpreted as causal evidence without a "
    "stronger identification strategy."
)


def _data_quality_status(diagnostics: ModelDiagnosticsResponse | None) -> str:
    if diagnostics is None:
        return "Needs review"
    # Use Jarque-Bera as a rough proxy for data quality concerns.
    jb = diagnostics.jarque_bera
    if jb and jb.available and jb.p_value is not None and jb.p_value < 0.01:
        return "Needs review"
    return "Good"


def _model_fit_status(result: AnalysisResult) -> str:
    r2 = result.fit.r_squared if result.fit else None
    if r2 is None:
        return "Limited"
    return "Available" if r2 > 0.05 else "Limited"


def _multicollinearity_status(diagnostics: ModelDiagnosticsResponse | None) -> str:
    if diagnostics is None or not diagnostics.vif:
        return "Low concern"
    max_vif = max((v.vif for v in diagnostics.vif if v.vif is not None), default=0.0)
    if max_vif > 10:
        return "High concern"
    if max_vif > 5:
        return "Moderate concern"
    return "Low concern"


def _heteroskedasticity_status(diagnostics: ModelDiagnosticsResponse | None) -> str:
    if diagnostics is None:
        return "Not detected"
    bp = diagnostics.breusch_pagan
    if bp and bp.available and bp.p_value is not None and bp.p_value < 0.05:
        return "Detected — robust standard errors recommended"
    return "Not detected"


def _panel_status(result: AnalysisResult) -> str:
    panel_types = {"fixed_effects", "random_effects", "two_way_fixed_effects", "pooled_ols"}
    return "Detected" if result.model_type in panel_types else "Not detected"


def generate_beginner_summary(
    result: AnalysisResult,
    diagnostics: ModelDiagnosticsResponse | None,
    dataset_filename: str,
    dependent_variable: str,
    primary_variable: str,
) -> BeginnerSummary:
    """Produce a plain-language summary from actual model outputs."""
    model_label = _MODEL_LABELS.get(result.model_type, result.model_type)
    n_rows = (result.fit.n_obs if result.fit else None) or 0
    n_cols_desc = f"{n_rows} observations"

    # Find the primary variable coefficient
    coeff = next(
        (c for c in result.coefficients if c.variable == primary_variable),
        None,
    )

    is_significant = bool(
        coeff and coeff.p_value is not None and coeff.p_value < 0.05
    )

    if coeff is None:
        main_finding = (
            f"The variable '{primary_variable}' could not be located in the "
            "model output. Check that the variable was included."
        )
    elif is_significant:
        direction = "positively" if (coeff.coefficient or 0) > 0 else "negatively"
        p_str = f"{coeff.p_value:.3f}" if coeff.p_value is not None else "unknown"
        main_finding = (
            f"Under the selected model, '{primary_variable}' is statistically "
            f"associated with '{dependent_variable}' ({direction}, p = {p_str}). "
            "This is a statistical association, not a causal claim."
        )
    else:
        p_str = f"{coeff.p_value:.3f}" if coeff.p_value is not None else "unknown"
        main_finding = (
            f"Under the selected model, '{primary_variable}' is not statistically "
            f"distinguishable from zero at the 5% level (p = {p_str}). "
            "This does not rule out a relationship — it may reflect limited data, "
            "model specification, or genuine absence of association."
        )

    r2 = result.fit.r_squared if result.fit else None
    r2_str = f"{r2:.3f}" if r2 is not None else "not available"
    headline = (
        f"Analysis of {dataset_filename}: "
        + ("association found" if is_significant else "no clear association detected")
    )

    warnings: list[str] = []
    if diagnostics:
        if _heteroskedasticity_status(diagnostics).startswith("Detected"):
            warnings.append(
                "Heteroskedasticity detected. Consider using robust standard errors."
            )
        mc = _multicollinearity_status(diagnostics)
        if mc != "Low concern":
            warnings.append(f"Multicollinearity: {mc}. Interpret coefficients with caution.")
        # high_leverage_count is not a field on ModelDiagnosticsResponse;
        # skip that check.

    diag_card = DiagnosticsStatusCard(
        data_quality=_data_quality_status(diagnostics),
        model_fit=_model_fit_status(result),
        multicollinearity=_multicollinearity_status(diagnostics),
        heteroskedasticity=_heteroskedasticity_status(diagnostics),
        panel_structure=_panel_status(result),
        causal_interpretation="Association only",
    )

    next_actions = [
        "View full regression table and diagnostics",
        "Compare with alternative models",
        "Generate a DOCX or LaTeX report",
        "Open the full Research Workspace for deeper investigation",
    ]

    return BeginnerSummary(
        headline=headline,
        dataset_description=f"{n_cols_desc} from '{dataset_filename}'. R² = {r2_str}.",
        model_used=model_label,
        main_finding=main_finding,
        is_significant=is_significant,
        causal_warning=_CAUSAL_WARNING,
        key_warnings=warnings,
        diagnostics_status=diag_card,
        next_actions=next_actions,
    )
