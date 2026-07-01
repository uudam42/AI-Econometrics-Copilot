export type ModelType =
  | "ols"
  | "robust_ols"
  | "pooled_ols"
  | "fixed_effects"
  | "random_effects"
  | "two_way_fixed_effects";

export type TransformationOp =
  | "drop_duplicates"
  | "drop_missing_rows"
  | "median_imputation"
  | "mean_imputation"
  | "winsorize"
  | "log_transform"
  | "standardize";

export interface VariableSelectionRequest {
  dataset_id: string;
  dependent_variable: string;
  primary_independent_variable: string;
  control_variables: string[];
  entity_column: string | null;
  time_column: string | null;
}

export interface TransformationOperation {
  operation: TransformationOp;
  columns: string[];
  parameters: Record<string, unknown>;
}

export interface AnalysisConfigurationRequest {
  dataset_id: string;
  variable_selection: VariableSelectionRequest;
  transformations: TransformationOperation[];
  model_type: ModelType;
  include_intercept: boolean;
  robust_standard_errors: boolean;
  cluster_standard_errors_by_entity: boolean;
}

export interface TransformationLogEntry {
  step: number;
  operation: string;
  columns: string[];
  parameters: Record<string, unknown>;
  reason: string;
  rows_before: number;
  rows_after: number;
  created_columns: string[];
}

export interface CoefficientResult {
  variable: string;
  coefficient: number | null;
  std_error: number | null;
  t_stat: number | null;
  p_value: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  significance: string;
}

export interface ModelFitStatistics {
  r_squared: number | null;
  adj_r_squared: number | null;
  f_statistic: number | null;
  f_pvalue: number | null;
  aic: number | null;
  bic: number | null;
  n_obs: number;
  formula: string;
}

export interface PlotData {
  fitted_values: number[];
  actual_values: number[];
  residuals: number[];
}

export interface ModelRecommendation {
  recommended_model: ModelType;
  confidence: "high" | "medium" | "low";
  reasons: string[];
  warnings: string[];
}

export interface AnalysisResult {
  analysis_id: string;
  dataset_id: string;
  dataset_filename: string;
  created_at: string;
  model_type: ModelType;
  formula: string;
  variable_selection: VariableSelectionRequest;
  transformation_log: TransformationLogEntry[];
  coefficients: CoefficientResult[];
  fit: ModelFitStatistics;
  plot_data: PlotData | null;
  model_metadata: Record<string, unknown>;
  recommendation: ModelRecommendation | null;
  disclaimer: string;
}

export interface VIFResult {
  variable: string;
  vif: number;
  risk_level: string;
  interpretation: string;
}

export interface DiagnosticTestResult {
  name: string;
  statistic: number | null;
  p_value: number | null;
  interpretation: string;
  available: boolean;
  unavailable_reason: string | null;
}

export interface HausmanTestResult {
  available: boolean;
  statistic: number | null;
  degrees_of_freedom: number | null;
  p_value: number | null;
  recommendation: string | null;
  unavailable_reason: string | null;
}

export interface DescriptiveStats {
  variable: string;
  count: number;
  mean: number | null;
  std: number | null;
  min: number | null;
  q25: number | null;
  median: number | null;
  q75: number | null;
  max: number | null;
  missing_count: number;
  skewness: number | null;
}

export interface CorrelationMatrixResult {
  variables: string[];
  matrix: (number | null)[][];
}

export interface ModelDiagnosticsResponse {
  analysis_id: string;
  descriptive_stats: DescriptiveStats[];
  correlation_matrix: CorrelationMatrixResult;
  vif: VIFResult[];
  breusch_pagan: DiagnosticTestResult;
  jarque_bera: DiagnosticTestResult;
  durbin_watson: DiagnosticTestResult;
  hausman: HausmanTestResult;
}

export const MODEL_TYPE_LABELS: Record<ModelType, string> = {
  ols: "OLS (Ordinary Least Squares)",
  robust_ols: "Robust OLS (HC1 Standard Errors)",
  pooled_ols: "Pooled OLS",
  fixed_effects: "Fixed Effects (Within Estimator)",
  random_effects: "Random Effects (GLS)",
  two_way_fixed_effects: "Two-Way Fixed Effects",
};

export const PANEL_MODELS: ModelType[] = [
  "pooled_ols",
  "fixed_effects",
  "random_effects",
  "two_way_fixed_effects",
];

export const CROSS_SECTION_MODELS: ModelType[] = ["ols", "robust_ols"];
