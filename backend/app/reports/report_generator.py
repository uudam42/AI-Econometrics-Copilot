"""Research report generator.

Consumes an AnalysisResult + ModelDiagnosticsResponse (single-model)
or a ComparisonResult (multi-model). Produces Markdown and HTML outputs.

No LLM is involved. All narrative text is deterministic based on the
pre-computed statistical results.
"""
from __future__ import annotations

import importlib
import uuid
from datetime import datetime, timezone
from html import escape

from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER
from app.reports.report_sections import (
    section_appendix,
    section_causal_warning,
    section_coefficient_interpretation,
    section_coefficient_stability,
    section_comparison_table,
    section_dataset_overview,
    section_diagnostics,
    section_limitations,
    section_metadata,
    section_model_specification,
    section_recommendation,
    section_regression_results,
    section_reproducibility,
    section_title,
    section_transformation_log,
    section_variable_definitions,
)
from app.schemas.comparison import ComparisonResult
from app.schemas.modeling import AnalysisResult, ModelDiagnosticsResponse
from app.schemas.reports import ReportArtifact, ReportGenerationRequest, SourceType

_WRITING_RULES_VERSION = "1.0"

_MODEL_LABELS = {
    "ols": "OLS (Ordinary Least Squares)",
    "robust_ols": "Robust OLS (HC1 Standard Errors)",
    "pooled_ols": "Pooled OLS",
    "fixed_effects": "Fixed Effects (Within Estimator)",
    "random_effects": "Random Effects (GLS)",
    "two_way_fixed_effects": "Two-Way Fixed Effects",
}


def _software_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for pkg in ("pandas", "numpy", "statsmodels", "scipy", "linearmodels"):
        try:
            mod = importlib.import_module(pkg)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"
    return versions


def _markdown_to_html(md: str) -> str:
    """Minimal Markdown → HTML conversion for report delivery.

    Only converts the constructs used in report_sections.py.
    For a richer rendering, replace with python-markdown.
    """
    import re

    lines = md.split("\n")
    html_lines: list[str] = []
    in_table = False
    in_code = False

    for line in lines:
        # Code fence
        if line.strip().startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                lang = line.strip()[3:].strip()
                html_lines.append(f'<pre><code class="language-{lang}">')
                in_code = True
            continue
        if in_code:
            html_lines.append(escape(line))
            continue

        # Table rows
        if line.startswith("|"):
            if not in_table:
                html_lines.append("<table>")
                in_table = True
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(re.fullmatch(r"-+", c.replace(":", "")) for c in cells if c):
                # separator row → becomes <thead> / <tbody> split
                html_lines.append("</thead><tbody>")
                continue
            tag = "th" if not any("</tbody>" in l for l in html_lines[-5:]) and "<thead>" not in "".join(html_lines[-5:]) and in_table else "td"
            if "<thead>" not in "".join(html_lines):
                html_lines.append("<thead><tr>")
                tag = "th"
            else:
                html_lines.append("<tr>")
            for cell in cells:
                html_lines.append(f"  <{tag}>{_inline_md(cell)}</{tag}>")
            html_lines.append("</tr>")
            continue
        else:
            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False

        # Headings
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            html_lines.append(f"<h{level}>{_inline_md(m.group(2))}</h{level}>")
            continue

        # Blockquote
        if line.startswith(">"):
            html_lines.append(f"<blockquote>{_inline_md(line[1:].strip())}</blockquote>")
            continue

        # Unordered list
        if re.match(r"^[-*]\s", line):
            html_lines.append(f"<li>{_inline_md(line[2:])}</li>")
            continue

        # Horizontal rule
        if re.fullmatch(r"-{3,}", line.strip()):
            html_lines.append("<hr>")
            continue

        # Blank line
        if not line.strip():
            html_lines.append("")
            continue

        # Paragraph
        html_lines.append(f"<p>{_inline_md(line)}</p>")

    if in_table:
        html_lines.append("</tbody></table>")
    return "\n".join(html_lines)


def _inline_md(text: str) -> str:
    import re
    text = escape(text)
    # Bold (**text** or __text__)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"__(.+?)__", r"<strong>\1</strong>", text)
    # Italic (*text*)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Inline code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # Line break
    text = text.replace("  \n", "<br>").replace("  ", "<br>")
    return text


def _wrap_html(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<style>
  body {{ font-family: Georgia, serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #1a1a1a; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: 8px; }}
  h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 4px; margin-top: 2em; }}
  h3 {{ margin-top: 1.5em; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.9em; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  th {{ background-color: #f5f5f5; font-weight: bold; }}
  blockquote {{ border-left: 4px solid #666; margin: 1em 0; padding: 0.5em 1em; background: #f9f9f9; font-style: italic; }}
  code {{ background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-size: 0.9em; }}
  pre code {{ display: block; padding: 1em; background: #f5f5f5; overflow-x: auto; }}
  li {{ margin: 0.3em 0; }}
  .disclaimer {{ border: 1px solid #e8a000; background: #fff8e6; padding: 12px 16px; border-radius: 4px; margin-top: 2em; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def generate_from_analysis(
    req: ReportGenerationRequest,
    result: AnalysisResult,
    diagnostics: ModelDiagnosticsResponse,
) -> ReportArtifact:
    """Generate a report from a single analysis artifact."""
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    model_label = _MODEL_LABELS.get(result.model_type, result.model_type)
    title = req.title or f"Econometric Analysis: {result.variable_selection.primary_independent_variable} → {result.variable_selection.dependent_variable}"
    rq = req.research_question

    is_panel = result.model_type in ("pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects")
    vs = result.variable_selection
    dep_var = vs.dependent_variable
    primary_iv = vs.primary_independent_variable
    controls = vs.control_variables

    sections = [
        section_title(title, rq),
        section_metadata(
            analysis_id=result.analysis_id,
            dataset_filename=result.dataset_filename,
            created_at=result.created_at.isoformat(),
            model_label=model_label,
        ),
        section_dataset_overview(
            dataset_filename=result.dataset_filename,
            n_rows=result.fit.n_obs,
            n_cols=None,
            structure="Panel" if is_panel else "Cross-sectional",
        ),
        section_variable_definitions(dep_var, primary_iv, controls, vs.entity_column, vs.time_column),
        section_transformation_log(result.transformation_log),
        section_model_specification(
            model_label=model_label,
            formula=result.formula,
            se_type=result.model_metadata.get("cov_type"),
            n_obs=result.fit.n_obs,
        ),
        section_regression_results(result.coefficients, result.fit, req.significance_level),
        section_coefficient_interpretation(result.coefficients, dep_var, primary_iv, req.significance_level),
        section_diagnostics(diagnostics, is_panel),
        section_limitations(
            model_label,
            warnings=result.recommendation.warnings if result.recommendation else [],
        ),
        section_causal_warning(),
        section_reproducibility(
            source_id=result.analysis_id,
            source_type="Analysis",
            dataset_filename=result.dataset_filename,
            created_at=now.isoformat(),
            software_versions=_software_versions(),
        ),
    ]

    if req.include_appendix:
        sections.append(
            section_appendix(
                result.transformation_log,
                result.variable_selection.model_dump(),
            )
        )

    sections_included = [
        "Title", "Metadata", "Dataset Overview", "Variable Definitions",
        "Transformations", "Model Specification", "Regression Results",
        "Coefficient Interpretation", "Diagnostic Summary", "Limitations",
        "Causal Warning", "Reproducibility",
    ]
    if req.include_appendix:
        sections_included.append("Appendix")

    md = "\n".join(sections)
    html = _wrap_html(_markdown_to_html(md), title)

    return ReportArtifact(
        report_id=report_id,
        source_type="analysis",
        source_id=result.analysis_id,
        title=title,
        research_question=rq,
        created_at=now,
        significance_level=req.significance_level,
        sections_included=sections_included,
        markdown_content=md,
        html_content=html,
        writing_rules_version=_WRITING_RULES_VERSION,
        disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
    )


def generate_from_comparison(
    req: ReportGenerationRequest,
    comparison: ComparisonResult,
    # diagnostics for the recommended model (if available from a linked analysis)
    diagnostics: ModelDiagnosticsResponse | None = None,
) -> ReportArtifact:
    """Generate a report from a comparison artifact."""
    report_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    rec_type = comparison.recommendation.recommended_model
    model_label = _MODEL_LABELS.get(rec_type, rec_type)
    title = req.title or f"Model Comparison Report: {comparison.variable_selection.primary_independent_variable} → {comparison.variable_selection.dependent_variable}"
    rq = req.research_question

    vs = comparison.variable_selection
    dep_var = vs.dependent_variable
    primary_iv = vs.primary_independent_variable
    controls = vs.control_variables

    # Find the recommended model entry for formula / fit
    rec_entry = next((m for m in comparison.models if m.model_type == rec_type and m.status == "completed"), None)
    rec_formula = rec_entry.formula if rec_entry else "—"
    rec_se_type = rec_entry.standard_error_type if rec_entry else None
    rec_n_obs = rec_entry.fit_metrics.n_obs if rec_entry and rec_entry.fit_metrics else None

    # Collect warnings from recommendation
    all_warnings = list(comparison.recommendation.warnings)
    for m in comparison.models:
        for w in m.warnings:
            if w not in all_warnings:
                all_warnings.append(w)

    is_panel = vs.entity_column is not None and vs.time_column is not None

    sections = [
        section_title(title, rq),
        section_metadata(
            comparison_id=comparison.comparison_id,
            dataset_filename=comparison.dataset_filename,
            created_at=comparison.created_at.isoformat(),
            model_label=f"Comparison across {len(comparison.models)} model(s)",
        ),
        section_dataset_overview(
            dataset_filename=comparison.dataset_filename,
            n_rows=rec_n_obs,
            n_cols=None,
            structure="Panel" if is_panel else "Cross-sectional",
        ),
        section_variable_definitions(dep_var, primary_iv, controls, vs.entity_column, vs.time_column),
        "## 4. Transformation Summary\n\n" + comparison.transformation_summary + "\n",
        section_comparison_table(comparison.models),
        section_recommendation(comparison.recommendation),
        section_model_specification(
            model_label=model_label,
            formula=rec_formula or "—",
            se_type=rec_se_type,
            n_obs=rec_n_obs,
        ),
        section_coefficient_stability(comparison.coefficient_stability),
    ]

    if diagnostics is not None:
        sections.append(section_diagnostics(diagnostics, is_panel))

    sections += [
        section_limitations(model_label, all_warnings),
        section_causal_warning(),
        section_reproducibility(
            source_id=comparison.comparison_id,
            source_type="Comparison",
            dataset_filename=comparison.dataset_filename,
            created_at=now.isoformat(),
            software_versions=_software_versions(),
        ),
    ]

    if req.include_appendix:
        sections.append(
            section_appendix([], vs.model_dump())
        )

    sections_included = [
        "Title", "Metadata", "Dataset Overview", "Variable Definitions",
        "Transformation Summary", "Model Comparison Table", "Recommendation",
        "Model Specification", "Coefficient Stability", "Limitations",
        "Causal Warning", "Reproducibility",
    ]
    if diagnostics:
        sections_included.append("Diagnostics")
    if req.include_appendix:
        sections_included.append("Appendix")

    md = "\n".join(sections)
    html = _wrap_html(_markdown_to_html(md), title)

    return ReportArtifact(
        report_id=report_id,
        source_type="comparison",
        source_id=comparison.comparison_id,
        title=title,
        research_question=rq,
        created_at=now,
        significance_level=req.significance_level,
        sections_included=sections_included,
        markdown_content=md,
        html_content=html,
        writing_rules_version=_WRITING_RULES_VERSION,
        disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
    )
