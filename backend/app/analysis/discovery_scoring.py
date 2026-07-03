"""Scoring and stability assessment for exploratory findings.

Produces a transparent, inspectable ranking score and stability labels.
"""
from __future__ import annotations

import math

from app.schemas.discovery import (
    CorrectedResult,
    ExploratoryFinding,
    FindingScoreComponent,
    SpecificationResult,
    StabilityAssessment,
    StabilityLabel,
    SupportLevel,
)


def _direction_str(coeff: float | None) -> str:
    if coeff is None:
        return "unavailable"
    if coeff > 1e-10:
        return "positive"
    if coeff < -1e-10:
        return "negative"
    return "zero"


def assess_stability(
    outcome: str,
    predictor: str,
    spec_results: list[SpecificationResult],
    corrected: dict[str, CorrectedResult],
) -> StabilityAssessment:
    completed = [r for r in spec_results if r.status == "completed"]
    n_completed = len(completed)

    if n_completed == 0:
        return StabilityAssessment(
            outcome_variable=outcome,
            primary_predictor=predictor,
            n_specifications=len(spec_results),
            n_completed=0,
            n_corrected_significant=0,
            direction_consistent=False,
            significance_consistent=False,
            stability_label="insufficient_evidence",
            specifications_used=[r.spec_id for r in spec_results],
        )

    directions = [_direction_str(r.coefficient) for r in completed if r.coefficient is not None]
    positive_count = directions.count("positive")
    negative_count = directions.count("negative")
    direction_consistent = (
        positive_count == len(directions) or negative_count == len(directions)
    ) if directions else False

    n_corrected_sig = sum(
        1 for r in completed
        if r.spec_id in corrected and corrected[r.spec_id].passes_threshold
    )

    sig_flags = [r.significance != "" for r in completed]
    significance_consistent = all(sig_flags) or not any(sig_flags)

    coeffs = [r.coefficient for r in completed if r.coefficient is not None]
    coeff_range = [min(coeffs), max(coeffs)] if coeffs else None

    if n_completed < 2:
        label: StabilityLabel = "insufficient_evidence"
    elif direction_consistent and n_corrected_sig >= n_completed * 0.5:
        label = "stable"
    elif direction_consistent:
        label = "partially_stable"
    else:
        label = "sensitive"

    return StabilityAssessment(
        outcome_variable=outcome,
        primary_predictor=predictor,
        n_specifications=len(spec_results),
        n_completed=n_completed,
        n_corrected_significant=n_corrected_sig,
        direction_consistent=direction_consistent,
        significance_consistent=significance_consistent,
        coefficient_range=coeff_range,
        stability_label=label,
        specifications_used=[r.spec_id for r in spec_results],
    )


def _score_data_quality(spec_results: list[SpecificationResult]) -> tuple[float, str]:
    if not spec_results:
        return 0.0, "No completed specifications"
    avg_n = sum(r.n_obs or 0 for r in spec_results) / len(spec_results)
    if avg_n >= 200:
        return 1.0, f"Large sample (avg N={avg_n:.0f})"
    if avg_n >= 50:
        return 0.6, f"Adequate sample (avg N={avg_n:.0f})"
    return 0.3, f"Small sample (avg N={avg_n:.0f})"


def _score_corrected_support(
    stability: StabilityAssessment,
) -> tuple[float, str]:
    if stability.n_completed == 0:
        return 0.0, "No completed specifications"
    ratio = stability.n_corrected_significant / stability.n_completed
    if ratio >= 0.75:
        return 1.0, f"{stability.n_corrected_significant}/{stability.n_completed} pass correction"
    if ratio >= 0.5:
        return 0.6, f"{stability.n_corrected_significant}/{stability.n_completed} pass correction"
    if ratio > 0:
        return 0.3, f"Only {stability.n_corrected_significant}/{stability.n_completed} pass correction"
    return 0.0, "None pass correction"


def _score_direction(stability: StabilityAssessment) -> tuple[float, str]:
    if stability.direction_consistent:
        return 1.0, "Consistent direction across specifications"
    return 0.2, "Direction changes across specifications"


def _score_stability(stability: StabilityAssessment) -> tuple[float, str]:
    mapping = {
        "stable": (1.0, "Stable across tested specifications"),
        "partially_stable": (0.6, "Partially stable across tested specifications"),
        "sensitive": (0.2, "Sensitive to specification choice"),
        "insufficient_evidence": (0.1, "Insufficient evidence for stability assessment"),
    }
    return mapping.get(stability.stability_label, (0.0, "Unknown"))


def _score_diagnostics(spec_results: list[SpecificationResult]) -> tuple[float, str]:
    if not spec_results:
        return 0.0, "No results"
    warning_count = sum(len(r.warnings) for r in spec_results)
    absorbed_count = sum(1 for r in spec_results if r.absorbed_variables)
    if absorbed_count > 0:
        return 0.1, f"Primary variable absorbed in {absorbed_count} specification(s)"
    if warning_count == 0:
        return 1.0, "No diagnostic warnings"
    if warning_count <= len(spec_results):
        return 0.6, f"{warning_count} warning(s) across specifications"
    return 0.3, f"{warning_count} warnings — review diagnostics"


def _score_fit(spec_results: list[SpecificationResult]) -> tuple[float, str]:
    r2_vals = [r.r_squared for r in spec_results if r.r_squared is not None]
    if not r2_vals:
        return 0.3, "No R² available"
    avg_r2 = sum(r2_vals) / len(r2_vals)
    if avg_r2 >= 0.5:
        return 1.0, f"Good fit (avg R²={avg_r2:.3f})"
    if avg_r2 >= 0.1:
        return 0.6, f"Moderate fit (avg R²={avg_r2:.3f})"
    return 0.3, f"Low fit (avg R²={avg_r2:.3f})"


def score_finding(
    outcome: str,
    predictor: str,
    spec_results: list[SpecificationResult],
    stability: StabilityAssessment,
    best_corrected: CorrectedResult | None,
) -> ExploratoryFinding:
    completed = [r for r in spec_results if r.status == "completed"]

    weights = {
        "corrected_support": 0.25,
        "direction_consistency": 0.15,
        "stability": 0.20,
        "data_quality": 0.15,
        "diagnostics": 0.15,
        "fit": 0.10,
    }

    dq_score, dq_expl = _score_data_quality(completed)
    cs_score, cs_expl = _score_corrected_support(stability)
    dir_score, dir_expl = _score_direction(stability)
    stab_score, stab_expl = _score_stability(stability)
    diag_score, diag_expl = _score_diagnostics(completed)
    fit_score, fit_expl = _score_fit(completed)

    breakdown = [
        FindingScoreComponent(criterion="Corrected Statistical Support", score=cs_score, weight=weights["corrected_support"], explanation=cs_expl),
        FindingScoreComponent(criterion="Specification Stability", score=stab_score, weight=weights["stability"], explanation=stab_expl),
        FindingScoreComponent(criterion="Direction Consistency", score=dir_score, weight=weights["direction_consistency"], explanation=dir_expl),
        FindingScoreComponent(criterion="Data Quality", score=dq_score, weight=weights["data_quality"], explanation=dq_expl),
        FindingScoreComponent(criterion="Diagnostic Quality", score=diag_score, weight=weights["diagnostics"], explanation=diag_expl),
        FindingScoreComponent(criterion="Model Fit", score=fit_score, weight=weights["fit"], explanation=fit_expl),
    ]

    total = sum(comp.score * comp.weight for comp in breakdown)
    final_score = round(total * 100, 1)

    if final_score >= 70:
        support: SupportLevel = "strong"
    elif final_score >= 50:
        support = "moderate"
    elif final_score >= 30:
        support = "weak"
    elif completed:
        support = "insufficient"
    else:
        support = "not_suitable"

    best = max(completed, key=lambda r: (r.n_obs or 0)) if completed else None
    direction = "unavailable"
    if best and best.coefficient is not None:
        direction = _direction_str(best.coefficient)

    warnings = ["This is an exploratory association and not causal evidence."]
    if stability.stability_label == "sensitive":
        warnings.append("This finding is sensitive to specification choice.")
    if any(r.absorbed_variables for r in completed):
        warnings.append("The primary variable was absorbed in at least one specification.")

    return ExploratoryFinding(
        finding_id=f"finding_{outcome}_{predictor}",
        outcome_variable=outcome,
        primary_predictor=predictor,
        relationship_direction=direction,
        exploratory_score=final_score,
        support_level=support,
        raw_p_value=best_corrected.raw_p_value if best_corrected else None,
        adjusted_q_value=best_corrected.adjusted_p_value if best_corrected else None,
        multiple_testing_method=best_corrected.correction_method if best_corrected else "none",
        stability_label=stability.stability_label,
        best_coefficient=best.coefficient if best else None,
        best_n_obs=best.n_obs if best else None,
        best_r_squared=best.r_squared if best else None,
        score_breakdown=breakdown,
        specification_ids=[r.spec_id for r in spec_results],
        warnings=warnings,
    )
