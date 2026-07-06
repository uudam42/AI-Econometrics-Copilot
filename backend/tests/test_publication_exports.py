"""Tests for Phase 8 — Publication-Ready Reporting and Advanced Export."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from tests.conftest import df_to_csv_bytes


# ---------------------------------------------------------------------------
# Helper: upload + analyse → return (dataset_id, analysis_id)
# ---------------------------------------------------------------------------

def _create_analysis(client, panel_df) -> tuple[str, str]:
    csv = df_to_csv_bytes(panel_df)
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    assert resp.status_code == 200
    did = resp.json()["dataset_id"]

    resp = client.post("/api/analyses/run", json={
        "dataset_id": did,
        "variable_selection": {
            "dataset_id": did,
            "dependent_variable": "gdp_per_capita",
            "primary_independent_variable": "internet_users",
            "control_variables": [],
        },
        "model_type": "ols",
        "transformations": [],
    })
    assert resp.status_code == 200
    aid = resp.json()["analysis_id"]
    return did, aid


def _create_comparison(client, panel_df) -> tuple[str, str]:
    csv = df_to_csv_bytes(panel_df)
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("test.csv", csv, "text/csv")},
    )
    did = resp.json()["dataset_id"]

    resp = client.post("/api/comparisons/run", json={
        "dataset_id": did,
        "variable_selection": {
            "dataset_id": did,
            "dependent_variable": "gdp_per_capita",
            "primary_independent_variable": "internet_users",
            "control_variables": [],
            "entity_column": "country",
            "time_column": "year",
        },
        "candidate_models": ["ols", "robust_ols"],
        "transformations": [],
    })
    assert resp.status_code == 200
    cid = resp.json()["comparison_id"]
    return did, cid


# ===========================================================================
# Academic tables unit tests
# ===========================================================================

class TestAcademicTables:

    def test_single_model_table_academic_style(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)

        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import single_model_table_md
        md = single_model_table_md(rec.result, rec.diagnostics, "academic")
        assert "Regression Results" in md
        assert "internet_users" in md
        assert "R²" in md
        assert "should not be interpreted as causal" in md

    def test_single_model_table_detailed_style(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import single_model_table_md
        md = single_model_table_md(rec.result, rec.diagnostics, "detailed")
        assert "t-stat" in md
        assert "p-value" in md
        assert "95% CI" in md

    def test_comparison_table(self, client, panel_df):
        did, cid = _create_comparison(client, panel_df)
        from app.storage.repositories import comparison_repository
        rec = comparison_repository.get(cid)

        from app.reports.academic_tables import comparison_table_md
        md = comparison_table_md(rec.result)
        assert "Model Comparison" in md
        assert "Observations" in md
        assert "internet_users" in md

    def test_stability_table(self, client, panel_df):
        did, cid = _create_comparison(client, panel_df)
        from app.storage.repositories import comparison_repository
        rec = comparison_repository.get(cid)

        from app.reports.academic_tables import stability_table_md
        md = stability_table_md(rec.result.coefficient_stability)
        assert "Coefficient Stability" in md
        assert "does not independently establish causality" in md

    def test_descriptive_stats_table(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import descriptive_stats_table_md
        md = descriptive_stats_table_md(rec.diagnostics.descriptive_stats)
        assert "Descriptive Statistics" in md
        assert "Mean" in md

    def test_variable_definition_table(self):
        from app.reports.academic_tables import variable_definition_table_md
        md = variable_definition_table_md(
            dep_var="gdp",
            primary_iv="trade",
            controls=["pop", "fdi"],
            entity_col="country",
            time_col="year",
        )
        assert "gdp" in md
        assert "trade" in md
        assert "pop" in md
        assert "Entity identifier" in md

    def test_diagnostic_summary_table(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import diagnostic_summary_table_md
        md = diagnostic_summary_table_md(rec.diagnostics)
        assert "Diagnostic Summary" in md


# ===========================================================================
# Academic figures unit tests
# ===========================================================================

class TestAcademicFigures:

    def test_coefficient_plot(self, client, panel_df, tmp_path):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_figures import generate_coefficient_plot
        fig = generate_coefficient_plot(rec.result, tmp_path)
        assert fig is not None
        assert fig.figure_type == "coefficient_plot"
        assert (tmp_path / fig.filename).exists()

    def test_residual_plot(self, client, panel_df, tmp_path):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_figures import generate_residual_plot
        fig = generate_residual_plot(rec.result, tmp_path)
        assert fig is not None
        assert fig.figure_type == "residual_fitted"
        assert (tmp_path / fig.filename).exists()

    def test_actual_vs_predicted(self, client, panel_df, tmp_path):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_figures import generate_actual_vs_predicted
        fig = generate_actual_vs_predicted(rec.result, tmp_path)
        assert fig is not None
        assert fig.figure_type == "actual_vs_predicted"
        assert (tmp_path / fig.filename).exists()

    def test_correlation_heatmap(self, client, panel_df, tmp_path):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_figures import generate_correlation_heatmap
        fig = generate_correlation_heatmap(rec.diagnostics, tmp_path)
        assert fig is not None
        assert fig.figure_type == "correlation_heatmap"
        assert (tmp_path / fig.filename).exists()

    def test_stability_chart(self, client, panel_df, tmp_path):
        did, cid = _create_comparison(client, panel_df)
        from app.storage.repositories import comparison_repository
        rec = comparison_repository.get(cid)

        from app.reports.academic_figures import generate_stability_chart
        fig = generate_stability_chart(rec.result, tmp_path)
        assert fig is not None
        assert fig.figure_type == "coefficient_stability"
        assert "does not establish causality" in fig.caption
        assert (tmp_path / fig.filename).exists()


# ===========================================================================
# DOCX export tests
# ===========================================================================

class TestDocxExport:

    def test_docx_generates_bytes(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import single_model_table_md
        md = single_model_table_md(rec.result)

        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="Test DOCX Export",
            author_name="Test Author",
        )

        from app.reports.docx_generator import generate_docx
        data = generate_docx(md, config)
        assert isinstance(data, bytes)
        assert len(data) > 1000
        # DOCX magic bytes (PK zip)
        assert data[:2] == b"PK"

    def test_docx_with_cover_page(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="Cover Page Test",
            author_name="Author Name",
            institution_name="Test University",
            include_cover_page=True,
        )
        from app.reports.docx_generator import generate_docx
        data = generate_docx("# Test\n\nHello world", config)
        assert len(data) > 500


# ===========================================================================
# LaTeX export tests
# ===========================================================================

class TestLatexExport:

    def test_latex_generates_valid_tex(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.reports.academic_tables import single_model_table_md
        md = single_model_table_md(rec.result)

        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="Test LaTeX Export",
            author_name="Test Author",
        )

        from app.reports.latex_generator import generate_latex
        tex = generate_latex(md, config)
        assert r"\documentclass" in tex
        assert r"\begin{document}" in tex
        assert r"\end{document}" in tex
        assert r"\begin{tabular}" in tex
        assert r"\toprule" in tex

    def test_latex_output_dir(self, client, panel_df, tmp_path):
        did, aid = _create_analysis(client, panel_df)
        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="LaTeX Dir Test",
        )

        from app.reports.latex_generator import generate_latex
        out = tmp_path / "latex_out"
        generate_latex("# Test\n\n| A | B |\n|---|---|\n| 1 | 2 |", config, output_dir=out)
        assert (out / "main.tex").exists()
        assert (out / "tables").is_dir()
        assert (out / "figures").is_dir()
        assert (out / "appendix").is_dir()
        assert (out / "README.md").exists()


# ===========================================================================
# PDF placeholder tests
# ===========================================================================

class TestPdfPlaceholder:

    def test_pdf_raises_unavailable(self):
        from app.reports.pdf_generator import generate_pdf, PDFExportUnavailableError
        with pytest.raises(PDFExportUnavailableError) as exc:
            generate_pdf("<html></html>", "/tmp/out.pdf")
        assert "Pango" in str(exc.value)
        assert exc.value.status_code == 501


# ===========================================================================
# Appendix generator tests
# ===========================================================================

class TestAppendixGenerator:

    def test_methodology_section_analysis(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="Test",
        )

        from app.reports.appendix_generator import generate_methodology_section
        md = generate_methodology_section(config, result=rec.result)
        assert "Methodology" in md
        assert "gdp_per_capita" in md
        assert "internet_users" in md

    def test_reproducibility_appendix(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        from app.storage.repositories import analysis_repository
        rec = analysis_repository.get(aid)

        from app.schemas.publication_export import PublicationExportConfig
        config = PublicationExportConfig(
            source_type="analysis",
            source_id=aid,
            title="Test",
        )

        from app.reports.appendix_generator import generate_reproducibility_appendix
        md = generate_reproducibility_appendix(config, result=rec.result)
        assert "Reproducibility" in md
        assert "Software Versions" in md
        assert "pandas" in md
        assert "auto-generated" in md


# ===========================================================================
# Publication export API integration tests
# ===========================================================================

class TestPublicationExportAPI:

    def test_generate_export_from_analysis_docx(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "API Test Export",
            "output_formats": ["docx"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["export_id"]
        assert "docx" in data["available_formats"]
        assert data["disclaimer"]
        assert len(data["sections_included"]) > 0

    def test_generate_export_from_comparison(self, client, panel_df):
        did, cid = _create_comparison(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "comparison",
            "source_id": cid,
            "title": "Comparison Export Test",
            "output_formats": ["markdown", "html"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "markdown" in data["available_formats"]
        assert "html" in data["available_formats"]

    def test_generate_export_multiple_formats(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Multi-Format Test",
            "output_formats": ["docx", "markdown", "latex", "json"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["available_formats"]) == {"docx", "markdown", "latex", "json"}

    def test_get_export_by_id(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Get Test",
            "output_formats": ["markdown"],
        })
        eid = resp.json()["export_id"]

        resp = client.get(f"/api/publication-exports/{eid}")
        assert resp.status_code == 200
        assert resp.json()["export_id"] == eid

    def test_download_docx(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Download Test",
            "output_formats": ["docx"],
        })
        eid = resp.json()["export_id"]

        resp = client.get(f"/api/publication-exports/{eid}/download/docx")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith(
            "application/vnd.openxmlformats"
        )
        assert resp.content[:2] == b"PK"

    def test_download_markdown(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "MD Download Test",
            "output_formats": ["markdown"],
        })
        eid = resp.json()["export_id"]

        resp = client.get(f"/api/publication-exports/{eid}/download/markdown")
        assert resp.status_code == 200
        assert "MD Download Test" in resp.text

    def test_download_latex(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "LaTeX Download",
            "output_formats": ["latex"],
        })
        eid = resp.json()["export_id"]

        resp = client.get(f"/api/publication-exports/{eid}/download/latex")
        assert resp.status_code == 200
        assert r"\documentclass" in resp.text

    def test_export_json_endpoint(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "JSON Export Test",
            "output_formats": ["docx"],
        })
        eid = resp.json()["export_id"]

        resp = client.get(f"/api/publication-exports/{eid}/export/json")
        assert resp.status_code == 200
        assert resp.json()["export_id"] == eid

    def test_list_project_exports(self, client, panel_df):
        proj = client.post("/api/projects", json={
            "title": "Export Project",
        })
        pid = proj.json()["project_id"]

        did, aid = _create_analysis(client, panel_df)
        client.post("/api/publication-exports/generate", json={
            "project_id": pid,
            "source_type": "analysis",
            "source_id": aid,
            "title": "Proj Export 1",
            "output_formats": ["markdown"],
        })
        client.post("/api/publication-exports/generate", json={
            "project_id": pid,
            "source_type": "analysis",
            "source_id": aid,
            "title": "Proj Export 2",
            "output_formats": ["docx"],
        })

        resp = client.get(f"/api/publication-exports/by-project/{pid}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 2

    def test_export_includes_figures(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Figures Test",
            "include_figures": True,
            "output_formats": ["docx"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["figures"]) > 0
        for fig in data["figures"]:
            assert fig["figure_type"]
            assert fig["caption"]

    def test_export_causal_warning_in_disclaimer(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Causal Warning Test",
            "output_formats": ["markdown"],
        })
        data = resp.json()
        assert "causal" in data["disclaimer"].lower()

    def test_export_with_all_sections(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Full Sections Test",
            "include_variable_table": True,
            "include_descriptive_statistics": True,
            "include_regression_table": True,
            "include_diagnostics": True,
            "include_methodology_section": True,
            "include_limitations_section": True,
            "include_reproducibility_appendix": True,
            "output_formats": ["markdown"],
        })
        assert resp.status_code == 200
        sections = resp.json()["sections_included"]
        assert "Variable Definitions" in sections
        assert "Regression Table" in sections
        assert "Methodology" in sections
        assert "Reproducibility Appendix" in sections

    def test_export_with_minimal_sections(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Minimal Export",
            "include_variable_table": False,
            "include_descriptive_statistics": False,
            "include_regression_table": True,
            "include_model_comparison": False,
            "include_diagnostics": False,
            "include_figures": False,
            "include_methodology_section": False,
            "include_limitations_section": False,
            "include_reproducibility_appendix": False,
            "output_formats": ["markdown"],
        })
        assert resp.status_code == 200
        sections = resp.json()["sections_included"]
        assert "Regression Table" in sections
        assert "Variable Definitions" not in sections

    def test_export_source_not_found(self, client):
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": "nonexistent-id",
            "title": "Missing Source",
            "output_formats": ["docx"],
        })
        assert resp.status_code in (404, 422)


# ===========================================================================
# Backward compatibility — existing report endpoints still work
# ===========================================================================

class TestBackwardCompatibility:

    def test_existing_report_generation_unchanged(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/reports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["markdown_content"]
        assert data["html_content"]

    def test_existing_report_markdown_endpoint(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/reports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
        })
        rid = resp.json()["report_id"]
        resp = client.get(f"/api/reports/{rid}/markdown")
        assert resp.status_code == 200

    def test_existing_report_html_endpoint(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/reports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
        })
        rid = resp.json()["report_id"]
        resp = client.get(f"/api/reports/{rid}/html")
        assert resp.status_code == 200


# ===========================================================================
# Persistence and timeline integration
# ===========================================================================

class TestPersistenceAndTimeline:

    def test_export_persisted_and_reloaded(self, client, panel_df):
        did, aid = _create_analysis(client, panel_df)
        resp = client.post("/api/publication-exports/generate", json={
            "source_type": "analysis",
            "source_id": aid,
            "title": "Persistence Test",
            "output_formats": ["docx"],
        })
        eid = resp.json()["export_id"]

        from app.storage.repositories import publication_export_repository
        publication_export_repository._cache.clear()

        rec = publication_export_repository.get(eid)
        assert rec.title == "Persistence Test"
        assert rec.export_id == eid

    def test_export_creates_timeline_event(self, client, panel_df):
        proj = client.post("/api/projects", json={"title": "Timeline Test"})
        pid = proj.json()["project_id"]

        did, aid = _create_analysis(client, panel_df)
        client.post("/api/publication-exports/generate", json={
            "project_id": pid,
            "source_type": "analysis",
            "source_id": aid,
            "title": "Timeline Export",
            "output_formats": ["markdown"],
        })

        resp = client.get(f"/api/projects/{pid}/timeline")
        assert resp.status_code == 200
        events = resp.json()
        export_events = [e for e in events if e["event_type"] == "publication_export_created"]
        assert len(export_events) == 1
        assert "Timeline Export" in export_events[0]["description"]
