"""Orchestrates publication-ready export generation.

Coordinates table generators, figure generators, appendix, and format-specific
exporters (DOCX, LaTeX, Markdown, HTML, JSON). All data comes from persisted
analysis/comparison/report artifacts.
"""
from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.analysis.econometric_rules import CAUSAL_LANGUAGE_DISCLAIMER
import app.core.config as _config
from app.core.errors import ModelNotFoundError, ValidationAppError
from app.reports.academic_tables import (
    comparison_table_md,
    descriptive_stats_table_md,
    diagnostic_summary_table_md,
    single_model_table_md,
    stability_table_md,
    variable_definition_table_md,
)
from app.reports.academic_figures import (
    generate_actual_vs_predicted,
    generate_coefficient_plot,
    generate_correlation_heatmap,
    generate_residual_plot,
    generate_stability_chart,
)
from app.reports.appendix_generator import (
    generate_methodology_section,
    generate_reproducibility_appendix,
)
from app.reports.docx_generator import generate_docx
from app.reports.latex_generator import generate_latex
from app.reports.report_generator import _markdown_to_html, _wrap_html
from app.schemas.modeling import AnalysisResult, ModelDiagnosticsResponse
from app.schemas.comparison import ComparisonResult
from app.schemas.publication_export import (
    ExportFormat,
    FigureMetadata,
    PublicationExportConfig,
    PublicationExportResult,
)
from app.storage.repositories import (
    analysis_repository,
    comparison_repository,
    report_repository,
    dataset_repository,
)


def _export_dir(export_id: str) -> Path:
    d = _config.settings.artifact_dir / "publication_exports" / export_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _figures_dir(export_id: str) -> Path:
    d = _export_dir(export_id) / "figures"
    d.mkdir(exist_ok=True)
    return d


def _build_markdown(
    config: PublicationExportConfig,
    result: AnalysisResult | None,
    diagnostics: ModelDiagnosticsResponse | None,
    comparison: ComparisonResult | None,
    dataset_checksum: str | None,
) -> tuple[str, list[str]]:
    sections: list[str] = []
    section_names: list[str] = []

    sections.append(f"# {config.title}\n")
    section_names.append("Title")
    if config.subtitle:
        sections.append(f"*{config.subtitle}*\n")

    if config.include_variable_table:
        if result:
            vs = result.variable_selection
        elif comparison:
            vs = comparison.variable_selection
        else:
            vs = None
        if vs:
            sections.append(variable_definition_table_md(
                dep_var=vs.dependent_variable,
                primary_iv=vs.primary_independent_variable,
                controls=vs.control_variables,
                entity_col=vs.entity_column,
                time_col=vs.time_column,
            ))
            section_names.append("Variable Definitions")

    if config.include_descriptive_statistics and diagnostics:
        stats = diagnostics.descriptive_stats
        if stats:
            sections.append(descriptive_stats_table_md(stats))
            section_names.append("Descriptive Statistics")

    if config.include_regression_table and result:
        sections.append(single_model_table_md(result, diagnostics, config.selected_table_style))
        section_names.append("Regression Table")

    if config.include_model_comparison and comparison:
        sections.append(comparison_table_md(comparison, config.selected_table_style))
        section_names.append("Model Comparison")

        if comparison.coefficient_stability:
            sections.append(stability_table_md(comparison.coefficient_stability))
            section_names.append("Coefficient Stability")

    if config.include_diagnostics and diagnostics:
        sections.append(diagnostic_summary_table_md(diagnostics))
        section_names.append("Diagnostic Summary")

    if config.include_methodology_section:
        sections.append(generate_methodology_section(config, result, comparison))
        section_names.append("Methodology")

    if config.include_limitations_section:
        sections.append(
            "## Limitations\n\n"
            "The results reported in this document describe statistical associations "
            "under the selected model specifications. They should not be interpreted "
            "as causal effects without additional identification assumptions and "
            "theoretical justification.\n"
        )
        section_names.append("Limitations")

    if config.include_reproducibility_appendix:
        tlog = result.transformation_log if result else None
        sections.append(generate_reproducibility_appendix(
            config, result, comparison, dataset_checksum, tlog,
        ))
        section_names.append("Reproducibility Appendix")

    return "\n\n".join(sections), section_names


def _generate_figures(
    config: PublicationExportConfig,
    export_id: str,
    result: AnalysisResult | None,
    diagnostics: ModelDiagnosticsResponse | None,
    comparison: ComparisonResult | None,
) -> list[FigureMetadata]:
    if not config.include_figures:
        return []

    fig_dir = _figures_dir(export_id)
    figs: list[FigureMetadata] = []

    if result:
        for gen in (generate_coefficient_plot, generate_residual_plot, generate_actual_vs_predicted):
            fig = gen(result, fig_dir)
            if fig:
                figs.append(fig)

    if diagnostics:
        fig = generate_correlation_heatmap(diagnostics, fig_dir)
        if fig:
            figs.append(fig)

    if comparison:
        fig = generate_stability_chart(comparison, fig_dir)
        if fig:
            figs.append(fig)

    return figs


def generate_publication_export(
    config: PublicationExportConfig,
) -> PublicationExportResult:
    export_id = str(uuid.uuid4())
    out = _export_dir(export_id)

    result: AnalysisResult | None = None
    diagnostics: ModelDiagnosticsResponse | None = None
    comparison: ComparisonResult | None = None
    dataset_checksum: str | None = None

    if config.source_type == "analysis":
        rec = analysis_repository.get(config.source_id)
        result = rec.result
        diagnostics = rec.diagnostics
        try:
            ds = dataset_repository.get(result.dataset_id)
            dataset_checksum = getattr(ds, "checksum", None)
        except Exception:
            pass

    elif config.source_type == "comparison":
        rec = comparison_repository.get(config.source_id)
        comparison = rec.result
        try:
            ds = dataset_repository.get(comparison.dataset_id)
            dataset_checksum = getattr(ds, "checksum", None)
        except Exception:
            pass

    elif config.source_type == "report":
        rec = report_repository.get(config.source_id)
        artifact = rec.artifact
        md_content = artifact.markdown_content
        html_content = artifact.html_content
        figs: list[FigureMetadata] = []
        available: list[ExportFormat] = []

        if "markdown" in config.output_formats:
            (out / "report.md").write_text(md_content, encoding="utf-8")
            available.append("markdown")
        if "html" in config.output_formats:
            (out / "report.html").write_text(html_content, encoding="utf-8")
            available.append("html")
        if "json" in config.output_formats:
            (out / "report.json").write_text(
                json.dumps(artifact.model_dump(mode="json"), indent=2, default=str),
                encoding="utf-8",
            )
            available.append("json")

        return PublicationExportResult(
            export_id=export_id,
            project_id=config.project_id,
            source_type=config.source_type,
            source_id=config.source_id,
            title=config.title,
            created_at=datetime.now(timezone.utc),
            available_formats=available,
            figures=[],
            sections_included=artifact.sections_included,
            disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
        )
    else:
        raise ValidationAppError(f"Unsupported source_type: '{config.source_type}'")

    md_content, section_names = _build_markdown(
        config, result, diagnostics, comparison, dataset_checksum,
    )
    figs = _generate_figures(config, export_id, result, diagnostics, comparison)

    available_formats: list[ExportFormat] = []

    if "markdown" in config.output_formats:
        (out / "report.md").write_text(md_content, encoding="utf-8")
        available_formats.append("markdown")

    if "html" in config.output_formats:
        html = _wrap_html(_markdown_to_html(md_content), config.title)
        (out / "report.html").write_text(html, encoding="utf-8")
        available_formats.append("html")

    if "docx" in config.output_formats:
        fig_dir = _figures_dir(export_id) if figs else None
        docx_bytes = generate_docx(md_content, config, figs, fig_dir)
        (out / "report.docx").write_bytes(docx_bytes)
        available_formats.append("docx")

    if "latex" in config.output_formats:
        latex_dir = out / "latex"
        generate_latex(md_content, config, figs, latex_dir)
        if figs:
            for fig in figs:
                src = _figures_dir(export_id) / fig.filename
                dst = latex_dir / "figures" / fig.filename
                if src.exists():
                    shutil.copy2(str(src), str(dst))
        available_formats.append("latex")

    if "json" in config.output_formats:
        export_data = {
            "export_id": export_id,
            "config": config.model_dump(mode="json"),
            "sections": section_names,
            "markdown": md_content,
            "figures": [f.model_dump(mode="json") for f in figs],
        }
        (out / "report.json").write_text(
            json.dumps(export_data, indent=2, default=str),
            encoding="utf-8",
        )
        available_formats.append("json")

    return PublicationExportResult(
        export_id=export_id,
        project_id=config.project_id,
        source_type=config.source_type,
        source_id=config.source_id,
        title=config.title,
        created_at=datetime.now(timezone.utc),
        available_formats=available_formats,
        figures=figs,
        sections_included=section_names,
        disclaimer=CAUSAL_LANGUAGE_DISCLAIMER,
    )


def get_export_file(export_id: str, fmt: ExportFormat) -> Path:
    base = _export_dir(export_id)
    ext_map: dict[str, str] = {
        "markdown": "report.md",
        "html": "report.html",
        "docx": "report.docx",
        "json": "report.json",
        "latex": "latex/main.tex",
    }
    fname = ext_map.get(fmt)
    if not fname:
        raise ValidationAppError(f"Unknown export format: '{fmt}'")
    path = base / fname
    if not path.exists():
        raise ModelNotFoundError(
            f"Export file for format '{fmt}' not found. "
            f"Was this format included in the export request?"
        )
    return path
