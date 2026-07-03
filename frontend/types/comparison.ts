import type { ModelType, TransformationOperation, VariableSelectionRequest } from "./modeling";

export type ComparisonStatus = "completed" | "failed" | "unavailable";

export interface ModelFitSummary {
  r_squared: number | null;
  adj_r_squared: number | null;
  within_r_squared: number | null;
  between_r_squared: number | null;
  overall_r_squared: number | null;
  aic: number | null;
  bic: number | null;
  f_statistic: number | null;
  n_obs: number | null;
  n_entities: number | null;
  n_time_periods: number | null;
}

export interface DiagnosticSummary {
  max_vif: number | null;
  heteroskedasticity_detected: boolean | null;
  hausman_rejects_re: boolean | null;
  hausman_p_value: number | null;
  durbin_watson: number | null;
}

export interface CoefficientStabilityEntry {
  model_type: ModelType;
  model_label: string;
  coefficient: number | null;
  std_error: number | null;
  p_value: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  significance: string;
  direction: "positive" | "negative" | "zero" | "unavailable";
}

export interface ModelComparisonEntry {
  model_type: ModelType;
  model_label: string;
  status: ComparisonStatus;
  reason: string | null;
  formula: string | null;
  fit_metrics: ModelFitSummary | null;
  diagnostic_summary: DiagnosticSummary | null;
  standard_error_type: string | null;
  entity_effects: boolean | null;
  time_effects: boolean | null;
  warnings: string[];
}

export interface ModelScoreComponent {
  criterion: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface ModelSelectionRecommendation {
  recommended_model: ModelType;
  confidence: "high" | "medium" | "low";
  score: number;
  reasons: string[];
  warnings: string[];
  score_breakdown: ModelScoreComponent[];
  alternative_models: { model_type: ModelType; model_label: string; score: string; reason: string }[];
}

export interface ComparisonResult {
  comparison_id: string;
  dataset_id: string;
  dataset_filename: string;
  created_at: string;
  variable_selection: VariableSelectionRequest;
  transformation_summary: string;
  models: ModelComparisonEntry[];
  coefficient_stability: CoefficientStabilityEntry[];
  recommendation: ModelSelectionRecommendation;
  disclaimer: string;
}

export interface ComparisonRequest {
  dataset_id: string;
  variable_selection: VariableSelectionRequest;
  transformations: TransformationOperation[];
  candidate_models: ModelType[];
  cluster_standard_errors_by_entity: boolean;
}

export interface ReportArtifact {
  report_id: string;
  source_type: "analysis" | "comparison";
  source_id: string;
  title: string;
  research_question: string | null;
  created_at: string;
  significance_level: number;
  sections_included: string[];
  markdown_content: string;
  html_content: string;
  writing_rules_version: string;
  disclaimer: string;
}

export interface ReportGenerationRequest {
  source_type: "analysis" | "comparison";
  source_id: string;
  title?: string;
  research_question?: string;
  significance_level?: number;
  include_appendix?: boolean;
}
