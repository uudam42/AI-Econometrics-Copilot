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

// ─── Comparison API ────────────────────────────────────────────────────────

export async function runComparison(
  request: import("@/types/comparison").ComparisonRequest
): Promise<import("@/types/comparison").ComparisonResult> {
  const response = await fetch(`${API_BASE_URL}/comparisons/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getComparison(
  comparisonId: string
): Promise<import("@/types/comparison").ComparisonResult> {
  const response = await fetch(`${API_BASE_URL}/comparisons/${comparisonId}`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function exportComparisonJson(comparisonId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/comparisons/${comparisonId}/export/json`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

// ─── Reports API ───────────────────────────────────────────────────────────

export async function generateReport(
  request: import("@/types/comparison").ReportGenerationRequest
): Promise<import("@/types/comparison").ReportArtifact> {
  const response = await fetch(`${API_BASE_URL}/reports/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getReport(
  reportId: string
): Promise<import("@/types/comparison").ReportArtifact> {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getReportMarkdown(reportId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/markdown`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.text();
}

export async function getReportHtml(reportId: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}/html`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.text();
}

// ─── Planning API ─────────────────────────────────────────────────────────

export async function generatePlan(
  request: import("@/types/planning").PlanGenerationRequest
): Promise<import("@/types/planning").ResearchPlan> {
  const response = await fetch(`${API_BASE_URL}/plans/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getPlan(
  planId: string
): Promise<import("@/types/planning").ResearchPlan> {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function approvePlan(
  planId: string,
  approval: import("@/types/planning").PlanApprovalRequest
): Promise<import("@/types/planning").PlanApprovalResult> {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(approval),
  });
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function exportPlanJson(planId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/export/json`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

// ─── Discovery API ────────────────────────────────────────────────────────

export async function runDiscovery(
  config: import("@/types/discovery").DiscoveryConfig
): Promise<import("@/types/discovery").DiscoveryResult> {
  const response = await fetch(`${API_BASE_URL}/discovery/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
  });
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getDiscovery(
  discoveryId: string
): Promise<import("@/types/discovery").DiscoveryResult> {
  const response = await fetch(`${API_BASE_URL}/discovery/${discoveryId}`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function getDiscoveryFindings(
  discoveryId: string
): Promise<import("@/types/discovery").ExploratoryFinding[]> {
  const response = await fetch(`${API_BASE_URL}/discovery/${discoveryId}/findings`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function exportDiscoveryJson(discoveryId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/discovery/${discoveryId}/export/json`);
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}

export async function createPlanFromFinding(
  discoveryId: string,
  findingId: string
): Promise<import("@/types/planning").ResearchPlan> {
  const response = await fetch(
    `${API_BASE_URL}/discovery/${discoveryId}/findings/${findingId}/create-plan`,
    { method: "POST" }
  );
  if (!response.ok) await parseErrorOrThrow(response);
  return response.json();
}
