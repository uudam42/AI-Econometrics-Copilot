export type DiscoveryMode = "guided" | "open";
export type MultipleTestingMethod = "benjamini_hochberg" | "bonferroni" | "none";
export type SupportLevel = "strong" | "moderate" | "weak" | "insufficient" | "not_suitable";
export type StabilityLabel = "stable" | "partially_stable" | "sensitive" | "insufficient_evidence";

export interface DiscoveryConfig {
  dataset_id: string;
  mode: DiscoveryMode;
  outcome_variables: string[];
  excluded_variables: string[];
  maximum_outcomes: number;
  maximum_predictors_per_outcome: number;
  maximum_controls_per_model: number;
  maximum_specifications: number;
  multiple_testing_method: MultipleTestingMethod;
  significance_level: number;
  min_observations: number;
  max_missing_rate: number;
  min_unique_values: number;
}

export interface VariableEligibility {
  column_name: string;
  eligible: boolean;
  exclusion_reasons: string[];
  missing_rate: number | null;
  unique_values: number | null;
  is_constant: boolean;
  quality_score: number;
}

export interface SpecificationResult {
  spec_id: string;
  status: "completed" | "failed" | "rejected";
  outcome_variable: string;
  primary_predictor: string;
  controls: string[];
  model_type: string;
  formula: string | null;
  coefficient: number | null;
  std_error: number | null;
  p_value: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  n_obs: number | null;
  r_squared: number | null;
  direction: string | null;
  significance: string;
  warnings: string[];
  failure_reason: string | null;
  absorbed_variables: string[] | null;
}

export interface CorrectedResult {
  spec_id: string;
  raw_p_value: number | null;
  adjusted_p_value: number | null;
  correction_method: string;
  passes_threshold: boolean;
}

export interface StabilityAssessment {
  outcome_variable: string;
  primary_predictor: string;
  n_specifications: number;
  n_completed: number;
  n_corrected_significant: number;
  direction_consistent: boolean;
  significance_consistent: boolean;
  coefficient_range: number[] | null;
  stability_label: StabilityLabel;
  specifications_used: string[];
}

export interface FindingScoreComponent {
  criterion: string;
  score: number;
  weight: number;
  explanation: string;
}

export interface ExploratoryFinding {
  finding_id: string;
  outcome_variable: string;
  primary_predictor: string;
  relationship_direction: string;
  exploratory_score: number;
  support_level: SupportLevel;
  raw_p_value: number | null;
  adjusted_q_value: number | null;
  multiple_testing_method: string;
  stability_label: StabilityLabel;
  best_coefficient: number | null;
  best_n_obs: number | null;
  best_r_squared: number | null;
  score_breakdown: FindingScoreComponent[];
  specification_ids: string[];
  warnings: string[];
}

export interface DiscoveryResult {
  discovery_id: string;
  dataset_id: string;
  dataset_filename: string;
  mode: DiscoveryMode;
  config: DiscoveryConfig;
  created_at: string;
  eligibility_results: VariableEligibility[];
  candidate_outcomes: string[];
  candidate_predictors: Record<string, string[]>;
  specifications_generated: number;
  specifications_completed: number;
  specifications_failed: number;
  specification_results: SpecificationResult[];
  corrected_results: CorrectedResult[];
  stability_assessments: StabilityAssessment[];
  findings: ExploratoryFinding[];
  disclaimer: string;
}

export const SUPPORT_LEVEL_LABELS: Record<SupportLevel, string> = {
  strong: "Strong Exploratory Support",
  moderate: "Moderate Exploratory Support",
  weak: "Weak Exploratory Support",
  insufficient: "Insufficient Evidence",
  not_suitable: "Not Suitable for Interpretation",
};

export const STABILITY_LABELS: Record<StabilityLabel, string> = {
  stable: "Stable across tested specifications",
  partially_stable: "Partially stable across tested specifications",
  sensitive: "Sensitive to specification choice",
  insufficient_evidence: "Insufficient evidence for stability assessment",
};

export const CORRECTION_LABELS: Record<MultipleTestingMethod, string> = {
  benjamini_hochberg: "Benjamini-Hochberg FDR",
  bonferroni: "Bonferroni",
  none: "No Correction (Warning: prone to false positives)",
};
