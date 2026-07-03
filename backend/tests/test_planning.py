"""Tests for Phase 5: natural-language research planning layer.

Covers: question parser, variable matcher, plan generation, absorbed variable
transparency, and planning API endpoints.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.analysis.economics_synonyms import (
    all_concepts,
    get_concept_for_token,
    get_tokens_for_concept,
)
from app.analysis.research_question_parser import parse_research_question
from app.analysis.variable_matcher import match_variables
from app.analysis.research_planner import generate_plan
from app.main import app
from app.schemas.planning import AnalysisIntent

client = TestClient(app)


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture()
def panel_df() -> pd.DataFrame:
    """World-Bank-style panel: 5 countries × 5 years."""
    rng = np.random.default_rng(42)
    countries = ["USA", "CHN", "GBR", "DEU", "JPN"]
    years = list(range(2015, 2020))
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
                "population": rng.uniform(5e6, 1.4e9),
                "education_spending": rng.uniform(3, 8),
            })
    return pd.DataFrame(rows)


@pytest.fixture()
def cross_section_df() -> pd.DataFrame:
    rng = np.random.default_rng(99)
    return pd.DataFrame({
        "income": rng.uniform(20000, 100000, 50),
        "years_schooling": rng.uniform(8, 20, 50),
        "experience": rng.uniform(1, 40, 50),
    })


# ──────────────────────────────────────────────────────────────────────
# Economics Synonyms
# ──────────────────────────────────────────────────────────────────────

class TestEconomicsSynonyms:
    def test_concept_for_known_token(self):
        assert get_concept_for_token("gdp_per_capita") == "gdp_per_capita"
        assert get_concept_for_token("internet_users") == "internet_penetration"

    def test_concept_for_unknown_token(self):
        assert get_concept_for_token("xyzzy_unknown") is None

    def test_tokens_for_concept(self):
        tokens = get_tokens_for_concept("gdp_per_capita")
        assert "gdppc" in tokens
        assert "gdp_per_capita" in tokens

    def test_all_concepts_nonempty(self):
        concepts = all_concepts()
        assert len(concepts) > 10
        assert "gdp_per_capita" in concepts
        assert "internet_penetration" in concepts


# ──────────────────────────────────────────────────────────────────────
# Research Question Parser
# ──────────────────────────────────────────────────────────────────────

class TestResearchQuestionParser:
    def test_association_question(self):
        parsed = parse_research_question(
            "Is internet penetration associated with GDP per capita?"
        )
        assert parsed.detected_intent == "association"
        assert not parsed.causal_keywords_found

    def test_causal_question_affect(self):
        parsed = parse_research_question(
            "Does internet penetration affect GDP per capita?"
        )
        assert parsed.detected_intent == "causal_claim_requested"
        assert any("affect" in kw for kw in parsed.causal_keywords_found)
        assert "causal language" in parsed.causal_warning.lower()

    def test_causal_question_cause(self):
        parsed = parse_research_question(
            "Does trade cause economic growth?"
        )
        assert parsed.detected_intent == "causal_claim_requested"
        assert any("cause" in kw for kw in parsed.causal_keywords_found)

    def test_causal_question_leads_to(self):
        parsed = parse_research_question(
            "Does urbanization lead to higher GDP?"
        )
        assert parsed.detected_intent == "causal_claim_requested"

    def test_exploratory_question(self):
        parsed = parse_research_question(
            "What factors explain variation in GDP per capita?"
        )
        assert parsed.detected_intent == "exploratory"

    def test_unclear_question(self):
        parsed = parse_research_question("GDP per capita internet users")
        assert parsed.detected_intent == "unclear"

    def test_empty_question(self):
        parsed = parse_research_question("")
        assert parsed.detected_intent == "unclear"
        assert parsed.normalized == ""

    def test_normalization_strips_punctuation(self):
        parsed = parse_research_question(
            "Is GDP per capita associated with trade openness???"
        )
        assert "???" not in parsed.normalized
        assert parsed.detected_intent == "association"

    def test_extracted_tokens_exclude_stopwords(self):
        parsed = parse_research_question(
            "Is internet use associated with GDP per capita?"
        )
        assert "is" not in parsed.extracted_tokens
        assert "with" not in parsed.extracted_tokens
        assert "internet" in parsed.extracted_tokens
        assert "gdp" in parsed.extracted_tokens

    def test_causal_warning_includes_keywords(self):
        parsed = parse_research_question("Does education affect income?")
        assert "affect" in parsed.causal_warning.lower()

    def test_association_no_causal_warning(self):
        parsed = parse_research_question(
            "Is internet use correlated with GDP?"
        )
        assert "causal language" not in parsed.causal_warning.lower()
        assert "associations" in parsed.causal_warning.lower()


# ──────────────────────────────────────────────────────────────────────
# Variable Matcher
# ──────────────────────────────────────────────────────────────────────

class TestVariableMatcher:
    def test_matches_panel_columns(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp", "per", "capita"]
        result = match_variables(panel_df, tokens)
        roles = {c.column_name: c.role for c in result.candidates}
        assert "country" in roles
        assert roles["country"] == "entity_column"
        assert "year" in roles
        assert roles["year"] == "time_column"

    def test_identifies_gdp_as_candidate(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp", "per", "capita"]
        result = match_variables(panel_df, tokens)
        col_names = [c.column_name for c in result.candidates]
        assert "gdp_per_capita" in col_names

    def test_identifies_internet_as_candidate(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp", "per", "capita"]
        result = match_variables(panel_df, tokens)
        col_names = [c.column_name for c in result.candidates]
        assert "internet_users" in col_names

    def test_preferred_outcome_override(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp"]
        result = match_variables(
            panel_df, tokens, preferred_outcome="gdp_per_capita"
        )
        gdp_candidate = next(
            c for c in result.candidates if c.column_name == "gdp_per_capita"
        )
        assert gdp_candidate.role == "dependent_variable"
        assert gdp_candidate.confidence >= 0.9

    def test_preferred_primary_iv_override(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp"]
        result = match_variables(
            panel_df, tokens, preferred_primary_iv="internet_users"
        )
        iv_candidate = next(
            c for c in result.candidates if c.column_name == "internet_users"
        )
        assert iv_candidate.role == "primary_independent_variable"
        assert iv_candidate.confidence >= 0.9

    def test_ambiguity_when_no_dep_var(self, cross_section_df: pd.DataFrame):
        tokens = ["xyzzy", "nonexistent"]
        result = match_variables(cross_section_df, tokens)
        assert any("dependent variable" in a.lower() for a in result.ambiguities)

    def test_candidates_sorted_by_confidence(self, panel_df: pd.DataFrame):
        tokens = ["internet", "gdp", "per", "capita"]
        result = match_variables(panel_df, tokens)
        confidences = [c.confidence for c in result.candidates]
        assert confidences == sorted(confidences, reverse=True)

    def test_cross_section_no_entity_time(self, cross_section_df: pd.DataFrame):
        tokens = ["income", "schooling"]
        result = match_variables(cross_section_df, tokens)
        roles = {c.column_name: c.role for c in result.candidates}
        assert "entity_column" not in roles.values()
        assert "time_column" not in roles.values()


# ──────────────────────────────────────────────────────────────────────
# Research Planner (integration)
# ──────────────────────────────────────────────────────────────────────

class TestResearchPlanner:
    def _structure_panel(self):
        from app.schemas.dataset import StructureDetectionResult
        return StructureDetectionResult(
            dataset_type="panel",
            entity_column="country",
            time_column="year",
            is_balanced_panel=True,
            entity_count=5,
            time_period_count=5,
            explanation="Panel detected.",
        )

    def _structure_cross_section(self):
        from app.schemas.dataset import StructureDetectionResult
        return StructureDetectionResult(
            dataset_type="cross_sectional",
            explanation="Cross-sectional.",
        )

    def test_generates_plan_with_all_fields(self, panel_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Is internet penetration associated with GDP per capita?",
            structure=self._structure_panel(),
        )
        assert plan.plan_id
        assert plan.dataset_id == "ds-1"
        assert plan.research_question
        assert plan.normalized_question
        assert plan.inferred_analysis_intent == "association"
        assert plan.user_approval_required is True
        assert len(plan.candidate_variables) > 0
        assert len(plan.suggested_models) > 0
        assert plan.detected_structure_summary
        assert plan.causal_warning

    def test_causal_question_triggers_warning(self, panel_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Does internet penetration cause GDP growth?",
            structure=self._structure_panel(),
        )
        assert plan.inferred_analysis_intent == "causal_claim_requested"
        assert "causal language" in plan.causal_warning.lower()

    def test_panel_suggests_fe_re(self, panel_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Is internet use associated with GDP per capita?",
            structure=self._structure_panel(),
        )
        model_types = [m.model_type for m in plan.suggested_models]
        assert "fixed_effects" in model_types
        assert "random_effects" in model_types

    def test_cross_section_no_fe(self, cross_section_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-2",
            df=cross_section_df,
            research_question="Is years of schooling associated with income?",
            structure=self._structure_cross_section(),
        )
        model_types = [m.model_type for m in plan.suggested_models]
        assert "fixed_effects" not in model_types

    def test_preferred_outcome_respected(self, panel_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Is internet use associated with GDP?",
            structure=self._structure_panel(),
            preferred_outcome="gdp_per_capita",
        )
        dep_vars = [
            c for c in plan.candidate_variables
            if c.role == "dependent_variable"
        ]
        assert any(c.column_name == "gdp_per_capita" for c in dep_vars)

    def test_log_transform_suggested_for_skewed(self, panel_df: pd.DataFrame):
        # Make population very skewed
        panel_df["population"] = np.exp(np.random.default_rng(42).normal(10, 3, len(panel_df)))
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Is internet use associated with GDP per capita?",
            structure=self._structure_panel(),
        )
        log_transforms = [
            t for t in plan.suggested_transformations
            if t.operation == "log_transform"
        ]
        assert any(t.requires_user_confirmation for t in log_transforms)

    def test_structure_summary_includes_entity_time(self, panel_df: pd.DataFrame):
        plan = generate_plan(
            dataset_id="ds-1",
            df=panel_df,
            research_question="Is internet use associated with GDP?",
            structure=self._structure_panel(),
        )
        assert "country" in plan.detected_structure_summary
        assert "year" in plan.detected_structure_summary


# ──────────────────────────────────────────────────────────────────────
# Absorbed Variable Transparency
# ──────────────────────────────────────────────────────────────────────

class TestAbsorbedVariables:
    def _panel_with_constant_iv(self) -> pd.DataFrame:
        """Create a panel where the primary IV is constant within each entity
        (time-invariant), so it will be absorbed by entity FE."""
        rng = np.random.default_rng(123)
        rows = []
        countries = ["A", "B", "C", "D", "E"]
        for i, country in enumerate(countries):
            time_invariant_val = float(i + 1) * 10
            for year in range(2010, 2015):
                rows.append({
                    "country": country,
                    "year": year,
                    "outcome": rng.normal(50, 10) + float(i) * 5,
                    "time_invariant_var": time_invariant_val,
                    "control": rng.normal(0, 1),
                })
        return pd.DataFrame(rows)

    def test_absorbed_variable_reported(self):
        from app.analysis.panel_models import run_panel
        df = self._panel_with_constant_iv()
        result = run_panel(
            df=df,
            dep_var="outcome",
            primary_iv="time_invariant_var",
            controls=["control"],
            entity_col="country",
            time_col="year",
            model_type="fixed_effects",
        )
        assert result.absorbed_variables is not None
        assert "time_invariant_var" in result.absorbed_variables

    def test_absorbed_metadata_has_warnings(self):
        from app.analysis.panel_models import run_panel
        df = self._panel_with_constant_iv()
        result = run_panel(
            df=df,
            dep_var="outcome",
            primary_iv="time_invariant_var",
            controls=["control"],
            entity_col="country",
            time_col="year",
            model_type="fixed_effects",
        )
        assert "absorbed_variables" in result.model_metadata
        assert "absorbed_warnings" in result.model_metadata
        assert result.model_metadata["primary_iv_absorbed"] is True
        assert "absorbed_critical_warning" in result.model_metadata

    def test_no_absorption_when_variable_varies(self):
        from app.analysis.panel_models import run_panel
        rng = np.random.default_rng(42)
        rows = []
        for country in ["A", "B", "C", "D", "E"]:
            for year in range(2010, 2015):
                rows.append({
                    "country": country,
                    "year": year,
                    "outcome": rng.normal(50, 10),
                    "varying_var": rng.normal(0, 1),
                    "control": rng.normal(0, 1),
                })
        df = pd.DataFrame(rows)
        result = run_panel(
            df=df,
            dep_var="outcome",
            primary_iv="varying_var",
            controls=["control"],
            entity_col="country",
            time_col="year",
            model_type="fixed_effects",
        )
        assert result.absorbed_variables is None
        assert "absorbed_variables" not in result.model_metadata


# ──────────────────────────────────────────────────────────────────────
# Planning API Endpoints
# ──────────────────────────────────────────────────────────────────────

class TestPlanningAPI:
    @pytest.fixture(autouse=True)
    def _upload_sample(self):
        """Upload a dataset via the API for use in planning tests."""
        import io
        rng = np.random.default_rng(42)
        countries = ["USA", "CHN", "GBR", "DEU", "JPN"]
        years = list(range(2015, 2020))
        rows = []
        for c in countries:
            for y in years:
                rows.append({
                    "country": c, "year": y,
                    "gdp_per_capita": rng.uniform(5000, 60000),
                    "internet_users": rng.uniform(30, 95),
                    "trade_openness": rng.uniform(20, 80),
                })
        df = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        resp = client.post(
            "/api/datasets/upload",
            files={"file": ("test_plan.csv", buf, "text/csv")},
        )
        assert resp.status_code == 200
        self.dataset_id = resp.json()["dataset_id"]

    def test_generate_plan(self):
        resp = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Is internet use associated with GDP per capita?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"]
        assert data["user_approval_required"] is True
        assert len(data["candidate_variables"]) > 0
        assert len(data["suggested_models"]) > 0
        assert data["inferred_analysis_intent"] == "association"

    def test_generate_plan_causal_warning(self):
        resp = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Does internet access cause higher GDP?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["inferred_analysis_intent"] == "causal_claim_requested"
        assert "causal language" in data["causal_warning"].lower()

    def test_get_plan(self):
        gen = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Is trade openness associated with GDP?",
        })
        plan_id = gen.json()["plan_id"]
        resp = client.get(f"/api/plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["plan_id"] == plan_id

    def test_get_nonexistent_plan_404(self):
        resp = client.get("/api/plans/nonexistent-id")
        assert resp.status_code == 404

    def test_approve_plan(self):
        gen = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Is internet use associated with GDP per capita?",
        })
        plan_id = gen.json()["plan_id"]
        resp = client.post(f"/api/plans/{plan_id}/approve", json={
            "dependent_variable": "gdp_per_capita",
            "primary_independent_variable": "internet_users",
            "control_variables": ["trade_openness"],
            "entity_column": "country",
            "time_column": "year",
            "approved_transformations": [],
            "selected_candidate_models": ["fixed_effects", "random_effects"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["approved"] is True
        assert data["plan_id"] == plan_id
        assert data["variable_selection"]["dependent_variable"] == "gdp_per_capita"
        assert "model" in data["redirect_path"]

    def test_export_plan_json(self):
        gen = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Is trade associated with GDP?",
        })
        plan_id = gen.json()["plan_id"]
        resp = client.get(f"/api/plans/{plan_id}/export/json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_id"] == plan_id
        assert "candidate_variables" in data
        assert "created_at" in data

    def test_plan_with_preferred_outcome(self):
        resp = client.post("/api/plans/generate", json={
            "dataset_id": self.dataset_id,
            "research_question": "Is internet use associated with GDP?",
            "preferred_outcome": "gdp_per_capita",
        })
        data = resp.json()
        dep_vars = [
            c for c in data["candidate_variables"]
            if c["role"] == "dependent_variable"
        ]
        assert any(c["column_name"] == "gdp_per_capita" for c in dep_vars)

    def test_plan_with_nonexistent_dataset_404(self):
        resp = client.post("/api/plans/generate", json={
            "dataset_id": "nonexistent",
            "research_question": "Is X associated with Y?",
        })
        assert resp.status_code == 404
