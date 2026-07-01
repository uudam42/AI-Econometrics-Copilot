import type {
  ApiErrorPayload,
  DatasetOverview,
  DatasetProfileResponse,
} from "@/types/dataset";
import type {
  AnalysisConfigurationRequest,
  AnalysisResult,
  ModelDiagnosticsResponse,
} from "@/types/modeling";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  code: string;
  details: Record<string, unknown>;

  constructor(payload: ApiErrorPayload["error"]) {
    super(payload.message);
    this.code = payload.code;
    this.details = payload.details;
  }
}

async function parseErrorOrThrow(response: Response): Promise<never> {
  let payload: ApiErrorPayload | null = null;
  try {
    payload = await response.json();
  } catch {
    // response body was not JSON
  }
  if (payload?.error) {
    throw new ApiError(payload.error);
  }
  throw new Error(`Request failed with status ${response.status}`);
}

export async function uploadDataset(file: File): Promise<DatasetOverview> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/datasets/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function getDatasetOverview(
  datasetId: string
): Promise<DatasetOverview> {
  const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/overview`);
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function getDatasetProfile(
  datasetId: string
): Promise<DatasetProfileResponse> {
  const response = await fetch(`${API_BASE_URL}/datasets/${datasetId}/profile`);
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function runAnalysis(
  config: AnalysisConfigurationRequest
): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analyses/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}`);
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function getAnalysisDiagnostics(
  analysisId: string
): Promise<ModelDiagnosticsResponse> {
  const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}/diagnostics`);
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}

export async function exportAnalysisJson(analysisId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/analyses/${analysisId}/export/json`);
  if (!response.ok) {
    await parseErrorOrThrow(response);
  }
  return response.json();
}
