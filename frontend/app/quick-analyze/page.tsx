"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import {
  ApiError,
  getDatasetOverview,
  quickAnalyzeConfirm,
  quickAnalyzePlan,
  quickAnalyzeUpload,
} from "@/lib/api";
import type {
  BeginnerSummary,
  ConfirmationRequest,
  DiagnosticsStatusCard,
  QuickAnalyzePlanResponse,
  QuickAnalyzeUploadResponse,
  RecommendationCard,
} from "@/types/quick_analyze";

// ---------------------------------------------------------------------------
// Stage types
// ---------------------------------------------------------------------------
type Stage = "upload" | "planning" | "review" | "running" | "results" | "error";

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StepIndicator({ current }: { current: Stage }) {
  const steps: { key: Stage; label: string }[] = [
    { key: "upload", label: "Upload" },
    { key: "review", label: "Review" },
    { key: "results", label: "Results" },
  ];
  const order: Stage[] = ["upload", "planning", "review", "running", "results", "error"];
  const idx = order.indexOf(current);

  return (
    <div className="flex items-center gap-2 text-xs">
      {steps.map((s, i) => {
        const sIdx = order.indexOf(s.key);
        const done = idx > sIdx;
        const active = idx === sIdx || (s.key === "review" && current === "planning") || (s.key === "results" && current === "running");
        return (
          <span key={s.key} className="flex items-center gap-2">
            {i > 0 && <span className="text-muted">→</span>}
            <span
              className={
                done
                  ? "font-medium text-green-600"
                  : active
                  ? "font-semibold text-accent"
                  : "text-muted"
              }
            >
              {s.label}
            </span>
          </span>
        );
      })}
    </div>
  );
}

function DiagnosticsGrid({ d }: { d: DiagnosticsStatusCard }) {
  const items = [
    { label: "Data quality", value: d.data_quality, bad: d.data_quality === "Needs review" },
    { label: "Model fit", value: d.model_fit, bad: d.model_fit === "Limited" },
    { label: "Multicollinearity", value: d.multicollinearity, bad: d.multicollinearity !== "Low concern" },
    { label: "Heteroskedasticity", value: d.heteroskedasticity, bad: d.heteroskedasticity.startsWith("Detected") },
    { label: "Panel structure", value: d.panel_structure, bad: false },
    { label: "Causal interpretation", value: d.causal_interpretation, bad: false },
  ];
  return (
    <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label} className="rounded border border-border bg-surface px-3 py-2">
          <p className="text-muted">{item.label}</p>
          <p className={item.bad ? "font-medium text-amber-600" : "font-medium text-green-600"}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Upload stage
// ---------------------------------------------------------------------------

function UploadStage({
  onUploaded,
}: {
  onUploaded: (up: QuickAnalyzeUploadResponse, question: string) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }

  async function handleSubmit() {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await quickAnalyzeUpload(file, question || undefined);
      onUploaded(result, question);
    } catch (err) {
      setError(
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Upload failed. Please try again."
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Upload Your Data</h2>
        <p className="mt-1 text-sm text-muted">
          Upload an Excel (.xlsx, .xls) or CSV file. We will automatically detect the
          structure and suggest the right model.
        </p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`cursor-pointer rounded-lg border-2 border-dashed px-6 py-12 text-center transition-colors ${
          dragging ? "border-accent bg-accent/5" : "border-border hover:border-accent/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx,.xls,.csv"
          className="hidden"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        {file ? (
          <p className="text-sm font-medium">{file.name}</p>
        ) : (
          <>
            <p className="text-sm font-medium">Drop file here or click to browse</p>
            <p className="mt-1 text-xs text-muted">Excel or CSV</p>
          </>
        )}
      </div>

      {/* Optional question */}
      <div>
        <label className="mb-1 block text-sm font-medium">
          Research question{" "}
          <span className="font-normal text-muted">(optional)</span>
        </label>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Does education affect income?"
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <p className="mt-1 text-xs text-muted">
          Leave blank for an exploratory overview of your dataset.
        </p>
      </div>

      {error && <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <Button onClick={handleSubmit} disabled={!file || uploading} className="w-full sm:w-auto">
        {uploading ? "Uploading…" : "Continue →"}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Review stage — recommendation card + confirmation form
// ---------------------------------------------------------------------------

function ReviewStage({
  sessionId,
  rec,
  datasetColumns,
  onConfirmed,
}: {
  sessionId: string;
  rec: RecommendationCard;
  datasetColumns: string[];
  onConfirmed: (summary: import("@/types/quick_analyze").QuickAnalyzeRunResponse) => void;
}) {
  const [dep, setDep] = useState(
    rec.outcome_variable.startsWith("(") ? "" : rec.outcome_variable
  );
  const [primary, setPrimary] = useState(
    rec.main_variable.startsWith("(") ? "" : rec.main_variable
  );
  const [controls, setControls] = useState<string[]>(rec.control_variables);
  const [modelType, setModelType] = useState(rec.recommended_model_type);
  const [logTransform, setLogTransform] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const colOptions = datasetColumns.length > 0 ? datasetColumns : [];

  function toggleControl(col: string) {
    setControls((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  }

  function toggleLog(col: string) {
    setLogTransform((prev) =>
      prev.includes(col) ? prev.filter((c) => c !== col) : [...prev, col]
    );
  }

  async function handleRun() {
    if (!dep || !primary) return;
    setRunning(true);
    setError(null);
    const body: ConfirmationRequest = {
      dependent_variable: dep,
      primary_independent_variable: primary,
      control_variables: controls,
      entity_column: null,
      time_column: null,
      model_type: modelType,
      apply_log_transform_to: logTransform,
      analysis_intent: "association",
    };
    try {
      const result = await quickAnalyzeConfirm(sessionId, body);
      onConfirmed(result);
    } catch (err) {
      setError(
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Analysis failed. Check variable selection and try again."
      );
    } finally {
      setRunning(false);
    }
  }

  const modelOptions = [
    { value: "ols", label: "OLS Regression" },
    { value: "robust_ols", label: "Robust OLS" },
    { value: "pooled_ols", label: "Pooled OLS" },
    { value: "fixed_effects", label: "Fixed Effects" },
    { value: "random_effects", label: "Random Effects" },
    { value: "two_way_fixed_effects", label: "Two-Way Fixed Effects" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Review Recommendation</h2>
        <p className="mt-1 text-sm text-muted">
          We analysed your dataset and suggest the setup below. Review and confirm before
          running — you can change any field.
        </p>
      </div>

      {/* Why this model */}
      <Card>
        <CardHeader>
          <CardTitle>Recommended: {rec.recommended_model}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-xs text-muted">Detected structure: {rec.detected_structure}</p>
          <ul className="space-y-1">
            {rec.why_reasons.map((r, i) => (
              <li key={i} className="text-xs">• {r}</li>
            ))}
          </ul>
          {rec.warnings.length > 0 && (
            <div className="mt-3 space-y-1 rounded border border-amber-200 bg-amber-50 px-3 py-2">
              {rec.warnings.map((w, i) => (
                <p key={i} className="text-xs text-amber-700">⚠ {w}</p>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Variable selection */}
      <Card>
        <CardHeader><CardTitle>Variable Selection</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium">
                Outcome variable <span className="text-red-500">*</span>
              </label>
              <Select value={dep} onChange={(e) => setDep(e.target.value)} required>
                <option value="">— select —</option>
                {colOptions.map((c) => <option key={c} value={c}>{c}</option>)}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium">
                Main explanatory variable <span className="text-red-500">*</span>
              </label>
              <Select value={primary} onChange={(e) => setPrimary(e.target.value)} required>
                <option value="">— select —</option>
                {colOptions.map((c) => <option key={c} value={c}>{c}</option>)}
              </Select>
            </div>
          </div>

          {colOptions.length > 0 && (
            <div>
              <label className="mb-1 block text-xs font-medium">Control variables</label>
              <div className="flex flex-wrap gap-2">
                {colOptions
                  .filter((c) => c !== dep && c !== primary)
                  .map((c) => (
                    <button
                      key={c}
                      type="button"
                      onClick={() => toggleControl(c)}
                      className={`rounded-full border px-3 py-0.5 text-xs transition-colors ${
                        controls.includes(c)
                          ? "border-accent bg-accent/10 text-accent"
                          : "border-border text-muted hover:border-accent/50"
                      }`}
                    >
                      {c}
                    </button>
                  ))}
              </div>
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs font-medium">Model</label>
            <Select value={modelType} onChange={(e) => setModelType(e.target.value)}>
              {modelOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
          </div>

          {rec.transformation_suggestions.length > 0 && (
            <div>
              <label className="mb-1 block text-xs font-medium">
                Optional log-transformations
              </label>
              <div className="space-y-1">
                {rec.transformation_suggestions.map((hint, i) => {
                  const col = hint.match(/'([^']+)'/)?.[1];
                  if (!col) return null;
                  return (
                    <label key={i} className="flex items-center gap-2 text-xs">
                      <input
                        type="checkbox"
                        checked={logTransform.includes(col)}
                        onChange={() => toggleLog(col)}
                        className="rounded"
                      />
                      <span>{hint}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {error && (
        <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">
          {error}
        </p>
      )}

      <div className="flex gap-3">
        <Button
          onClick={handleRun}
          disabled={!dep || !primary || running}
        >
          {running ? "Running model…" : "Run Analysis →"}
        </Button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results stage
// ---------------------------------------------------------------------------

function ResultsStage({
  summary,
  analysisId,
}: {
  summary: BeginnerSummary;
  analysisId: string;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{summary.headline}</h2>
        <p className="mt-1 text-sm text-muted">{summary.dataset_description}</p>
      </div>

      {/* Main finding */}
      <Card>
        <CardHeader>
          <CardTitle>
            {summary.is_significant ? "Association Found" : "No Clear Association"}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm leading-relaxed">{summary.main_finding}</p>
          <p className="text-xs text-muted">{summary.model_used}</p>
        </CardContent>
      </Card>

      {/* Diagnostics */}
      <Card>
        <CardHeader><CardTitle>Diagnostics Overview</CardTitle></CardHeader>
        <CardContent>
          <DiagnosticsGrid d={summary.diagnostics_status} />
        </CardContent>
      </Card>

      {/* Warnings */}
      {summary.key_warnings.length > 0 && (
        <div className="space-y-1 rounded border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-xs font-medium text-amber-700">Warnings</p>
          {summary.key_warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-700">⚠ {w}</p>
          ))}
        </div>
      )}

      {/* Causal warning — always shown */}
      <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-xs text-blue-700">
        <span className="font-medium">Note: </span>
        {summary.causal_warning}
      </div>

      {/* Next actions */}
      <Card>
        <CardHeader><CardTitle>What to do next</CardTitle></CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {summary.next_actions.map((a, i) => (
              <li key={i} className="text-sm">• {a}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-3">
        <Link href={`/analyses/${analysisId}`}>
          <Button>Open Full Workspace →</Button>
        </Link>
        <Link href="/quick-analyze">
          <Button variant="secondary">Start New Analysis</Button>
        </Link>
        <Link href="/projects">
          <Button variant="ghost">My Projects</Button>
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function QuickAnalyzePage() {
  const [stage, setStage] = useState<Stage>("upload");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadInfo, setUploadInfo] = useState<QuickAnalyzeUploadResponse | null>(null);
  const [planResp, setPlanResp] = useState<QuickAnalyzePlanResponse | null>(null);
  const [runResp, setRunResp] = useState<import("@/types/quick_analyze").QuickAnalyzeRunResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [datasetColumns, setDatasetColumns] = useState<string[]>([]);

  const handleUploaded = useCallback(
    async (up: QuickAnalyzeUploadResponse, _question: string) => {
      setUploadInfo(up);
      setSessionId(up.session_id);
      setStage("planning");
      setErrorMsg(null);
      try {
        const [plan, overview] = await Promise.all([
          quickAnalyzePlan(up.session_id),
          getDatasetOverview(up.dataset_id).catch(() => null),
        ]);
        if (overview?.column_types) {
          setDatasetColumns(overview.column_types.map((c) => c.name));
        }
        setPlanResp(plan);
        setStage("review");
      } catch (err) {
        setErrorMsg(
          err instanceof ApiError || err instanceof Error
            ? err.message
            : "Planning failed. Please try again."
        );
        setStage("error");
      }
    },
    []
  );

  const handleConfirmed = useCallback(
    (resp: import("@/types/quick_analyze").QuickAnalyzeRunResponse) => {
      setRunResp(resp);
      setStage("results");
    },
    []
  );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div>
            <Link href="/" className="text-sm font-semibold hover:text-accent">
              ← AI Econometrics Copilot
            </Link>
            <p className="text-xs text-muted">Quick Analyze</p>
          </div>
          <StepIndicator current={stage} />
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        {stage === "upload" && (
          <UploadStage onUploaded={handleUploaded} />
        )}

        {stage === "planning" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Analysing Your Data…</h2>
            <p className="text-sm text-muted">
              We are profiling the dataset and detecting its structure. This usually takes
              a few seconds.
            </p>
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="animate-pulse">●</span>
              {uploadInfo
                ? `Processing ${uploadInfo.filename} (${uploadInfo.n_rows} rows, ${uploadInfo.n_columns} columns)`
                : "Processing…"}
            </div>
          </div>
        )}

        {stage === "review" && planResp && (
          <ReviewStage
            sessionId={sessionId!}
            rec={planResp.recommendation}
            datasetColumns={datasetColumns}
            onConfirmed={handleConfirmed}
          />
        )}

        {stage === "running" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">Running Model…</h2>
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="animate-pulse">●</span>
              Fitting the econometric model and computing diagnostics…
            </div>
          </div>
        )}

        {stage === "results" && runResp && (
          <ResultsStage summary={runResp.summary} analysisId={runResp.analysis_id} />
        )}

        {stage === "error" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-red-600">Something went wrong</h2>
            <p className="text-sm">{errorMsg ?? "An unexpected error occurred."}</p>
            <Button onClick={() => { setStage("upload"); setSessionId(null); setPlanResp(null); setErrorMsg(null); }}>
              Start Over
            </Button>
          </div>
        )}
      </main>

      <footer className="border-t border-border py-4 text-center text-xs text-muted">
        This analysis identifies statistical associations only — not causal effects.
      </footer>
    </div>
  );
}
