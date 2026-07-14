export const en = {
  // Common
  "app.title": "AI Econometrics Copilot",
  "app.tagline": "Explainable, reproducible econometric analysis",
  "common.back_home": "← Home",
  "common.home": "Home",
  "common.loading": "Loading…",
  "common.error": "Something went wrong.",
  "common.empty": "Nothing here yet.",
  "common.open": "Open",
  "common.rows": "rows",
  "common.columns": "columns",
  "common.created": "Created",
  "common.uploaded": "Uploaded",
  "common.project": "Project",
  "common.no_project": "No project",
  "common.back": "Back",
  "common.save": "Save",
  "common.cancel": "Cancel",
  "common.delete": "Delete",
  "common.confirm": "Confirm",
  "common.close": "Close",
  "common.download": "Download",
  "common.export": "Export",
  "common.view": "View",
  "common.search": "Search",
  "common.filter": "Filter",
  "common.status": "Status",
  "common.actions": "Actions",
  "common.details": "Details",
  "common.description": "Description",
  "common.name": "Name",
  "common.type": "Type",
  "common.date": "Date",
  "common.yes": "Yes",
  "common.no": "No",

  // Home
  "home.my_projects": "My Projects",
  "home.hero": "What would you like to do?",
  "home.hero_sub":
    "Choose a path below — you can always switch to the full Research Workspace later.",
  "home.card_quick_title": "Analyse My Excel / CSV",
  "home.card_quick_desc":
    "Upload your file, answer one question, and get a plain-language result in under a minute.",
  "home.card_demo_title": "Try a Demo Dataset",
  "home.card_demo_desc":
    "Load a sample World Bank panel dataset and explore the full workflow.",
  "home.card_demo_unavailable": "Demo data not available on this installation.",
  "home.card_projects_title": "Open Previous Project",
  "home.card_projects_desc":
    "Return to a project you have already started and continue your research.",
  "home.creating_demo": "Creating demo project…",
  "home.demo_error": "Could not create demo project.",
  "home.advanced": "Advanced workflow",
  "home.link_datasets": "📂 All Datasets",
  "home.link_projects": "🗂 All Projects",
  "home.link_reports": "📄 Reports",
  "home.link_analyses": "🔬 Analyses",
  "home.footer":
    "Statistical associations only — not causal effects unless additional identification assumptions are justified.",

  // Quick Analyze
  "qa.title": "Quick Analyze",
  "qa.step_upload": "Upload",
  "qa.step_review": "Review",
  "qa.step_results": "Results",
  "qa.upload_title": "Upload Your Data",
  "qa.upload_desc":
    "Upload an Excel (.xlsx, .xls) or CSV file. We will automatically detect the structure and suggest the right model.",
  "qa.drop_zone": "Drop file here or click to browse",
  "qa.drop_zone_hint": "Excel or CSV",
  "qa.question_label": "Research question",
  "qa.question_optional": "(optional)",
  "qa.question_placeholder": "e.g. Does education affect income?",
  "qa.question_hint": "Leave blank for an exploratory overview of your dataset.",
  "qa.uploading": "Uploading…",
  "qa.continue": "Continue →",
  "qa.analysing_title": "Analysing Your Data…",
  "qa.analysing_desc":
    "We are profiling the dataset and detecting its structure. This usually takes a few seconds.",
  "qa.processing": "Processing…",
  "qa.review_title": "Review Recommendation",
  "qa.review_desc":
    "We analysed your dataset and suggest the setup below. Review and confirm before running — you can change any field.",
  "qa.recommended": "Recommended",
  "qa.detected_structure": "Detected structure",
  "qa.var_selection": "Variable Selection",
  "qa.outcome_var": "Outcome variable",
  "qa.main_expl_var": "Main explanatory variable",
  "qa.control_vars": "Control variables",
  "qa.model": "Model",
  "qa.optional_log": "Optional log-transformations",
  "qa.select_placeholder": "— select —",
  "qa.running_model": "Running model…",
  "qa.run_analysis": "Run Analysis →",
  "qa.fitting_model": "Running Model…",
  "qa.fitting_desc": "Fitting the econometric model and computing diagnostics…",
  "qa.association_found": "Association Found",
  "qa.no_association": "No Clear Association",
  "qa.diagnostics_overview": "Diagnostics Overview",
  "qa.warnings": "Warnings",
  "qa.causal_note_label": "Note: ",
  "qa.next_actions": "What to do next",
  "qa.open_workspace": "Open Full Workspace →",
  "qa.start_new": "Start New Analysis",
  "qa.my_projects": "My Projects",
  "qa.error_title": "Something went wrong",
  "qa.start_over": "Start Over",
  "qa.footer":
    "This analysis identifies statistical associations only — not causal effects.",
  "qa.required": "*",

  // Diagnostics status labels
  "diag.data_quality": "Data quality",
  "diag.model_fit": "Model fit",
  "diag.multicollinearity": "Multicollinearity",
  "diag.heteroskedasticity": "Heteroskedasticity",
  "diag.panel_structure": "Panel structure",
  "diag.causal_interpretation": "Causal interpretation",

  // Datasets index
  "datasets.title": "All Datasets",
  "datasets.subtitle": "Every dataset uploaded to this workspace.",
  "datasets.empty":
    "No datasets uploaded yet. Use Quick Analyze or a project to upload one.",
  "datasets.model": "Model",
  "datasets.plan": "Plan",

  // Analyses index
  "analyses.title": "All Analyses",
  "analyses.subtitle": "Every analysis run in this workspace.",
  "analyses.empty": "No analyses run yet.",
  "analyses.model_type": "Model",
  "analyses.dependent": "Dependent variable",

  // Reports index
  "reports.title": "All Reports",
  "reports.subtitle": "Every research report generated in this workspace.",
  "reports.empty": "No reports generated yet.",
  "reports.source": "Source",

  // Projects
  "projects.title": "Research Projects",
  "projects.subtitle":
    "Persistent workspaces for reproducible econometric research",
  "projects.new": "New Project",
  "projects.count_one": "project",
  "projects.count_other": "projects",
  "projects.show_archived": "Show archived",
  "projects.loading": "Loading projects...",
  "projects.empty_title": "No projects yet",
  "projects.empty_desc":
    "Create a new project to start organizing your research, or try the sample dataset to explore the platform.",
  "projects.try_sample": "Try Sample Dataset",
  "projects.creating": "Creating...",
  "projects.create_new": "Create New Project",
  "projects.all_projects": "All Projects",

  // Project detail
  "project.workspace": "Project Workspace",
  "project.artifacts": "Artifacts",
  "project.timeline": "Timeline",
  "project.view_all_events": "View all",
  "project.events": "events",
  "project.export_section": "Export",
  "project.pub_exports": "Publication Exports →",
  "project.loading": "Loading project...",
  "project.error_load": "Failed to load project",
  "project.datasets": "Datasets",
  "project.upload_dataset": "Upload Dataset",
  "project.no_datasets": "No datasets uploaded to this project yet.",

  // Project form
  "project_form.title_label": "Project Title",
  "project_form.title_placeholder": "e.g. Trade & GDP Analysis",
  "project_form.question_label": "Research Question",
  "project_form.question_placeholder":
    "e.g. How does trade openness affect GDP per capita?",
  "project_form.desc_label": "Description",
  "project_form.desc_placeholder": "Brief summary of the research scope",
  "project_form.create": "Create Project",
  "project_form.creating": "Creating…",

  // Model configuration
  "model.dep_var": "Dependent Variable",
  "model.primary_iv": "Primary Explanatory Variable",
  "model.controls": "Control Variables",
  "model.entity_col": "Entity Column",
  "model.time_col": "Time Column",
  "model.model_type": "Model Type",
  "model.run": "Run Analysis →",
  "model.running": "Running…",
  "model.robust_se": "Robust Standard Errors",
  "model.cluster_se": "Cluster by Entity",
  "model.intercept": "Include Intercept",
  "model.transformations": "Data Transformations",
  "model.ols": "OLS Regression",
  "model.robust_ols": "Robust OLS",
  "model.pooled_ols": "Pooled OLS",
  "model.fixed_effects": "Fixed Effects",
  "model.random_effects": "Random Effects",
  "model.two_way_fe": "Two-Way Fixed Effects",

  // Results
  "results.coefficients": "Coefficient Table",
  "results.diagnostics": "Diagnostics",
  "results.plots": "Plots",
  "results.compare": "Compare Models",
  "results.generate_report": "Generate Report",
  "results.export_json": "Export JSON",
  "results.coefficient_plot": "Coefficient Plot",
  "results.residual_plot": "Residual Plot",
  "results.actual_vs_predicted": "Actual vs. Predicted",
  "results.formula": "Formula",
  "results.observations": "Observations",

  // Discovery
  "discovery.title": "Exploratory Discovery",
  "discovery.subtitle":
    "Bounded specification search with multiple-testing correction",
  "discovery.run": "Run Discovery",
  "discovery.findings": "Findings",
  "discovery.correction_method": "Correction Method",

  // Reports detail
  "report.title": "Research Report",
  "report.download_md": "Download Markdown",
  "report.download_html": "Download HTML",
  "report.view_analysis": "View Analysis",

  // Publication export
  "pub.title": "Publication Export",
  "pub.format": "Format",
  "pub.docx": "Word (DOCX)",
  "pub.latex": "LaTeX",
  "pub.markdown": "Markdown",
  "pub.json": "JSON",
  "pub.generate": "Generate Export",
  "pub.download": "Download",

  // Comparison
  "compare.title": "Model Comparison",
  "compare.add_model": "Add Model",
  "compare.side_by_side": "Side-by-Side Comparison",
  "compare.stability": "Coefficient Stability",

  // Planning
  "plan.title": "Research Planning",
  "plan.question_label": "Research Question",
  "plan.generate": "Generate Plan",
  "plan.approve": "Approve Plan",
  "plan.candidate_vars": "Candidate Variables",
  "plan.suggested_models": "Suggested Models",
  "plan.causal_warning":
    "This analysis estimates statistical associations under the selected model. It should not be interpreted as causal evidence without an explicit identification strategy.",

  // Desktop
  "desktop.startup_title": "Starting AI Econometrics Copilot…",
  "desktop.recovery_title": "Something went wrong",
  "desktop.copy_diagnostics": "Copy Technical Details",
  "desktop.copied": "Copied!",
  "desktop.close_app": "Close Application",
  "desktop.about_title": "About AI Econometrics Copilot",

  // Errors
  "error.backend_unreachable":
    "The analysis engine is not reachable. Please check whether the backend is running.",
  "error.model_failed":
    "The recommended model could not be estimated with the selected variables. You can customize the model or try a simpler model.",
  "error.upload_failed":
    "The file could not be read. Please check that it is a CSV, XLSX, or XLS file.",
  "error.session_not_found":
    "The Quick Analyze session was not found. Please restart the workflow.",
  "error.unexpected": "An unexpected error occurred.",

  // Language switcher
  "lang.switch_to": "中文",
} as const;

export type TranslationKey = keyof typeof en;
