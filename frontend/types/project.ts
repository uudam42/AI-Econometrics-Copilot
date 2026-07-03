export type ProjectStatus = "draft" | "active" | "archived";

export interface ProjectCreateRequest {
  title: string;
  description?: string;
  research_question?: string;
  tags?: string[];
  research_context?: string;
  notes?: string;
  methodology_notes?: string;
}

export interface ProjectUpdateRequest {
  title?: string;
  description?: string;
  research_question?: string;
  status?: ProjectStatus;
  tags?: string[];
  default_dataset_id?: string;
  research_context?: string;
  notes?: string;
  methodology_notes?: string;
}

export interface ProjectResponse {
  project_id: string;
  title: string;
  description: string;
  research_question: string;
  status: ProjectStatus;
  tags: string[];
  default_dataset_id: string | null;
  research_context: string;
  notes: string;
  methodology_notes: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  event_type: string;
  artifact_type: string | null;
  artifact_id: string | null;
  description: string;
  created_at: string;
}

export interface DatasetSummary {
  dataset_id: string;
  filename: string;
  n_rows: number;
  n_columns: number;
  uploaded_at: string;
}

export interface ProjectArtifacts {
  datasets: DatasetSummary[];
  plans: { plan_id: string; dataset_id: string; approved: boolean; created_at: string }[];
  analyses: { analysis_id: string; dataset_id: string; dataset_filename: string; created_at: string }[];
  comparisons: { comparison_id: string; dataset_id: string; created_at: string }[];
  reports: { report_id: string; source_type: string; source_id: string; created_at: string }[];
  discoveries: { discovery_id: string; dataset_id: string; created_at: string }[];
}

export interface ProjectExport {
  project: ProjectResponse;
  artifacts: ProjectArtifacts;
  timeline: TimelineEvent[];
  disclaimer: string;
}
