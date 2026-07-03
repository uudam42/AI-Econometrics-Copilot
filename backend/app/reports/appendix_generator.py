"""Methodology and reproducibility appendix generator.

Produces a deterministic appendix from analysis artifacts — dataset checksum,
transformation log, model configuration, software versions. Never fabricates
content.
"""
from __future__ import annotations

import hashlib
import importlib
from datetime import datetime, timezone

from app.schemas.modeling import AnalysisResult, ModelDiagnosticsResponse
from app.schemas.comparison import ComparisonResult
from app.schemas.publication_export import PublicationExportConfig


def _software_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for pkg in ("pandas", "numpy", "statsmodels", "scipy", "linearmodels", "python-docx"):
        name = pkg.replace("-", "_")
        try:
            mod = importlib.import_module(name)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"
    return versions


def generate_methodology_section(
    config: PublicationExportConfig,
    result: AnalysisResult | None = None,
    comparison: ComparisonResult | None = None,
) -> str:
    lines = ["## Methodology", ""]

    if result:
        vs = result.variable_selection
        lines += [
            "### Variable Selection",
            "",
            f"- **Dependent variable:** {vs.dependent_variable}",
            f"- **Primary independent variable:** {vs.primary_independent_variable}",
        ]
        if vs.control_variables:
            lines.append(f"- **Control variables:** {', '.join(vs.control_variables)}")
        if vs.entity_column:
            lines.append(f"- **Entity identifier:** {vs.entity_column}")
        if vs.time_column:
            lines.append(f"- **Time identifier:** {vs.time_column}")

        lines += [
            "",
            "### Model Specification",
            "",
            f"- **Model type:** {result.model_type}",
            f"- **Formula:** `{result.formula}`",
            f"- **Observations:** {result.fit.n_obs}",
        ]
        meta = result.model_metadata or {}
        if meta.get("cov_type"):
            lines.append(f"- **Standard errors:** {meta['cov_type']}")
        if meta.get("entity_effects"):
            lines.append("- **Entity fixed effects:** Yes")
        if meta.get("time_effects"):
            lines.append("- **Time fixed effects:** Yes")

    elif comparison:
        vs = comparison.variable_selection
        lines += [
            "### Variable Selection",
            "",
            f"- **Dependent variable:** {vs.dependent_variable}",
            f"- **Primary independent variable:** {vs.primary_independent_variable}",
        ]
        if vs.control_variables:
            lines.append(f"- **Control variables:** {', '.join(vs.control_variables)}")

        completed = [m for m in comparison.models if m.status == "completed"]
        lines += [
            "",
            "### Models Estimated",
            "",
        ]
        for m in completed:
            lines.append(f"- {m.model_label} ({m.model_type})")

        rec = comparison.recommendation
        lines += [
            "",
            f"### Model Selection",
            "",
            f"The recommended model is **{rec.recommended_model}** based on "
            f"multi-criteria weighted scoring.",
        ]

    lines += [
        "",
        "### Limitations",
        "",
        "The results reported in this document describe statistical associations "
        "under the selected model specifications. They should not be interpreted "
        "as causal effects without additional identification assumptions and "
        "theoretical justification.",
        "",
    ]
    return "\n".join(lines)


def generate_reproducibility_appendix(
    config: PublicationExportConfig,
    result: AnalysisResult | None = None,
    comparison: ComparisonResult | None = None,
    dataset_checksum: str | None = None,
    transformation_log: list | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    versions = _software_versions()

    lines = [
        "## Appendix: Reproducibility Information",
        "",
        "### Export Metadata",
        "",
        f"- **Export title:** {config.title}",
        f"- **Generated at:** {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Source type:** {config.source_type}",
        f"- **Source ID:** {config.source_id}",
    ]
    if config.project_id:
        lines.append(f"- **Project ID:** {config.project_id}")

    if dataset_checksum:
        lines += [
            "",
            "### Dataset Integrity",
            "",
            f"- **SHA-256 checksum:** `{dataset_checksum}`",
        ]

    if transformation_log:
        lines += [
            "",
            "### Transformation Log",
            "",
            "| Step | Transformation | Parameters |",
            "|---|---|---|",
        ]
        for i, t in enumerate(transformation_log, 1):
            if isinstance(t, dict):
                name = t.get("transformation", t.get("name", "unknown"))
                params = {k: v for k, v in t.items() if k not in ("transformation", "name")}
                lines.append(f"| {i} | {name} | {params or '—'} |")
            else:
                lines.append(f"| {i} | {t} | — |")

    if result:
        meta = result.model_metadata or {}
        lines += [
            "",
            "### Model Configuration",
            "",
            f"- **Model type:** {result.model_type}",
            f"- **Formula:** `{result.formula}`",
        ]
        for k, v in meta.items():
            lines.append(f"- **{k}:** {v}")

    lines += [
        "",
        "### Software Versions",
        "",
        "| Package | Version |",
        "|---|---|",
    ]
    for pkg, ver in versions.items():
        lines.append(f"| {pkg} | {ver} |")

    lines += [
        "",
        "*This appendix is auto-generated from persisted analysis artifacts "
        "and reflects the exact configuration used at the time of analysis.*",
        "",
    ]
    return "\n".join(lines)
