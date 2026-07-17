"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useI18n } from "@/lib/i18n";
import {
  ApiError,
  getDatasetOverview,
  quickAnalyzeConfirm,
  quickAnalyzePlan,
  quickAnalyzeUpload,
} from "@/lib/api";
import type { I18nError } from "@/lib/api";
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
  const { t } = useI18n();
  const steps: { key: Stage; label: string }[] = [
    { key: "upload", label: t("qa.step_upload") },
    { key: "review", label: t("qa.step_review") },
    { key: "results", label: t("qa.step_results") },
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
  const { t } = useI18n();
  const items = [
    { label: t("diag.data_quality"), value: d.data_quality, bad: d.data_quality === "Needs review" },
    { label: t("diag.model_fit"), value: d.model_fit, bad: d.model_fit === "Limited" },
    { label: t("diag.multicollinearity"), value: d.multicollinearity, bad: d.multicollinearity !== "Low concern" },
    { label: t("diag.heteroskedasticity"), value: d.heteroskedasticity, bad: d.heteroskedasticity.startsWith("Detected") },
    { label: t("diag.panel_structure"), value: d.panel_structure, bad: false },
    { label: t("diag.causal_interpretation"), value: d.causal_interpretation, bad: false },
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
  const { t } = useI18n();
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
      const key = (err as I18nError)?.i18nKey;
      setError(
        key ? t(key)
          : err instanceof ApiError || err instanceof Error
            ? err.message
            : t("error.upload_failed")
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t("qa.upload_title")}</h2>
        <p className="mt-1 text-sm text-muted">{t("qa.upload_desc")}</p>
      </div>

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
            <p className="text-sm font-medium">{t("qa.drop_zone")}</p>
            <p className="mt-1 text-xs text-muted">{t("qa.drop_zone_hint")}</p>
          </>
        )}
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium">
          {t("qa.question_label")}{" "}
          <span className="font-normal text-muted">{t("qa.question_optional")}</span>
        </label>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={t("qa.question_placeholder")}
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <p className="mt-1 text-xs text-muted">{t("qa.question_hint")}</p>
      </div>

      {error && <p className="rounded border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      <Button onClick={handleSubmit} disabled={!file || uploading} className="w-full sm:w-auto">
        {uploading ? t("qa.uploading") : t("qa.continue")}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Review stage
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
  const { t } = useI18n();
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
      entity_column: rec.entity_column ?? null,
      time_column: rec.time_column ?? null,
      model_type: modelType,
      apply_log_transform_to: logTransform,
      analysis_intent: "association",
    };
    try {
      const result = await quickAnalyzeConfirm(sessionId, body);
      onConfirmed(result);
    } catch (err) {
      const key = (err as I18nError)?.i18nKey;
      setError(
        key ? t(key)
          : err instanceof ApiError || err instanceof Error
            ? err.message
            : t("error.model_failed")
      );
    } finally {
      setRunning(false);
    }
  }

  const modelOptions = [
    { value: "ols", label: t("model.ols") },
    { value: "robust_ols", label: t("model.robust_ols") },
    { value: "pooled_ols", label: t("model.pooled_ols") },
    { value: "fixed_effects", label: t("model.fixed_effects") },
    { value: "random_effects", label: t("model.random_effects") },
    { value: "two_way_fixed_effects", label: t("model.two_way_fe") },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{t("qa.review_title")}</h2>
        <p className="mt-1 text-sm text-muted">{t("qa.review_desc")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("qa.recommended")}: {rec.recommended_model}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-xs text-muted">{t("qa.detected_structure")}: {rec.detected_structure}</p>
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

      <Card>
        <CardHeader><CardTitle>{t("qa.var_selection")}</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium">
                {t("qa.outcome_var")} <span className="text-red-500">{t("qa.required")}</span>
              </label>
              <Select value={dep} onChange={(e) => setDep(e.target.value)} required>
                <option value="">{t("qa.select_placeholder")}</option>
                {colOptions.map((c) => <option key={c} value={c}>{c}</option>)}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium">
                {t("qa.main_expl_var")} <span className="text-red-500">{t("qa.required")}</span>
              </label>
              <Select value={primary} onChange={(e) => setPrimary(e.target.value)} required>
                <option value="">{t("qa.select_placeholder")}</option>
                {colOptions.map((c) => <option key={c} value={c}>{c}</option>)}
              </Select>
            </div>
          </div>

          {colOptions.length > 0 && (
            <div>
              <label className="mb-1 block text-xs font-medium">{t("qa.control_vars")}</label>
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
            <label className="mb-1 block text-xs font-medium">{t("qa.model")}</label>
            <Select value={modelType} onChange={(e) => setModelType(e.target.value)}>
              {modelOptions.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </Select>
          </div>

          {rec.transformation_suggestions.length > 0 && (
            <div>
              <label className="mb-1 block text-xs font-medium">{t("qa.optional_log")}</label>
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
        <Button onClick={handleRun} disabled={!dep || !primary || running}>
          {running ? t("qa.running_model") : t("qa.run_analysis")}
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
  const { t } = useI18n();
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">{summary.headline}</h2>
        <p className="mt-1 text-sm text-muted">{summary.dataset_description}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>
            {summary.is_significant ? t("qa.association_found") : t("qa.no_association")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm leading-relaxed">{summary.main_finding}</p>
          <p className="text-xs text-muted">{summary.model_used}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>{t("qa.diagnostics_overview")}</CardTitle></CardHeader>
        <CardContent>
          <DiagnosticsGrid d={summary.diagnostics_status} />
        </CardContent>
      </Card>

      {summary.key_warnings.length > 0 && (
        <div className="space-y-1 rounded border border-amber-200 bg-amber-50 px-4 py-3">
          <p className="text-xs font-medium text-amber-700">{t("qa.warnings")}</p>
          {summary.key_warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-700">⚠ {w}</p>
          ))}
        </div>
      )}

      <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-xs text-blue-700">
        <span className="font-medium">{t("qa.causal_note_label")}</span>
        {summary.causal_warning}
      </div>

      <Card>
        <CardHeader><CardTitle>{t("qa.next_actions")}</CardTitle></CardHeader>
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
          <Button>{t("qa.open_workspace")}</Button>
        </Link>
        <Link href="/quick-analyze">
          <Button variant="secondary">{t("qa.start_new")}</Button>
        </Link>
        <Link href="/projects">
          <Button variant="ghost">{t("qa.my_projects")}</Button>
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function QuickAnalyzePage() {
  const { t } = useI18n();
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
        const key = (err as I18nError)?.i18nKey;
        setErrorMsg(
          key ? t(key)
            : err instanceof ApiError || err instanceof Error
              ? err.message
              : t("error.unexpected")
        );
        setStage("error");
      }
    },
    [t]
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
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <div>
            <Link href="/" className="text-sm font-semibold hover:text-accent">
              {t("common.back_home")}
            </Link>
            <p className="text-xs text-muted">{t("qa.title")}</p>
          </div>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <StepIndicator current={stage} />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-10">
        {stage === "upload" && (
          <UploadStage onUploaded={handleUploaded} />
        )}

        {stage === "planning" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold">{t("qa.analysing_title")}</h2>
            <p className="text-sm text-muted">{t("qa.analysing_desc")}</p>
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="animate-pulse">●</span>
              {uploadInfo
                ? `${uploadInfo.filename} (${uploadInfo.n_rows} ${t("common.rows")}, ${uploadInfo.n_columns} ${t("common.columns")})`
                : t("qa.processing")}
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
            <h2 className="text-lg font-semibold">{t("qa.fitting_model")}</h2>
            <div className="flex items-center gap-2 text-sm text-muted">
              <span className="animate-pulse">●</span>
              {t("qa.fitting_desc")}
            </div>
          </div>
        )}

        {stage === "results" && runResp && (
          <ResultsStage summary={runResp.summary} analysisId={runResp.analysis_id} />
        )}

        {stage === "error" && (
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-red-600">{t("qa.error_title")}</h2>
            <p className="text-sm">{errorMsg ?? t("error.unexpected")}</p>
            <Button onClick={() => { setStage("upload"); setSessionId(null); setPlanResp(null); setErrorMsg(null); }}>
              {t("qa.start_over")}
            </Button>
          </div>
        )}
      </main>

      <footer className="border-t border-border py-4 text-center text-xs text-muted">
        {t("qa.footer")}
      </footer>
    </div>
  );
}
