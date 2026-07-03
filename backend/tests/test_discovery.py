"""Tests for Phase 6: constrained exploratory relationship discovery.

Covers: variable screening, candidate generation, multiple-testing
correction, stability evaluation, scoring, finding-to-plan handoff,
and API endpoints.
"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.analysis.discovery_candidates import generate_specifications
from app.analysis.discovery_engine import run_discovery
from app.analysis.discovery_scoring import assess_stability, score_finding
from app.analysis.discovery_screening import (
    screen_variables,
    select_candidate_outcomes,
    select_candidate_predictors,
)
from app.analysis.multiple_testing import (
    apply_correction,
    benjamini_hochberg,
    bonferroni,
    no_correction,
)
from app.main import app
from app.schemas.dataset import StructureDetectionResult
from app.schemas.discovery import (
    CorrectedResult,
    DiscoveryConfig,
    SpecificationResult,
)

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture()
def panel_df() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    countries = ["USA", "CHN", "GBR", "DEU", "JPN", "FRA", "IND", "BRA", "CAN", "AUS"]
    years = list(range(2010, 2020))
    rows = []
    for country in countries:
        for year in years:
            rows.append({
                "country": country,
                "year": year,
                "gdp_per_capita": rng.uniform(5000, 60000),
                "internet_users": rng.uniform(30, 95),
                "trade_openness": rng.uniform(20, 80),
                "inflation": rng.uniform(0.5, 15),
                "education_spending": rng.uniform(3, 8),
                "population": rng.uniform(5e6, 1.4e9),
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def cross_section_df() -> pd.DataFrame:
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "income": rng.uniform(20000, 100000, 60),
        "years_schooling": rng.uniform(8, 20, 60),
        "experience": rng.uniform(1, 40, 60),
        "age": rng.uniform(22, 65, 60),
    })


@pytest.fixture()
def panel_structure() -> StructureDetectionResult:
    return StructureDetectionResult(
        dataset_type="panel",
        entity_column="country",
        time_column="year",
        is_balanced_panel=True,
        entity_count=10,
        time_period_count=10,
        explanation="Panel detected.",
    )


@pytest.fixture()
def cross_structure() -> StructureDetectionResult:
    return StructureDetectionResult(
        dataset_type="cross_sectional",
        explanation="Cross-sectional.",
    )


# ──────────────────────────────────────────────────────────────────────
# Variable Screening
# ──────────────────────────────────────────────────────────────────────

class TestVariableScreening:
    def test_excludes_entity_column(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        country = next(r for r in results if r.column_name == "country")
        assert not country.eligible
        assert any("entity" in reason.lower() for reason in country.exclusion_reasons)

    def test_excludes_time_column(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        year = next(r for r in results if r.column_name == "year")
        assert not year.eligible
        assert any("time" in reason.lower() for reason in year.exclusion_reasons)

    def test_excludes_user_specified(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=["inflation"])
        inflation = next(r for r in results if r.column_name == "inflation")
        assert not inflation.eligible
        assert any("excluded by user" in reason.lower() for reason in inflation.exclusion_reasons)

    def test_excludes_constant_column(self, panel_df: pd.DataFrame):
        panel_df["constant_col"] = 42.0
        results = screen_variables(panel_df, excluded_variables=[])
        const = next(r for r in results if r.column_name == "constant_col")
        assert not const.eligible
        assert any("constant" in reason.lower() for reason in const.exclusion_reasons)

    def test_excludes_high_missing(self, panel_df: pd.DataFrame):
        panel_df["mostly_missing"] = np.nan
        panel_df.loc[:10, "mostly_missing"] = 1.0
        results = screen_variables(panel_df, excluded_variables=[], max_missing_rate=0.3)
        mm = next(r for r in results if r.column_name == "mostly_missing")
        assert not mm.eligible
        assert any("missing" in reason.lower() for reason in mm.exclusion_reasons)

    def test_eligible_numeric_columns(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        gdp = next(r for r in results if r.column_name == "gdp_per_capita")
        assert gdp.eligible
        assert gdp.quality_score > 0

    def test_quality_score_assigned(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        eligible = [r for r in results if r.eligible]
        for r in eligible:
            assert 0.0 < r.quality_score <= 1.0

    def test_candidate_outcomes_limited(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        outcomes = select_candidate_outcomes(results, max_outcomes=3)
        assert len(outcomes) <= 3
        assert all(isinstance(o, str) for o in outcomes)

    def test_candidate_outcomes_user_specified(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        outcomes = select_candidate_outcomes(
            results, max_outcomes=5, user_specified=["gdp_per_capita"]
        )
        assert outcomes == ["gdp_per_capita"]

    def test_candidate_predictors_exclude_outcome(self, panel_df: pd.DataFrame):
        results = screen_variables(panel_df, excluded_variables=[])
        preds = select_candidate_predictors(panel_df, "gdp_per_capita", results)
        assert "gdp_per_capita" not in preds


# ──────────────────────────────────────────────────────────────────────
# Candidate Specification Generation
# ──────────────────────────────────────────────────────────────────────

class TestCandidateGeneration:
    def test_generates_bounded_specs(
        self, panel_df: pd.DataFrame, panel_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            panel_df,
            outcome="gdp_per_capita",
            predictors=["internet_users", "trade_openness"],
            controls_pool=["inflation", "education_spending"],
            structure=panel_structure,
            max_specs=30,
        )
        assert len(specs) <= 30
        assert all(s.outcome_variable == "gdp_per_capita" for s in specs)

    def test_hard_limit_enforced(
        self, panel_df: pd.DataFrame, panel_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            panel_df,
            outcome="gdp_per_capita",
            predictors=["internet_users", "trade_openness", "inflation"],
            controls_pool=["education_spending"],
            structure=panel_structure,
            max_specs=5,
        )
        assert len(specs) <= 5

    def test_includes_bivariate_baseline(
        self, panel_df: pd.DataFrame, panel_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            panel_df,
            outcome="gdp_per_capita",
            predictors=["internet_users"],
            controls_pool=[],
            structure=panel_structure,
        )
        baseline = [s for s in specs if s.model_type == "ols" and len(s.controls) == 0]
        assert len(baseline) >= 1

    def test_panel_fe_included_for_panel(
        self, panel_df: pd.DataFrame, panel_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            panel_df,
            outcome="gdp_per_capita",
            predictors=["internet_users"],
            controls_pool=["inflation"],
            structure=panel_structure,
        )
        fe_specs = [s for s in specs if s.model_type == "fixed_effects"]
        assert len(fe_specs) >= 1

    def test_no_panel_for_cross_section(
        self, cross_section_df: pd.DataFrame, cross_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            cross_section_df,
            outcome="income",
            predictors=["years_schooling"],
            controls_pool=["experience"],
            structure=cross_structure,
        )
        panel_specs = [s for s in specs if s.model_type in ("fixed_effects", "two_way_fixed_effects")]
        assert len(panel_specs) == 0

    def test_every_spec_has_reason(
        self, panel_df: pd.DataFrame, panel_structure: StructureDetectionResult
    ):
        specs = generate_specifications(
            panel_df,
            outcome="gdp_per_capita",
            predictors=["internet_users"],
            controls_pool=[],
            structure=panel_structure,
        )
        for s in specs:
            assert s.generation_reason


# ──────────────────────────────────────────────────────────────────────
# Multiple Testing Correction
# ──────────────────────────────────────────────────────────────────────

class TestMultipleTesting:
    def test_bh_basic(self):
        p_values = [("a", 0.01), ("b", 0.03), ("c", 0.04), ("d", 0.25)]
        results = benjamini_hochberg(p_values, alpha=0.05)
        assert all(isinstance(r, CorrectedResult) for r in results)
        passed = [r for r in results if r.passes_threshold]
        not_passed = [r for r in results if not r.passes_threshold]
        assert len(passed) >= 1
        assert any(r.spec_id == "d" for r in not_passed)

    def test_bh_preserves_raw_values(self):
        p_values = [("a", 0.01), ("b", 0.5)]
        results = benjamini_hochberg(p_values)
        a_result = next(r for r in results if r.spec_id == "a")
        assert a_result.raw_p_value == 0.01
        assert a_result.adjusted_p_value is not None

    def test_bonferroni_basic(self):
        p_values = [("a", 0.001), ("b", 0.03), ("c", 0.5)]
        results = bonferroni(p_values, alpha=0.05)
        a_result = next(r for r in results if r.spec_id == "a")
        b_result = next(r for r in results if r.spec_id == "b")
        assert a_result.passes_threshold
        assert not b_result.passes_threshold
        assert b_result.adjusted_p_value == pytest.approx(0.09, abs=0.001)

    def test_bonferroni_stricter_than_bh(self):
        p_values = [("a", 0.01), ("b", 0.02), ("c", 0.03)]
        bh = benjamini_hochberg(p_values, alpha=0.05)
        bonf = bonferroni(p_values, alpha=0.05)
        bh_pass = sum(1 for r in bh if r.passes_threshold)
        bonf_pass = sum(1 for r in bonf if r.passes_threshold)
        assert bonf_pass <= bh_pass

    def test_no_correction_warning(self):
        p_values = [("a", 0.04), ("b", 0.06)]
        results = no_correction(p_values, alpha=0.05)
        a_result = next(r for r in results if r.spec_id == "a")
        assert a_result.passes_threshold
        assert a_result.correction_method == "none"

    def test_handles_none_p_values(self):
        p_values = [("a", 0.01), ("b", None), ("c", 0.5)]
        results = benjamini_hochberg(p_values)
        b_result = next(r for r in results if r.spec_id == "b")
        assert not b_result.passes_threshold
        assert b_result.adjusted_p_value is None

    def test_apply_correction_dispatches(self):
        p_values = [("a", 0.01)]
        bh = apply_correction(p_values, "benjamini_hochberg")
        assert bh[0].correction_method == "benjamini_hochberg"
        bonf = apply_correction(p_values, "bonferroni")
        assert bonf[0].correction_method == "bonferroni"
        none = apply_correction(p_values, "none")
        assert none[0].correction_method == "none"


# ──────────────────────────────────────────────────────────────────────
# Stability and Scoring
# ──────────────────────────────────────────────────────────────────────

class TestStabilityAndScoring:
    def _make_result(self, spec_id: str, coeff: float, p: float, n: int = 100) -> SpecificationResult:
        return SpecificationResult(
            spec_id=spec_id,
            status="completed",
            outcome_variable="y",
            primary_predictor="x",
            model_type="ols",
            formula="y ~ x",
            coefficient=coeff,
            p_value=p,
            n_obs=n,
            r_squared=0.3,
            direction="positive" if coeff > 0 else "negative",
            significance="**" if p < 0.05 else "",
        )

    def test_stable_when_consistent(self):
        results = [
            self._make_result("s1", 2.5, 0.001),
            self._make_result("s2", 2.3, 0.002),
            self._make_result("s3", 2.7, 0.001),
        ]
        corrected = {
            "s1": CorrectedResult(spec_id="s1", raw_p_value=0.001, adjusted_p_value=0.003, correction_method="bh", passes_threshold=True),
            "s2": CorrectedResult(spec_id="s2", raw_p_value=0.002, adjusted_p_value=0.003, correction_method="bh", passes_threshold=True),
            "s3": CorrectedResult(spec_id="s3", raw_p_value=0.001, adjusted_p_value=0.003, correction_method="bh", passes_threshold=True),
        }
        stability = assess_stability("y", "x", results, corrected)
        assert stability.stability_label == "stable"
        assert stability.direction_consistent

    def test_sensitive_when_direction_changes(self):
        results = [
            self._make_result("s1", 2.5, 0.01),
            self._make_result("s2", -1.3, 0.02),
        ]
        corrected = {
            "s1": CorrectedResult(spec_id="s1", raw_p_value=0.01, adjusted_p_value=0.02, correction_method="bh", passes_threshold=True),
            "s2": CorrectedResult(spec_id="s2", raw_p_value=0.02, adjusted_p_value=0.02, correction_method="bh", passes_threshold=True),
        }
        stability = assess_stability("y", "x", results, corrected)
        assert stability.stability_label == "sensitive"
        assert not stability.direction_consistent

    def test_insufficient_evidence_single_spec(self):
        results = [self._make_result("s1", 2.5, 0.01)]
        corrected = {
            "s1": CorrectedResult(spec_id="s1", raw_p_value=0.01, adjusted_p_value=0.01, correction_method="bh", passes_threshold=True),
        }
        stability = assess_stability("y", "x", results, corrected)
        assert stability.stability_label == "insufficient_evidence"

    def test_score_finding_produces_valid_output(self):
        results = [
            self._make_result("s1", 2.5, 0.001, 200),
            self._make_result("s2", 2.3, 0.002, 200),
        ]
        corrected_map = {
            "s1": CorrectedResult(spec_id="s1", raw_p_value=0.001, adjusted_p_value=0.002, correction_method="bh", passes_threshold=True),
            "s2": CorrectedResult(spec_id="s2", raw_p_value=0.002, adjusted_p_value=0.002, correction_method="bh", passes_threshold=True),
        }
        stability = assess_stability("y", "x", results, corrected_map)
        finding = score_finding("y", "x", results, stability, corrected_map["s1"])
        assert finding.exploratory_score > 0
        assert finding.support_level in ("strong", "moderate", "weak", "insufficient", "not_suitable")
        assert len(finding.score_breakdown) > 0
        assert any("exploratory" in w.lower() for w in finding.warnings)

    def test_absorbed_variable_penalized(self):
        results = [
            SpecificationResult(
                spec_id="s1", status="completed",
                outcome_variable="y", primary_predictor="x",
                model_type="fixed_effects", formula="y ~ x",
                coefficient=1.0, p_value=0.01, n_obs=100, r_squared=0.2,
                direction="positive", significance="**",
                absorbed_variables=["control1"],
            ),
        ]
        corrected_map = {
            "s1": CorrectedResult(spec_id="s1", raw_p_value=0.01, adjusted_p_value=0.01, correction_method="bh", passes_threshold=True),
        }
        stability = assess_stability("y", "x", results, corrected_map)
        finding = score_finding("y", "x", results, stability, corrected_map["s1"])
        diag_component = next(c for c in finding.score_breakdown if "Diagnostic" in c.criterion)
        assert diag_component.score < 0.5


# ──────────────────────────────────────────────────────────────────────
# Discovery Engine (integration)
# ──────────────────────────────────────────────────────────────────────

class TestDiscoveryEngine:
    def _make_record(self, df: pd.DataFrame):
        from app.models.dataset_registry import DatasetRecord
        from pathlib import Path
        return DatasetRecord(
            dataset_id="test-ds",
            filename="test.csv",
            original_path=Path("/tmp/test.csv"),
            dataframe=df,
        )

    def test_guided_discovery(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="guided",
            outcome_variables=["gdp_per_capita"],
            excluded_variables=["country", "year"],
            maximum_specifications=10,
        )
        result = run_discovery(config, record)
        assert result.discovery_id
        assert result.mode == "guided"
        assert result.candidate_outcomes == ["gdp_per_capita"]
        assert result.specifications_generated <= 10
        assert result.specifications_generated == result.specifications_completed + result.specifications_failed
        assert len(result.findings) > 0
        assert result.disclaimer

    def test_open_discovery(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="open",
            excluded_variables=["country", "year"],
            maximum_outcomes=3,
            maximum_specifications=15,
        )
        result = run_discovery(config, record)
        assert result.mode == "open"
        assert len(result.candidate_outcomes) <= 3
        assert result.specifications_generated <= 15

    def test_findings_ranked_by_score(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="guided",
            outcome_variables=["gdp_per_capita"],
            excluded_variables=["country", "year"],
            maximum_specifications=20,
        )
        result = run_discovery(config, record)
        scores = [f.exploratory_score for f in result.findings]
        assert scores == sorted(scores, reverse=True)

    def test_failed_models_preserved(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="guided",
            outcome_variables=["gdp_per_capita"],
            excluded_variables=["country", "year"],
            maximum_specifications=20,
        )
        result = run_discovery(config, record)
        all_statuses = [r.status for r in result.specification_results]
        assert all(s in ("completed", "failed", "rejected") for s in all_statuses)

    def test_corrected_results_present(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="guided",
            outcome_variables=["gdp_per_capita"],
            excluded_variables=["country", "year"],
            multiple_testing_method="benjamini_hochberg",
            maximum_specifications=10,
        )
        result = run_discovery(config, record)
        assert len(result.corrected_results) > 0
        for cr in result.corrected_results:
            assert cr.correction_method == "benjamini_hochberg"

    def test_panel_models_included_for_panel_data(self, panel_df: pd.DataFrame):
        record = self._make_record(panel_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="guided",
            outcome_variables=["gdp_per_capita"],
            excluded_variables=["country", "year"],
            maximum_specifications=30,
        )
        result = run_discovery(config, record)
        model_types = {r.model_type for r in result.specification_results}
        assert "fixed_effects" in model_types or "two_way_fixed_effects" in model_types

    def test_cross_section_no_panel_models(self, cross_section_df: pd.DataFrame):
        record = self._make_record(cross_section_df)
        config = DiscoveryConfig(
            dataset_id="test-ds",
            mode="open",
            excluded_variables=[],
            maximum_specifications=10,
        )
        result = run_discovery(config, record)
        model_types = {r.model_type for r in result.specification_results}
        assert "fixed_effects" not in model_types

    def test_no_eligible_outcomes_raises(self):
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["a", "b", "c"]})
        from app.models.dataset_registry import DatasetRecord
        from pathlib import Path
        record = DatasetRecord(
            dataset_id="test-ds",
            filename="test.csv",
            original_path=Path("/tmp/test.csv"),
            dataframe=df,
        )
        config = DiscoveryConfig(dataset_id="test-ds", mode="open")
        from app.core.errors import ValidationAppError
        with pytest.raises(ValidationAppError):
            run_discovery(config, record)


# ──────────────────────────────────────────────────────────────────────
# Discovery API
# ──────────────────────────────────────────────────────────────────────

class TestDiscoveryAPI:
    @pytest.fixture(autouse=True)
    def _upload_sample(self):
        rng = np.random.default_rng(42)
        countries = ["USA", "CHN", "GBR", "DEU", "JPN", "FRA", "IND", "BRA", "CAN", "AUS"]
        years = list(range(2010, 2020))
        rows = []
        for c in countries:
            for y in years:
                rows.append({
                    "country": c, "year": y,
                    "gdp_per_capita": rng.uniform(5000, 60000),
                    "internet_users": rng.uniform(30, 95),
                    "trade_openness": rng.uniform(20, 80),
                    "inflation": rng.uniform(0.5, 15),
                })
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        resp = client.post(
            "/api/datasets/upload",
            files={"file": ("test_disc.csv", buf, "text/csv")},
        )
        assert resp.status_code == 200
        self.dataset_id = resp.json()["dataset_id"]

    def test_run_discovery_guided(self):
        resp = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "guided",
            "outcome_variables": ["gdp_per_capita"],
            "excluded_variables": ["country", "year"],
            "maximum_specifications": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["discovery_id"]
        assert data["mode"] == "guided"
        assert len(data["findings"]) > 0
        assert data["disclaimer"]

    def test_run_discovery_open(self):
        resp = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "open",
            "excluded_variables": ["country", "year"],
            "maximum_outcomes": 2,
            "maximum_specifications": 8,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "open"
        assert len(data["candidate_outcomes"]) <= 2

    def test_get_discovery(self):
        gen = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "guided",
            "outcome_variables": ["gdp_per_capita"],
            "excluded_variables": ["country", "year"],
            "maximum_specifications": 5,
        })
        discovery_id = gen.json()["discovery_id"]
        resp = client.get(f"/api/discovery/{discovery_id}")
        assert resp.status_code == 200
        assert resp.json()["discovery_id"] == discovery_id

    def test_get_findings(self):
        gen = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "guided",
            "outcome_variables": ["gdp_per_capita"],
            "excluded_variables": ["country", "year"],
            "maximum_specifications": 5,
        })
        discovery_id = gen.json()["discovery_id"]
        resp = client.get(f"/api/discovery/{discovery_id}/findings")
        assert resp.status_code == 200
        findings = resp.json()
        assert isinstance(findings, list)

    def test_export_json(self):
        gen = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "guided",
            "outcome_variables": ["gdp_per_capita"],
            "excluded_variables": ["country", "year"],
            "maximum_specifications": 5,
        })
        discovery_id = gen.json()["discovery_id"]
        resp = client.get(f"/api/discovery/{discovery_id}/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert "specification_results" in data
        assert "corrected_results" in data
        assert "findings" in data

    def test_create_plan_from_finding(self):
        gen = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "mode": "guided",
            "outcome_variables": ["gdp_per_capita"],
            "excluded_variables": ["country", "year"],
            "maximum_specifications": 10,
        })
        data = gen.json()
        discovery_id = data["discovery_id"]
        findings = data["findings"]
        assert len(findings) > 0
        finding_id = findings[0]["finding_id"]

        resp = client.post(
            f"/api/discovery/{discovery_id}/findings/{finding_id}/create-plan"
        )
        assert resp.status_code == 200
        plan = resp.json()
        assert plan["plan_id"]
        assert plan["user_approval_required"] is True
        assert plan["dataset_id"] == self.dataset_id

    def test_nonexistent_discovery_404(self):
        resp = client.get("/api/discovery/nonexistent-id")
        assert resp.status_code == 404

    def test_nonexistent_dataset_404(self):
        resp = client.post("/api/discovery/run", json={
            "dataset_id": "nonexistent",
            "mode": "open",
        })
        assert resp.status_code == 404

    def test_validation_rejects_unsafe_limits(self):
        resp = client.post("/api/discovery/run", json={
            "dataset_id": self.dataset_id,
            "maximum_specifications": 200,
        })
        assert resp.status_code == 422
