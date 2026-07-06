"""Publication-ready figure generators using matplotlib.

Generates PNG figures from real analysis artifacts. No seaborn.
Each figure includes a standardized caption and metadata.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from app.schemas.modeling import AnalysisResult, ModelDiagnosticsResponse
from app.schemas.comparison import ComparisonResult
from app.schemas.publication_export import FigureMetadata

_FIG_DPI = 150
_FIG_SIZE = (8, 5)


def _save_fig(fig: plt.Figure, path: Path) -> None:
    fig.savefig(str(path), dpi=_FIG_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generate_coefficient_plot(
    result: AnalysisResult,
    output_dir: Path,
) -> FigureMetadata | None:
    coeffs = [c for c in result.coefficients if c.variable not in ("Intercept", "const")]
    if not coeffs:
        return None

    fig, ax = plt.subplots(figsize=_FIG_SIZE)
    names = [c.variable for c in coeffs]
    values = [c.coefficient for c in coeffs]
    ci_low = [c.ci_lower for c in coeffs]
    ci_high = [c.ci_upper for c in coeffs]
    errors = [[v - lo for v, lo in zip(values, ci_low)],
              [hi - v for v, hi in zip(values, ci_high)]]

    y_pos = range(len(names))
    ax.barh(y_pos, values, xerr=errors, color="#4A7C8E", capsize=4, height=0.5, alpha=0.85)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=9)
    ax.axvline(x=0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Coefficient Estimate", fontsize=10)
    ax.set_title("Estimated Coefficients with 95% Confidence Intervals", fontsize=11)
    ax.invert_yaxis()
    fig.tight_layout()

    fname = "fig_coefficient_plot.png"
    _save_fig(fig, output_dir / fname)
    return FigureMetadata(
        figure_id=str(uuid.uuid4()),
        figure_type="coefficient_plot",
        caption=(
            "Estimated coefficients and 95% confidence intervals for the selected "
            "model specification."
        ),
        filename=fname,
        source_artifact_id=result.analysis_id,
        variables=[c.variable for c in coeffs],
        model_type=result.model_type,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_residual_plot(
    result: AnalysisResult,
    output_dir: Path,
) -> FigureMetadata | None:
    if not result.plot_data:
        return None

    fig, ax = plt.subplots(figsize=_FIG_SIZE)
    fitted = result.plot_data.fitted_values
    residuals = result.plot_data.residuals
    ax.scatter(fitted, residuals, alpha=0.4, s=12, color="#4A7C8E", edgecolors="none")
    ax.axhline(y=0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Fitted Values", fontsize=10)
    ax.set_ylabel("Residuals", fontsize=10)
    ax.set_title("Residuals vs. Fitted Values", fontsize=11)
    fig.tight_layout()

    fname = "fig_residual_plot.png"
    _save_fig(fig, output_dir / fname)
    return FigureMetadata(
        figure_id=str(uuid.uuid4()),
        figure_type="residual_fitted",
        caption="Residuals plotted against fitted values for the selected model specification.",
        filename=fname,
        source_artifact_id=result.analysis_id,
        variables=[],
        model_type=result.model_type,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_actual_vs_predicted(
    result: AnalysisResult,
    output_dir: Path,
) -> FigureMetadata | None:
    if not result.plot_data:
        return None

    fig, ax = plt.subplots(figsize=_FIG_SIZE)
    actual = result.plot_data.actual_values
    fitted = result.plot_data.fitted_values
    ax.scatter(fitted, actual, alpha=0.4, s=12, color="#4A7C8E", edgecolors="none")
    mn = min(min(actual), min(fitted))
    mx = max(max(actual), max(fitted))
    ax.plot([mn, mx], [mn, mx], color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Predicted", fontsize=10)
    ax.set_ylabel("Actual", fontsize=10)
    ax.set_title("Actual vs. Predicted Values", fontsize=11)
    fig.tight_layout()

    fname = "fig_actual_vs_predicted.png"
    _save_fig(fig, output_dir / fname)
    return FigureMetadata(
        figure_id=str(uuid.uuid4()),
        figure_type="actual_vs_predicted",
        caption="Actual values plotted against model-predicted values.",
        filename=fname,
        source_artifact_id=result.analysis_id,
        variables=[],
        model_type=result.model_type,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_correlation_heatmap(
    diagnostics: ModelDiagnosticsResponse,
    output_dir: Path,
) -> FigureMetadata | None:
    cm = diagnostics.correlation_matrix
    if not cm.variables or not cm.matrix:
        return None

    matrix = np.array(cm.matrix, dtype=float)
    fig, ax = plt.subplots(figsize=(max(6, len(cm.variables) * 0.8),
                                     max(5, len(cm.variables) * 0.6)))
    im = ax.imshow(matrix, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cm.variables)))
    ax.set_yticks(range(len(cm.variables)))
    ax.set_xticklabels(cm.variables, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(cm.variables, fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Pearson Correlation")
    ax.set_title("Correlation Matrix", fontsize=11)
    fig.tight_layout()

    fname = "fig_correlation_heatmap.png"
    _save_fig(fig, output_dir / fname)
    return FigureMetadata(
        figure_id=str(uuid.uuid4()),
        figure_type="correlation_heatmap",
        caption="Pearson correlation matrix for the variables used in the analysis.",
        filename=fname,
        source_artifact_id=diagnostics.analysis_id,
        variables=cm.variables,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def generate_stability_chart(
    comparison: ComparisonResult,
    output_dir: Path,
) -> FigureMetadata | None:
    entries = [e for e in comparison.coefficient_stability if e.coefficient is not None]
    if not entries:
        return None

    fig, ax = plt.subplots(figsize=_FIG_SIZE)
    labels = [e.model_label for e in entries]
    values = [e.coefficient for e in entries]
    ci_low = [e.ci_lower or e.coefficient for e in entries]
    ci_high = [e.ci_upper or e.coefficient for e in entries]
    errors = [[v - lo for v, lo in zip(values, ci_low)],
              [hi - v for v, hi in zip(values, ci_high)]]

    x_pos = range(len(labels))
    ax.bar(x_pos, values, yerr=errors, color="#4A7C8E", capsize=5, width=0.5, alpha=0.85)
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    ax.axhline(y=0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_ylabel("Coefficient Estimate", fontsize=10)
    ax.set_title(
        f"Coefficient Stability: {comparison.variable_selection.primary_independent_variable}",
        fontsize=11,
    )
    fig.tight_layout()

    fname = "fig_stability_chart.png"
    _save_fig(fig, output_dir / fname)
    return FigureMetadata(
        figure_id=str(uuid.uuid4()),
        figure_type="coefficient_stability",
        caption=(
            "Coefficient stability for the primary explanatory variable across "
            "completed model specifications. Stability across tested specifications "
            "does not establish causality."
        ),
        filename=fname,
        source_artifact_id=comparison.comparison_id,
        variables=[comparison.variable_selection.primary_independent_variable],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
