"""Section builders for econometric research reports.

Each function returns a string of Markdown. All coefficient values, p-values,
and test statistics must come from pre-computed results — this module NEVER
fabricates numerical claims.
"""
from __future__ import annotations

from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER
from app.schemas.comparison import ComparisonResult, ModelComparisonEntry
from app.schemas.modeling import (
    AnalysisResult,
    CoefficientResult,
    DiagnosticTestResult,
    HausmanTestResult,
    ModelDiagnosticsResponse,
    VIFResult,
)

_MODEL_LABELS = {
    "ols": "OLS (Ordinary Least Squares)",
    "robust_ols": "Robust OLS (HC1 Standard Errors)",
    "pooled_ols": "Pooled OLS",
    "fixed_effects": "Fixed Effects (Within Estimator)",
    "random_effects": "Random Effects (GLS)",
    "two_way_fixed_effects": "Two-Way Fixed Effects",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _fmt(v: float | None, decimals: int = 4) -> str:
    if v is None:
        return "N/A"
    return f"{v:.{decimals}f}"


def _sig_label(sig: str) -> str:
    if sig == "***":
        return "statistically significant at the 1% level"
    if sig == "**":
        return "statistically significant at the 5% level"
    if sig == "*":
        return "statistically significant at the 10% level"
    return "not statistically significant at conventional thresholds"


def _interpret_coeff(
    coeff: CoefficientResult,
    dep_var: str,
    sig_level: float = 0.05,
    is_log_dep: bool = False,
) -> str:
    """Produce a careful coefficient interpretation sentence."""
    v = coeff.variable
    b = coeff.coefficient
    p = coeff.p_value
    sig = coeff.significance

    if b is None:
        return f"The coefficient for **{v}** could not be estimated."

    if p is not None and p >= sig_level:
        return (
            f"The estimated association between **{v}** and **{dep_var}** is not "
            f"statistically distinguishable from zero at the {sig_level:.0%} significance "
            f"level (coefficient = {_fmt(b)}, p = {_fmt(p)})."
        )

    direction = "positively" if b > 0 else "negatively"
    if is_log_dep:
        pct = abs(b) * 100
        return (
            f"A one-unit increase in **{v}** is associated with an approximate "
            f"**{pct:.2f}%** {'increase' if b > 0 else 'decrease'} in **{dep_var}**, "
            f"holding selected controls constant "
            f"(coefficient = {_fmt(b)}, SE = {_fmt(coeff.std_error)}, "
            f"95% CI [{_fmt(coeff.ci_lower)}, {_fmt(coeff.ci_upper)}], "
            f"p = {_fmt(p)}; {_sig_label(sig)})."
        )
    return (
        f"A one-unit increase in **{v}** is associated with an estimated "
        f"**{_fmt(abs(b))}**-unit {direction.replace('ly', '')} change in **{dep_var}**, "
        f"holding selected controls constant "
        f"(coefficient = {_fmt(b)}, SE = {_fmt(coeff.std_error)}, "
        f"95% CI [{_fmt(coeff.ci_lower)}, {_fmt(coeff.ci_upper)}], "
        f"p = {_fmt(p)}; {_sig_label(sig)})."
    )


# ──────────────────────────────────────────────────────────────────────────────
# Section builders
# ──────────────────────────────────────────────────────────────────────────────

def section_title(title: str, research_question: str | None) -> str:
    lines = [f"# {title}", ""]
    if research_question:
        lines += [f"> **Research question:** {research_question}", ""]
    return "\n".join(lines)


def section_metadata(
    *,
    analysis_id: str | None = None,
    comparison_id: str | None = None,
    dataset_filename: str,
    created_at: str,
    model_label: str,
) -> str:
    src_id = analysis_id or comparison_id or "—"
    src_type = "Analysis" if analysis_id else "Comparison"
    return "\n".join([
        "## 1. Analysis Metadata",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| {src_type} ID | `{src_id}` |",
        f"| Dataset | {dataset_filename} |",
        f"| Model | {model_label} |",
        f"| Generated at | {created_at} |",
        "",
    ])


def section_dataset_overview(
    *,
    dataset_filename: str,
    n_rows: int | None,
    n_cols: int | None,
    structure: str | None,
) -> str:
    lines = ["## 2. Dataset Overview", ""]
    lines.append(f"**File:** {dataset_filename}")
    if n_rows is not None:
        lines.append(f"  \n**Observations:** {n_rows}")
    if n_cols is not None:
        lines.append(f"  \n**Variables:** {n_cols}")
    if structure:
        lines.append(f"  \n**Detected structure:** {structure}")
    lines.append("")
    return "\n".join(lines)


def section_variable_definitions(
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    entity_col: str | None,
    time_col: str | None,
) -> str:
    lines = [
        "## 3. Variable Definitions",
        "",
        "| Role | Variable |",
        "|---|---|",
        f"| Dependent variable | `{dep_var}` |",
        f"| Primary independent variable | `{primary_iv}` |",
    ]
    for c in controls:
        lines.append(f"| Control variable | `{c}` |")
    if entity_col:
        lines.append(f"| Entity identifier | `{entity_col}` |")
    if time_col:
        lines.append(f"| Time identifier | `{time_col}` |")
    lines.append("")
    return "\n".join(lines)


def section_transformation_log(log: list) -> str:
    if not log:
        return "## 4. Data Cleaning\n\nNo transformations were applied.\n"
    lines = ["## 4. Data Cleaning and Transformations", ""]
    for entry in log:
        step = getattr(entry, "step", "?")
        op = getattr(entry, "operation", "")
        cols = getattr(entry, "columns", [])
        r_before = getattr(entry, "rows_before", "?")
        r_after = getattr(entry, "rows_after", "?")
        lines.append(
            f"**Step {step}:** `{op}` on `{', '.join(cols)}` "
            f"— rows: {r_before} → {r_after}"
        )
    lines.append("")
    return "\n".join(lines)


def section_model_specification(
    model_label: str,
    formula: str,
    se_type: str | None,
    n_obs: int | None,
) -> str:
    return "\n".join([
        "## 5. Model Specification",
        "",
        f"**Model:** {model_label}",
        f"  \n**Formula:** `{formula}`",
        f"  \n**Standard errors:** {se_type or 'standard'}",
        f"  \n**Observations:** {n_obs if n_obs is not None else 'N/A'}",
        "",
    ])


def section_comparison_table(models: list[ModelComparisonEntry]) -> str:
    lines = [
        "## 6. Model Comparison Summary",
        "",
        "| Model | Status | N | R² | Adj. R² | AIC | BIC | Max VIF | Hetero |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for m in models:
        status = m.status
        fm = m.fit_metrics
        dm = m.diagnostic_summary
        n = str(fm.n_obs) if fm and fm.n_obs else "—"
        r2 = _fmt(fm.r_squared, 3) if fm else "—"
        ar2 = _fmt(fm.adj_r_squared, 3) if fm else "—"
        aic = _fmt(fm.aic, 1) if fm else "—"
        bic = _fmt(fm.bic, 1) if fm else "—"
        vif = _fmt(dm.max_vif, 1) if dm and dm.max_vif else "—"
        hetero = ("Yes" if dm.heteroskedasticity_detected else "No") if (dm and dm.heteroskedasticity_detected is not None) else "—"
        reason_note = f" ({m.reason[:60]}…)" if m.reason and len(m.reason or "") > 60 else (f" ({m.reason})" if m.reason else "")
        lines.append(
            f"| {m.model_label} | {status}{reason_note} | {n} | {r2} | {ar2} | {aic} | {bic} | {vif} | {hetero} |"
        )
    lines.append("")
    return "\n".join(lines)


def section_recommendation(rec) -> str:
    lines = [
        "## 7. Model Recommendation",
        "",
        f"**Recommended model:** {_MODEL_LABELS.get(rec.recommended_model, rec.recommended_model)}  ",
        f"**Confidence:** {rec.confidence}  ",
        f"**Score:** {rec.score}/100",
        "",
        "**Reasons:**",
    ]
    for r in rec.reasons:
        lines.append(f"- {r}")
    if rec.warnings:
        lines += ["", "**Warnings:**"]
        for w in rec.warnings:
            lines.append(f"- {w}")
    if getattr(rec, "score_breakdown", None):
        lines += ["", "**Score breakdown:**", "", "| Criterion | Score | Weight |", "|---|---|---|"]
        for c in rec.score_breakdown:
            lines.append(f"| {c.criterion} | {c.score}/100 | {c.weight:.0%} |")
    if getattr(rec, "alternative_models", None):
        lines += ["", "**Alternative models considered:**"]
        for alt in rec.alternative_models:
            label = alt.get("model_label") or _MODEL_LABELS.get(alt.get("model_type", ""), alt.get("model_type", ""))
            lines.append(f"- {label} — {alt.get('reason', '')}")
    lines.append("")
    return "\n".join(lines)


def section_regression_results(
    coefficients: list[CoefficientResult],
    fit,
    sig_level: float = 0.05,
) -> str:
    lines = [
        "## 8. Regression Results",
        "",
        "| Variable | Coefficient | Std. Error | t-stat | p-value | 95% CI | Sig. |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in coefficients:
        ci = f"[{_fmt(c.ci_lower)}, {_fmt(c.ci_upper)}]"
        lines.append(
            f"| {c.variable} | {_fmt(c.coefficient)} | {_fmt(c.std_error)} | "
            f"{_fmt(c.t_stat)} | {_fmt(c.p_value)} | {ci} | {c.significance} |"
        )
    lines += [
        "",
        "*Significance codes: \\*\\*\\* p < 0.01, \\*\\* p < 0.05, \\* p < 0.10*",
        "",
        "**Model fit:**",
    ]
    if fit:
        if fit.r_squared is not None:
            lines.append(f"- R² = {_fmt(fit.r_squared, 3)}")
        if fit.adj_r_squared is not None:
            lines.append(f"- Adjusted R² = {_fmt(fit.adj_r_squared, 3)}")
        if fit.aic is not None:
            lines.append(f"- AIC = {_fmt(fit.aic, 2)}")
        if fit.bic is not None:
            lines.append(f"- BIC = {_fmt(fit.bic, 2)}")
        lines.append(f"- N = {fit.n_obs}")
    lines.append("")
    return "\n".join(lines)


def section_coefficient_interpretation(
    coefficients: list[CoefficientResult],
    dep_var: str,
    primary_iv: str,
    sig_level: float = 0.05,
) -> str:
    is_log_dep = dep_var.startswith("log_")
    lines = ["## 9. Key Coefficient Interpretation", ""]

    primary = next((c for c in coefficients if c.variable == primary_iv), None)
    if primary:
        lines.append(_interpret_coeff(primary, dep_var, sig_level, is_log_dep))
        lines.append("")

    others = [c for c in coefficients if c.variable not in (primary_iv, "Intercept", "const")]
    if others:
        lines.append("**Control variables:**")
        for c in others:
            lines.append(f"- {_interpret_coeff(c, dep_var, sig_level, is_log_dep)}")
        lines.append("")

    return "\n".join(lines)


def section_diagnostics(
    diagnostics: ModelDiagnosticsResponse,
    is_panel: bool,
) -> str:
    lines = ["## 10. Diagnostic Test Summary", ""]

    def _test_row(test: DiagnosticTestResult) -> str:
        if not test.available:
            return f"**{test.name}:** {test.unavailable_reason or 'Not available.'}"
        stat = _fmt(test.statistic) if test.statistic is not None else "—"
        p = _fmt(test.p_value) if test.p_value is not None else "—"
        return f"**{test.name}:** statistic = {stat}, p-value = {p}. {test.interpretation}"

    if not is_panel:
        lines.append(_test_row(diagnostics.breusch_pagan))
        lines.append("")
    lines.append(_test_row(diagnostics.jarque_bera))
    lines.append("")
    lines.append(_test_row(diagnostics.durbin_watson))
    lines.append("")

    if diagnostics.hausman.available:
        h = diagnostics.hausman
        lines.append(
            f"**Hausman Test:** χ² = {_fmt(h.statistic)}, df = {h.degrees_of_freedom}, "
            f"p-value = {_fmt(h.p_value)}. {h.recommendation or ''}"
        )
    else:
        lines.append(f"**Hausman Test:** {diagnostics.hausman.unavailable_reason or 'Not available.'}")
    lines.append("")

    if diagnostics.vif:
        lines.append("**Variance Inflation Factors (VIF):**")
        lines.append("")
        lines.append("| Variable | VIF | Risk Level |")
        lines.append("|---|---|---|")
        for v in diagnostics.vif:
            lines.append(f"| {v.variable} | {_fmt(v.vif, 2)} | {v.risk_level} |")
        lines.append("")

    return "\n".join(lines)


def section_coefficient_stability(stability_entries) -> str:
    if not stability_entries:
        return ""
    lines = [
        "## 11. Coefficient Stability Across Specifications",
        "",
        "> Consistency across model specifications may indicate stability under the "
        "tested specifications, but does not independently establish causality.",
        "",
        "| Model | Coefficient | Std. Error | p-value | 95% CI | Sig. | Direction |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in stability_entries:
        ci = f"[{_fmt(e.ci_lower)}, {_fmt(e.ci_upper)}]"
        lines.append(
            f"| {e.model_label} | {_fmt(e.coefficient)} | {_fmt(e.std_error)} | "
            f"{_fmt(e.p_value)} | {ci} | {e.significance} | {e.direction} |"
        )
    lines.append("")
    return "\n".join(lines)


def section_limitations(model_label: str, warnings: list[str]) -> str:
    lines = [
        "## 12. Robustness and Model Limitations",
        "",
        f"This analysis uses {model_label}. The following limitations and caveats apply:",
        "",
    ]
    for w in warnings:
        lines.append(f"- {w}")
    if not warnings:
        lines.append("- No specific warnings were generated for this specification.")
    lines.append("")
    return "\n".join(lines)


def section_causal_warning() -> str:
    return "\n".join([
        "## 13. Causal Interpretation Warning",
        "",
        f"> **{CAUSAL_LANGUAGE_DISCLAIMER}**",
        "",
        "All coefficient interpretations in this report use language such as "
        '"is associated with" and "is estimated to be" rather than "causes" or '
        '"proves." This is intentional and reflects standard econometric practice '
        "for observational data.",
        "",
    ])


def section_reproducibility(
    *,
    source_id: str,
    source_type: str,
    dataset_filename: str,
    created_at: str,
    software_versions: dict[str, str] | None = None,
) -> str:
    lines = [
        "## 14. Reproducibility Information",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Source type | {source_type} |",
        f"| Source ID | `{source_id}` |",
        f"| Dataset | {dataset_filename} |",
        f"| Report generated | {created_at} |",
    ]
    if software_versions:
        for pkg, ver in software_versions.items():
            lines.append(f"| {pkg} | {ver} |")
    lines.append("")
    lines.append(
        "To reproduce this analysis, load the same dataset, apply the listed "
        "transformations, and re-run with the recorded model specification."
    )
    lines.append("")
    return "\n".join(lines)


def section_appendix(transformation_log: list, config_dict: dict | None) -> str:
    lines = ["## Appendix: Transformation Log and Model Configuration", ""]
    if transformation_log:
        lines.append("### Transformation Log")
        lines.append("")
        for entry in transformation_log:
            step = getattr(entry, "step", "?")
            op = getattr(entry, "operation", "")
            cols = getattr(entry, "columns", [])
            params = getattr(entry, "parameters", {})
            r_before = getattr(entry, "rows_before", "?")
            r_after = getattr(entry, "rows_after", "?")
            created = getattr(entry, "created_columns", [])
            lines.append(f"**Step {step}:** `{op}`")
            lines.append(f"- Columns: `{', '.join(cols)}`")
            if params:
                lines.append(f"- Parameters: `{params}`")
            lines.append(f"- Rows before: {r_before}, after: {r_after}")
            if created:
                lines.append(f"- New columns: `{', '.join(created)}`")
            lines.append("")
    if config_dict:
        import json
        lines += ["### Model Configuration", "", "```json", json.dumps(config_dict, indent=2, default=str), "```", ""]
    return "\n".join(lines)
