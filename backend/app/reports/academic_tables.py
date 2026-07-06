"""Publication-ready regression table generators.

All values come from persisted analysis/comparison artifacts.
This module NEVER fabricates coefficients, standard errors, or statistics.
"""
from __future__ import annotations

from typing import Literal

from app.schemas.comparison import (
    ComparisonResult,
    CoefficientStabilityEntry,
    ModelComparisonEntry,
)
from app.schemas.modeling import (
    AnalysisResult,
    CoefficientResult,
    DescriptiveStats,
    ModelDiagnosticsResponse,
    VIFResult,
)

TableStyle = Literal["academic", "compact", "detailed"]

_SIG_NOTE = (
    "Standard errors are reported in parentheses. "
    "Statistical significance is indicated by conventional stars: "
    "*** p < 0.01, ** p < 0.05, * p < 0.10. "
    "The reported estimates describe statistical associations under the selected "
    "model specification and should not be interpreted as causal effects without "
    "additional identification assumptions."
)


def _fmt(v: float | None, d: int = 4) -> str:
    if v is None:
        return "—"
    return f"{v:.{d}f}"


# ---------------------------------------------------------------------------
# Single-model regression table
# ---------------------------------------------------------------------------

def single_model_table_md(
    result: AnalysisResult,
    diagnostics: ModelDiagnosticsResponse | None = None,
    style: TableStyle = "academic",
) -> str:
    dep_var = result.variable_selection.dependent_variable
    lines = [
        f"**Table: Regression Results — {dep_var}**",
        "",
    ]

    if style == "detailed":
        lines += [
            "| Variable | Coefficient | Std. Error | t-stat | p-value | 95% CI | Sig. |",
            "|---|---|---|---|---|---|---|",
        ]
        for c in result.coefficients:
            ci = f"[{_fmt(c.ci_lower)}, {_fmt(c.ci_upper)}]"
            lines.append(
                f"| {c.variable} | {_fmt(c.coefficient)} | ({_fmt(c.std_error)}) | "
                f"{_fmt(c.t_stat)} | {_fmt(c.p_value)} | {ci} | {c.significance} |"
            )
    else:
        lines += [
            "| Variable | Coefficient |",
            "|---|---|",
        ]
        for c in result.coefficients:
            sig = c.significance
            lines.append(f"| {c.variable} | {_fmt(c.coefficient)}{sig} |")
            lines.append(f"| | ({_fmt(c.std_error)}) |")

    lines += ["", "| Statistic | Value |", "|---|---|"]
    lines.append(f"| Observations | {result.fit.n_obs} |")
    if result.fit.r_squared is not None:
        lines.append(f"| R² | {_fmt(result.fit.r_squared, 3)} |")
    if result.fit.adj_r_squared is not None:
        lines.append(f"| Adjusted R² | {_fmt(result.fit.adj_r_squared, 3)} |")
    if result.fit.aic is not None:
        lines.append(f"| AIC | {_fmt(result.fit.aic, 2)} |")
    if result.fit.bic is not None:
        lines.append(f"| BIC | {_fmt(result.fit.bic, 2)} |")

    meta = result.model_metadata or {}
    if meta.get("entity_effects"):
        lines.append("| Entity Effects | Yes |")
    if meta.get("time_effects"):
        lines.append("| Time Effects | Yes |")
    se_type = meta.get("se_type", "standard")
    lines.append(f"| Standard Errors | {se_type} |")
    lines += ["", f"*Note: {_SIG_NOTE}*", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Multi-model comparison table
# ---------------------------------------------------------------------------

def comparison_table_md(
    comparison: ComparisonResult,
    style: TableStyle = "academic",
) -> str:
    completed = [m for m in comparison.models if m.status == "completed"]
    if not completed:
        return "*No completed models available for comparison table.*\n"

    all_vars: list[str] = []
    model_coeffs: dict[str, dict[str, CoefficientStabilityEntry]] = {}

    for entry in comparison.coefficient_stability:
        model_coeffs.setdefault(entry.model_label, {})[
            comparison.variable_selection.primary_independent_variable
        ] = entry

    header_labels = [f"({i+1})" for i in range(len(completed))]
    lines = [
        "**Table: Model Comparison**",
        "",
        "| | " + " | ".join(header_labels) + " |",
        "|---" + "|---" * len(completed) + "|",
        "| | " + " | ".join(m.model_label for m in completed) + " |",
    ]

    primary_iv = comparison.variable_selection.primary_independent_variable
    row_coef = [f"| {primary_iv} "]
    row_se = ["| "]
    for m in completed:
        entry = None
        for s in comparison.coefficient_stability:
            if s.model_label == m.model_label:
                entry = s
                break
        if entry and entry.coefficient is not None:
            row_coef.append(f"| {_fmt(entry.coefficient)}{entry.significance} ")
            row_se.append(f"| ({_fmt(entry.std_error)}) ")
        else:
            row_coef.append("| — ")
            row_se.append("| ")
    lines.append("".join(row_coef) + "|")
    lines.append("".join(row_se) + "|")

    lines.append("| | " + " | ".join("" for _ in completed) + " |")

    row_n = ["| Observations "]
    row_r2 = ["| R² "]
    row_entity = ["| Entity Effects "]
    row_time = ["| Time Effects "]
    row_se_type = ["| Standard Errors "]
    for m in completed:
        fm = m.fit_metrics
        row_n.append(f"| {fm.n_obs if fm and fm.n_obs else '—'} ")
        r2_val = fm.r_squared if fm and fm.r_squared is not None else None
        if r2_val is None and fm:
            r2_val = fm.within_r_squared
        row_r2.append(f"| {_fmt(r2_val, 3) if r2_val is not None else '—'} ")
        row_entity.append(f"| {'Yes' if m.entity_effects else 'No'} ")
        row_time.append(f"| {'Yes' if m.time_effects else 'No'} ")
        row_se_type.append(f"| {m.standard_error_type or 'standard'} ")

    lines.append("".join(row_n) + "|")
    lines.append("".join(row_r2) + "|")
    lines.append("".join(row_entity) + "|")
    lines.append("".join(row_time) + "|")
    lines.append("".join(row_se_type) + "|")

    unavailable = [m for m in comparison.models if m.status != "completed"]
    if unavailable:
        lines += ["", "*Unavailable models:*"]
        for m in unavailable:
            reason = m.reason or "estimation failed"
            lines.append(f"- {m.model_label}: {reason}")

    lines += ["", f"*Note: {_SIG_NOTE}*", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Coefficient stability table
# ---------------------------------------------------------------------------

def stability_table_md(entries: list[CoefficientStabilityEntry]) -> str:
    if not entries:
        return ""
    lines = [
        "**Table: Coefficient Stability Across Specifications**",
        "",
        "| Model | Coefficient | Std. Error | p-value | 95% CI | Sig. | Direction |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in entries:
        ci = f"[{_fmt(e.ci_lower)}, {_fmt(e.ci_upper)}]"
        lines.append(
            f"| {e.model_label} | {_fmt(e.coefficient)} | {_fmt(e.std_error)} | "
            f"{_fmt(e.p_value)} | {ci} | {e.significance} | {e.direction} |"
        )
    lines += [
        "",
        "*Consistency across model specifications may indicate stability under the "
        "tested specifications, but does not independently establish causality.*",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Descriptive statistics table
# ---------------------------------------------------------------------------

def descriptive_stats_table_md(stats: list[DescriptiveStats]) -> str:
    if not stats:
        return ""
    lines = [
        "**Table: Descriptive Statistics**",
        "",
        "| Variable | N | Mean | Std. Dev. | Min | Q25 | Median | Q75 | Max | Missing |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for s in stats:
        lines.append(
            f"| {s.variable} | {s.count} | {_fmt(s.mean, 2)} | {_fmt(s.std, 2)} | "
            f"{_fmt(s.min, 2)} | {_fmt(s.q25, 2)} | {_fmt(s.median, 2)} | "
            f"{_fmt(s.q75, 2)} | {_fmt(s.max, 2)} | {s.missing_count} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Variable definition table
# ---------------------------------------------------------------------------

def variable_definition_table_md(
    dep_var: str,
    primary_iv: str,
    controls: list[str],
    entity_col: str | None = None,
    time_col: str | None = None,
) -> str:
    lines = [
        "**Table: Variable Definitions**",
        "",
        "| Role | Variable |",
        "|---|---|",
        f"| Dependent variable | {dep_var} |",
        f"| Primary independent variable | {primary_iv} |",
    ]
    for c in controls:
        lines.append(f"| Control variable | {c} |")
    if entity_col:
        lines.append(f"| Entity identifier | {entity_col} |")
    if time_col:
        lines.append(f"| Time identifier | {time_col} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Diagnostic summary table
# ---------------------------------------------------------------------------

def diagnostic_summary_table_md(diag: ModelDiagnosticsResponse) -> str:
    lines = [
        "**Table: Diagnostic Summary**",
        "",
        "| Test | Statistic | p-value | Interpretation |",
        "|---|---|---|---|",
    ]

    for test in [diag.breusch_pagan, diag.jarque_bera, diag.durbin_watson]:
        if test.available:
            lines.append(
                f"| {test.name} | {_fmt(test.statistic)} | {_fmt(test.p_value)} | "
                f"{test.interpretation} |"
            )
        else:
            lines.append(
                f"| {test.name} | — | — | {test.unavailable_reason or 'Not available'} |"
            )

    h = diag.hausman
    if h.available:
        lines.append(
            f"| Hausman | {_fmt(h.statistic)} | {_fmt(h.p_value)} | "
            f"{h.recommendation or ''} |"
        )
    else:
        lines.append(f"| Hausman | — | — | {h.unavailable_reason or 'Not available'} |")

    if diag.vif:
        lines += [
            "",
            "**VIF:**",
            "",
            "| Variable | VIF | Risk |",
            "|---|---|---|",
        ]
        for v in diag.vif:
            lines.append(f"| {v.variable} | {_fmt(v.vif, 2)} | {v.risk_level} |")

    lines.append("")
    return "\n".join(lines)
