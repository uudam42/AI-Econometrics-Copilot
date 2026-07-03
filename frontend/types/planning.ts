import type { ModelType } from "./modeling";

export type VariableRole =
  | "dependent_variable"
  | "primary_independent_variable"
  | "control_variable"
  | "entity_column"
  | "time_column"
  | "unresolved";

export type AnalysisIntent =
  | "association"
  | "exploratory"
  | "causal_claim_requested"
  | "unclear";

export interface CandidateVariable {
  column_name: string;
  role: VariableRole;
  confidence: number;
  evidence: string[];
  warnings: string[];
}

export interface SuggestedTransformation {
  operation: string;
  columns: string[];
  confidence: number;
  reason: string;
  requires_user_confirmation: boolean;
}

export interface SuggestedModel {
  model_type: string;
  confidence: number;
  reasons: string[];
  requirements: string[];
  warnings: string[];
}

export interface ResearchPlan {
  plan_id: string;
  dataset_id: string;
  research_question: string;
  normalized_question: string;
  user_context: string | null;
  inferred_analysis_intent: AnalysisIntent;
  candidate_variables: CandidateVariable[];
  suggested_transformations: SuggestedTransformation[];
  suggested_models: SuggestedModel[];
  detected_structure_summary: string;
  ambiguities: string[];
  causal_warning: string;
  user_approval_required: boolean;
}

export interface PlanGenerationRequest {
  dataset_id: string;
  research_question: string;
  context?: string;
  preferred_outcome?: string;
  preferred_primary_independent_variable?: string;
}

export interface PlanApprovalRequest {
  dependent_variable: string;
  primary_independent_variable: string;
  control_variables: string[];
  entity_column: string | null;
  time_column: string | null;
  approved_transformations: Record<string, unknown>[];
  selected_candidate_models: string[];
}

export interface PlanApprovalResult {
  plan_id: string;
  approved: boolean;
  variable_selection: Record<string, unknown>;
  transformations: Record<string, unknown>[];
  candidate_models: string[];
  redirect_path: string;
}

export const VARIABLE_ROLE_LABELS: Record<VariableRole, string> = {
  dependent_variable: "Dependent Variable",
  primary_independent_variable: "Primary Independent Variable",
  control_variable: "Control Variable",
  entity_column: "Entity Column",
  time_column: "Time Column",
  unresolved: "Unresolved",
};

export const INTENT_LABELS: Record<AnalysisIntent, string> = {
  association: "Association Analysis",
  exploratory: "Exploratory Analysis",
  causal_claim_requested: "Causal Claim (Reframed as Association)",
  unclear: "Unclear Intent",
};
