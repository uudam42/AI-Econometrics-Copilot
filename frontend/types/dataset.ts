export type InferredRole =
  | "numeric"
  | "categorical"
  | "datetime"
  | "identifier"
  | "boolean"
  | "text"
  | "unknown";

export interface ColumnTypeInfo {
  name: string;
  pandas_dtype: string;
  inferred_role: InferredRole;
  unique_count: number;
  unique_ratio: number;
  role_hints: string[];
}

export interface DatasetOverview {
  dataset_id: string;
  filename: string;
  n_rows: number;
  n_columns: number;
  column_types: ColumnTypeInfo[];
  preview_rows: Record<string, unknown>[];
  uploaded_at: string;
}

export interface ColumnQualityReport {
  column: string;
  dtype: string;
  missing_count: number;
  missing_rate: number;
  duplicate_value_count: number;
  is_constant: boolean;
  outlier_count: number | null;
  outlier_method: string | null;
  zero_ratio: number | null;
  negative_ratio: number | null;
  skewness: number | null;
  kurtosis: number | null;
  suggested_transformation: string | null;
  reason: string | null;
}

export interface DatasetQualityReport {
  dataset_id: string;
  n_rows: number;
  n_columns: number;
  duplicate_row_count: number;
  duplicate_row_rate: number;
  constant_columns: string[];
  potential_id_columns: string[];
  potential_time_columns: string[];
  potential_categorical_columns: string[];
  columns: ColumnQualityReport[];
}

export type DatasetType = "panel" | "time_series" | "cross_sectional" | "unknown";

export interface StructureDetectionResult {
  dataset_type: DatasetType;
  entity_column: string | null;
  time_column: string | null;
  is_balanced_panel: boolean | null;
  entity_count: number | null;
  time_period_count: number | null;
  explanation: string;
}

export interface DatasetProfileResponse {
  dataset_id: string;
  quality: DatasetQualityReport;
  structure: StructureDetectionResult;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}
