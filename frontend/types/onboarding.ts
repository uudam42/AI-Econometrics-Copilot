export interface OnboardingStatus {
  has_projects: boolean;
  has_demo: boolean;
  sample_data_available: boolean;
}

export interface DemoProjectResponse {
  project_id: string;
  dataset_id: string;
  title: string;
  message: string;
}
