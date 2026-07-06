export type ExportSourceType = "analysis" | "comparison" | "report" | "project";
export type TableStyle = "academic" | "compact" | "detailed";
export type ExportFormat = "markdown" | "html" | "docx" | "latex" | "json";

export interface PublicationExportConfig {
  project_id?: string | null;
  source_type: ExportSourceType;
  source_id: string;

  title: string;
  subtitle?: string | null;
  author_name?: string | null;
  institution_name?: string | null;
  course_or_supervisor?: string | null;
  report_date?: string | null;

  selected_model_id?: string | null;
  selected_table_style?: TableStyle;

  include_cover_page?: boolean;
  include_executive_summary?: boolean;
  include_dataset_section?: boolean;
  include_variable_table?: boolean;
  include_descriptive_statistics?: boolean;
  include_regression_table?: boolean;
  include_model_comparison?: boolean;
  include_diagnostics?: boolean;
  include_figures?: boolean;
  include_methodology_section?: boolean;
  include_limitations_section?: boolean;
  include_appendix?: boolean;
  include_reproducibility_appendix?: boolean;

  output_formats?: ExportFormat[];
}

export interface FigureMetadata {
  figure_id: string;
  figure_type: string;
  caption: string;
  filename: string;
  source_artifact_id: string;
  variables: string[];
  model_type?: string | null;
  generated_at?: string | null;
}

export interface PublicationExportResult {
  export_id: string;
  project_id?: string | null;
  source_type: ExportSourceType;
  source_id: string;
  title: string;
  created_at: string;
  available_formats: ExportFormat[];
  figures: FigureMetadata[];
  sections_included: string[];
  disclaimer: string;
}

export interface PublicationExportListItem {
  export_id: string;
  title: string;
  source_type: ExportSourceType;
  source_id: string;
  created_at: string;
  available_formats: ExportFormat[];
}
