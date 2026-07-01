"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CoefficientTable } from "@/components/results/CoefficientTable";
import { CoefficientPlot } from "@/components/results/CoefficientPlot";
import { ResidualPlot } from "@/components/results/ResidualPlot";
import { CorrelationHeatmap } from "@/components/results/CorrelationHeatmap";
import { DiagnosticsPanel } from "@/components/results/DiagnosticsPanel";
import {
  ApiError,
  getAnalysis,
  getAnalysisDiagnostics,
  exportAnalysisJson,
} from "@/lib/api";
import type { AnalysisResult, ModelDiagnosticsResponse } from "@/types/modeling";
import { MODEL_TYPE_LABELS } from "@/types/modeling";

function fmt(v: number | null, d = 4): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(d);
}

function ConfidenceBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    high: "bg-green-100 text-green-800",
    medium: "bg-amber-100 text-amber-800",
    low: "bg-stone-100 text-stone-600",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${styles[level] ?? styles.low}`}>
      {level} confidence
    </span>
  );
}

export default function AnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const router = useRouter();

  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [diagnostics, setDiagnostics] = useState<ModelDiagnosticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [res, diag] = await Promise.all([
          getAnalysis(analysisId),
          getAnalysisDiagnostics(analysisId),
        ]);
        setResult(res);
        setDiagnostics(diag);
      } catch (e) {
        setError(
          e instanceof ApiError || e instanceof Error
            ? e.message
            : "Failed to load analysis results."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [analysisId]);

  async function handleExport() {
    setExporting(true);
    try {
      const artifact = await exportAnalysisJson(analysisId);
      const blob = new Blob([JSON.stringify(artifact, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `analysis_${analysisId.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Non-fatal export error
    } finally {
      setExporting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted">Loading analysis results…</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-sm text-red-600">{error ?? "Analysis not found."}</p>
        <Button variant="secondary" className="mt-4" onClick={() => router.push("/")}>
          Back to upload
        </Button>
      </div>
    );
  }

  const isOLS = ["ols", "robust_ols"].includes(result.model_type);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold">Analysis Results</h1>
            <p className="text-xs text-muted">
              {result.dataset_filename} · {MODEL_TYPE_LABELS[result.model_type]}
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleExport} disabled={exporting}>
              {exporting ? "Exporting…" : "Export JSON"}
            </Button>
            <Button
              variant="secondary"
              onClick={() =>
                router.push(`/datasets/${result.dataset_id}/model`)
              }
            >
              ← Reconfigure
            </Button>
            <Button variant="secondary" onClick={() => router.push("/")}>
              New dataset
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 px-6 py-8">
        {/* Analysis overview */}
        <Card>
          <CardHeader>
            <CardTitle>Analysis Overview</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
              <div>
                <p className="text-xs text-muted">Model</p>
                <p className="font-medium">{MODEL_TYPE_LABELS[result.model_type]}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Observations</p>
                <p className="font-medium font-mono">{result.fit.n_obs}</p>
              </div>
              <div>
                <p className="text-xs text-muted">R²</p>
                <p className="font-medium font-mono">{fmt(result.fit.r_squared, 4)}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Adjusted R²</p>
                <p className="font-medium font-mono">{fmt(result.fit.adj_r_squared, 4)}</p>
              </div>
              {result.fit.aic !== null && (
                <div>
                  <p className="text-xs text-muted">AIC</p>
                  <p className="font-medium font-mono">{fmt(result.fit.aic, 2)}</p>
                </div>
              )}
              {result.fit.bic !== null && (
                <div>
                  <p className="text-xs text-muted">BIC</p>
                  <p className="font-medium font-mono">{fmt(result.fit.bic, 2)}</p>
                </div>
              )}
              {result.fit.f_statistic !== null && (
                <div>
                  <p className="text-xs text-muted">F-statistic</p>
                  <p className="font-medium font-mono">{fmt(result.fit.f_statistic, 3)}</p>
                </div>
              )}
            </div>
            <div className="mt-3 rounded bg-stone-100 px-3 py-2">
              <p className="font-mono text-xs text-foreground">{result.formula}</p>
            </div>
          </CardContent>
        </Card>

        {/* Model recommendation */}
        {result.recommendation && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle>Model Recommendation</CardTitle>
                <ConfidenceBadge level={result.recommendation.confidence} />
              </div>
            </CardHeader>
            <CardContent>
              <p className="mb-2 text-xs font-semibold text-muted uppercase tracking-wide">
                Suggested: {MODEL_TYPE_LABELS[result.recommendation.recommended_model]}
              </p>
              <ul className="mb-3 space-y-1">
                {result.recommendation.reasons.map((r, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span className="text-green-600">✓</span>
                    {r}
                  </li>
                ))}
              </ul>
              {result.recommendation.warnings.map((w, i) => (
                <p key={i} className="text-xs text-amber-700">
                  ⚠ {w}
                </p>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Variables used */}
        <Card>
          <CardHeader>
            <CardTitle>Variables</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
              <div>
                <p className="text-xs text-muted">Dependent</p>
                <p className="font-mono font-medium">{result.variable_selection.dependent_variable}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Primary Explanatory</p>
                <p className="font-mono font-medium">{result.variable_selection.primary_independent_variable}</p>
              </div>
              {result.variable_selection.control_variables.length > 0 && (
                <div>
                  <p className="text-xs text-muted">Controls</p>
                  <p className="font-mono font-medium">{result.variable_selection.control_variables.join(", ")}</p>
                </div>
              )}
              {result.variable_selection.entity_column && (
                <div>
                  <p className="text-xs text-muted">Entity Column</p>
                  <p className="font-mono font-medium">{result.variable_selection.entity_column}</p>
                </div>
              )}
              {result.variable_selection.time_column && (
                <div>
                  <p className="text-xs text-muted">Time Column</p>
                  <p className="font-mono font-medium">{result.variable_selection.time_column}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Transformation log */}
        {result.transformation_log.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Applied Transformations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {result.transformation_log.map((entry) => (
                  <div
                    key={entry.step}
                    className="flex items-start gap-3 rounded border border-border px-3 py-2 text-sm"
                  >
                    <span className="w-5 text-center font-mono text-muted">{entry.step}</span>
                    <div>
                      <p className="font-medium">{entry.operation}</p>
                      {entry.columns.length > 0 && (
                        <p className="text-xs text-muted">
                          Columns: {entry.columns.join(", ")}
                        </p>
                      )}
                      {entry.created_columns.length > 0 && (
                        <p className="text-xs text-green-700">
                          Created: {entry.created_columns.join(", ")}
                        </p>
                      )}
                      <p className="text-xs text-muted">
                        Rows: {entry.rows_before} → {entry.rows_after}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Coefficients */}
        <Card>
          <CardHeader>
            <CardTitle>Regression Coefficients</CardTitle>
            <CardDescription>
              All values computed by statsmodels / linearmodels. Coefficients reflect
              statistical associations under the selected model specification.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <CoefficientTable coefficients={result.coefficients} />
          </CardContent>
        </Card>

        {/* Coefficient plot */}
        <Card>
          <CardHeader>
            <CardTitle>Coefficient Plot (95% CI)</CardTitle>
          </CardHeader>
          <CardContent>
            <CoefficientPlot coefficients={result.coefficients} />
          </CardContent>
        </Card>

        {/* Residual plots — OLS only */}
        {result.plot_data && (
          <Card>
            <CardHeader>
              <CardTitle>Residual Diagnostics</CardTitle>
            </CardHeader>
            <CardContent>
              <ResidualPlot plotData={result.plot_data} />
            </CardContent>
          </Card>
        )}

        {/* Diagnostics */}
        {diagnostics && (
          <Card>
            <CardHeader>
              <CardTitle>Econometric Diagnostics</CardTitle>
            </CardHeader>
            <CardContent>
              <DiagnosticsPanel diagnostics={diagnostics} />
            </CardContent>
          </Card>
        )}

        {/* Correlation heatmap */}
        {diagnostics && (
          <Card>
            <CardHeader>
              <CardTitle>Correlation Matrix</CardTitle>
              <CardDescription>Pearson correlation among model variables.</CardDescription>
            </CardHeader>
            <CardContent>
              <CorrelationHeatmap data={diagnostics.correlation_matrix} />
            </CardContent>
          </Card>
        )}

        {/* Model metadata */}
        {Object.keys(result.model_metadata).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Model Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
                {Object.entries(result.model_metadata).map(([k, v]) => (
                  <div key={k}>
                    <p className="text-xs text-muted">{k.replace(/_/g, " ")}</p>
                    <p className="font-mono font-medium">{String(v)}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Disclaimer */}
        <div className="rounded-md border border-amber-200 bg-amber-50 p-4">
          <p className="text-xs text-amber-800">{result.disclaimer}</p>
        </div>
      </main>

      <footer className="border-t border-border py-3 text-center text-xs text-muted">
        AI Econometrics Copilot · Reproducible analysis · Analysis ID: {analysisId.slice(0, 8)}
      </footer>
    </div>
  );
}
