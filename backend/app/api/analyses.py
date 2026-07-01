"""Analysis execution and retrieval endpoints."""
from __future__ import annotations

import importlib
from typing import Any

from fastapi import APIRouter

from app.analysis.model_runner import run_analysis
from app.core.errors import ModelNotFoundError
from app.models.analysis_registry import analysis_registry
from app.models.dataset_registry import registry as dataset_registry
from app.schemas.modeling import (
    AnalysisConfigurationRequest,
    AnalysisExportArtifact,
    AnalysisResult,
    ModelDiagnosticsResponse,
)

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/run", response_model=AnalysisResult)
async def run_analysis_endpoint(
    config: AnalysisConfigurationRequest,
) -> AnalysisResult:
    """Execute a full analysis: transform → model → diagnostics → store."""
    record = dataset_registry.get(config.dataset_id)
    result, diagnostics = run_analysis(config, record)

    ar = analysis_registry.create(
        dataset_id=record.dataset_id,
        dataset_filename=record.filename,
        config=config,
        result=result,
        diagnostics=diagnostics,
        transformation_log=result.transformation_log,
    )

    # Sync the stable registry ID into the result object
    result.analysis_id = ar.analysis_id
    diagnostics.analysis_id = ar.analysis_id
    # Update the stored copies too
    ar.result = result
    ar.diagnostics = diagnostics

    return result


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    record = analysis_registry.get(analysis_id)
    return record.result


@router.get("/{analysis_id}/diagnostics", response_model=ModelDiagnosticsResponse)
async def get_analysis_diagnostics(analysis_id: str) -> ModelDiagnosticsResponse:
    record = analysis_registry.get(analysis_id)
    return record.diagnostics


@router.get("/{analysis_id}/report", response_model=dict)
async def get_analysis_report(analysis_id: str) -> dict:
    """Return a structured narrative report (rule-generated, no LLM)."""
    record = analysis_registry.get(analysis_id)
    result = record.result
    diagnostics = record.diagnostics

    significant_vars = [
        c.variable for c in result.coefficients if c.significance != "" and c.variable != "Intercept"
    ]
    warnings: list[str] = []
    if diagnostics.breusch_pagan.available and diagnostics.breusch_pagan.p_value is not None:
        if diagnostics.breusch_pagan.p_value < 0.05:
            warnings.append(
                "Evidence of heteroskedasticity was detected. Consider robust standard errors."
            )
    if diagnostics.hausman.available and diagnostics.hausman.p_value is not None:
        warnings.append(diagnostics.hausman.recommendation or "")
    high_vif = [v.variable for v in diagnostics.vif if v.risk_level in ("moderate", "severe")]
    if high_vif:
        warnings.append(f"Elevated VIF for: {', '.join(high_vif)}. Multicollinearity may affect estimates.")

    return {
        "analysis_id": analysis_id,
        "model_type": result.model_type,
        "formula": result.formula,
        "n_obs": result.fit.n_obs,
        "r_squared": result.fit.r_squared,
        "significant_variables": significant_vars,
        "warnings": warnings,
        "disclaimer": result.disclaimer,
        "recommendation": result.recommendation.model_dump() if result.recommendation else None,
    }


@router.get("/{analysis_id}/export/json", response_model=AnalysisExportArtifact)
async def export_analysis_json(analysis_id: str) -> AnalysisExportArtifact:
    """Export a complete reproducible analysis artifact as JSON."""
    record = analysis_registry.get(analysis_id)
    result = record.result
    diagnostics = record.diagnostics
    config = record.config

    # Collect software versions
    versions: dict[str, str] = {}
    for pkg in ("pandas", "numpy", "statsmodels", "scipy", "linearmodels"):
        try:
            mod = importlib.import_module(pkg)
            versions[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            versions[pkg] = "not installed"

    diagnostics_summary = {
        "breusch_pagan": diagnostics.breusch_pagan.model_dump(),
        "jarque_bera": diagnostics.jarque_bera.model_dump(),
        "durbin_watson": diagnostics.durbin_watson.model_dump(),
        "hausman": diagnostics.hausman.model_dump(),
        "vif": [v.model_dump() for v in diagnostics.vif],
    }

    return AnalysisExportArtifact(
        analysis_id=analysis_id,
        dataset_id=result.dataset_id,
        dataset_filename=result.dataset_filename,
        created_at=result.created_at,
        model_type=result.model_type,
        formula=result.formula,
        variable_selection=result.variable_selection.model_dump(),
        transformations=[t.model_dump() for t in config.transformations],
        transformation_log=[entry.model_dump() for entry in result.transformation_log],
        coefficients=[c.model_dump() for c in result.coefficients],
        fit=result.fit.model_dump(),
        diagnostics_summary=diagnostics_summary,
        model_metadata=result.model_metadata,
        recommendation=result.recommendation.model_dump() if result.recommendation else None,
        software_versions=versions,
        disclaimer=result.disclaimer,
    )
