export type QuickAnalyzeStage =
  | "created"
  | "uploaded"
  | "profiled"
  | "planned"
  | "awaiting_confirmation"
  | "running"
  | "complete"
  | "failed";

export type AnalysisIntentChoice = "association" | "exploratory";

export interface RecommendationCard {
  outcome_variable: string;
  main_variable: string;
  control_variables: string[];
  entity_column: string | null;
  time_column: string | null;
  detected_structure: string;
  recommended_model: string;
  recommended_model_type: string;
  transformation_suggestions: string[];
  why_reasons: string[];
  warnings: string[];
  is_exploratory: boolean;
  needs_user_input: string | null;
}

export interface DiagnosticsStatusCard {
  data_quality: "Good" | "Needs review";
  model_fit: "Available" | "Limited";
  multicollinearity: "Low concern" | "Moderate concern" | "High concern";
  heteroskedasticity:
    | "Not detected"
    | "Detected — robust standard errors recommended";
  panel_structure: "Detected" | "Not detected";
  causal_interpretation: "Association only";
}

export interface BeginnerSummary {
  headline: string;
  dataset_description: string;
  model_used: string;
  main_finding: string;
  is_significant: boolean;
  significance_threshold: number;
  causal_warning: string;
  key_warnings: string[];
  diagnostics_status: DiagnosticsStatusCard;
  next_actions: string[];
}

export interface QuickAnalyzeSession {
  session_id: string;
  stage: QuickAnalyzeStage;
  project_id: string | null;
  dataset_id: string | null;
  plan_id: string | null;
  analysis_id: string | null;
  research_question: string | null;
  analysis_intent: AnalysisIntentChoice;
  recommendation: RecommendationCard | null;
  summary: BeginnerSummary | null;
  progress_message: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface QuickAnalyzeUploadResponse {
  session_id: string;
  dataset_id: string;
  project_id: string;
  filename: string;
  n_rows: number;
  n_columns: number;
  stage: QuickAnalyzeStage;
}

export interface QuickAnalyzePlanResponse {
  session_id: string;
  stage: QuickAnalyzeStage;
  recommendation: RecommendationCard;
  progress_message: string;
}

export interface ConfirmationRequest {
  dependent_variable: string;
  primary_independent_variable: string;
  control_variables: string[];
  entity_column: string | null;
  time_column: string | null;
  model_type: string;
  apply_log_transform_to: string[];
  analysis_intent: AnalysisIntentChoice;
}

export interface QuickAnalyzeRunResponse {
  session_id: string;
  stage: QuickAnalyzeStage;
  analysis_id: string;
  summary: BeginnerSummary;
  progress_message: string;
}

export interface QuickAnalyzeSessionDetail {
  session: QuickAnalyzeSession;
  workspace_url: string | null;
}
