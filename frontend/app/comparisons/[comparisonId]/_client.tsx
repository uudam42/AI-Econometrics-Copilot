"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ModelComparisonTable } from "@/components/comparison/ModelComparisonTable";
import { ModelRecommendationCard } from "@/components/comparison/ModelRecommendationCard";
import { ModelScoreBreakdown } from "@/components/comparison/ModelScoreBreakdown";
import { CoefficientStabilityTable } from "@/components/comparison/CoefficientStabilityTable";
import { getComparison, exportComparisonJson, generateReport } from "@/lib/api";
import type { ComparisonResult } from "@/types/comparison";

function fmt(v: number | null | undefined, dec = 3): string {
  if (v == null) return "—";
  return v.toFixed(dec);
}

export default function ComparisonPage() {
  const { comparisonId } = useParams<{ comparisonId: string }>();
  const router = useRouter();

  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  useEffect(() => {
    getComparison(comparisonId)
      .then(setComparison)
      .catch(() => setError("Comparison not found."))
      .finally(() => setLoading(false));
  }, [comparisonId]);

  async function handleExport() {
    if (!comparison) return;
    const artifact = await exportComparisonJson(comparisonId);
    const blob = new Blob([JSON.stringify(artifact, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `comparison_${comparisonId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function handleGenerateReport() {
    setGeneratingReport(true);
    try {
      const report = await generateReport({
        source_type: "comparison",
        source_id: comparisonId,
        significance_level: 0.05,
        include_appendix: true,
      });
      router.push(`/reports/${report.report_id}`);
    } finally {
      setGeneratingReport(false);
    }
  }

  if (loading) return <div className="p-8 text-center text-muted">Loading comparison…</div>;
  if (error || !comparison) return <div className="p-8 text-center text-red-600">{error ?? "Error loading comparison."}</div>;

  const completed = comparison.models.filter((m) => m.status === "completed");
  const failed = comparison.models.filter((m) => m.status !== "completed");
  const vs = comparison.variable_selection;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Comparison Results</h1>
          <p className="mt-1 text-sm text-muted">
            {comparison.dataset_filename} — {comparison.created_at.slice(0, 19).replace("T", " ")} UTC
          </p>
          <p className="mt-0.5 text-xs text-muted font-mono">{comparisonId}</p>
        </div>
        <div className="flex gap-2 flex-shrink-0">
          <Button onClick={handleExport} variant="secondary">Export JSON</Button>
          <Button onClick={handleGenerateReport} disabled={generatingReport}>
            {generatingReport ? "Generating…" : "Generate Report →"}
          </Button>
        </div>
      </div>

      {/* Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Comparison Overview</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 text-sm">
          <div className="space-y-1">
            <p><span className="text-muted">Dependent variable:</span> <strong>{vs.dependent_variable}</strong></p>
            <p><span className="text-muted">Primary IV:</span> <strong>{vs.primary_independent_variable}</strong></p>
            {vs.control_variables.length > 0 && (
              <p><span className="text-muted">Controls:</span> {vs.control_variables.join(", ")}</p>
            )}
            {vs.entity_column && <p><span className="text-muted">Entity:</span> {vs.entity_column}</p>}
            {vs.time_column && <p><span className="text-muted">Time:</span> {vs.time_column}</p>}
          </div>
          <div className="space-y-1">
            <p><span className="text-muted">Models run:</span> {comparison.models.length}</p>
            <p><span className="text-muted">Completed:</span> {completed.length}</p>
            <p><span className="text-muted">Failed / unavailable:</span> {failed.length}</p>
            <p><span className="text-muted">Transformations:</span> {comparison.transformation_summary}</p>
          </div>
        </CardContent>
      </Card>

      {/* Recommendation */}
      <Card>
        <CardHeader>
          <CardTitle>Model Recommendation</CardTitle>
          <CardDescription>Rule-driven, multi-criteria recommendation — not solely based on R².</CardDescription>
        </CardHeader>
        <CardContent>
          <ModelRecommendationCard rec={comparison.recommendation} />
        </CardContent>
      </Card>

      {/* Comparison table */}
      <Card>
        <CardHeader>
          <CardTitle>Model Comparison Table</CardTitle>
        </CardHeader>
        <CardContent>
          <ModelComparisonTable models={comparison.models} />
        </CardContent>
      </Card>

      {/* Coefficient stability */}
      {comparison.coefficient_stability.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Coefficient Stability Across Specifications</CardTitle>
          </CardHeader>
          <CardContent>
            <CoefficientStabilityTable
              entries={comparison.coefficient_stability}
              primaryIv={vs.primary_independent_variable}
            />
          </CardContent>
        </Card>
      )}

      {/* Score breakdown */}
      {comparison.recommendation.score_breakdown.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recommendation Score Breakdown</CardTitle>
            <CardDescription>
              Score for the recommended model: <strong>{comparison.recommendation.recommended_model}</strong>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ModelScoreBreakdown components={comparison.recommendation.score_breakdown} />
          </CardContent>
        </Card>
      )}

      {/* Diagnostic summary from completed models */}
      {completed.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Diagnostic Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="bg-muted/40 text-left">
                    <th className="border px-3 py-2">Model</th>
                    <th className="border px-3 py-2">Max VIF</th>
                    <th className="border px-3 py-2">Hetero.</th>
                    <th className="border px-3 py-2">Hausman rejects RE</th>
                    <th className="border px-3 py-2">Durbin-Watson</th>
                  </tr>
                </thead>
                <tbody>
                  {completed.map((m) => {
                    const d = m.diagnostic_summary;
                    return (
                      <tr key={m.model_type} className="hover:bg-muted/20">
                        <td className="border px-3 py-2 font-medium">{m.model_label}</td>
                        <td className="border px-3 py-2">{fmt(d?.max_vif, 1)}</td>
                        <td className="border px-3 py-2">
                          {d?.heteroskedasticity_detected == null ? "—" : d.heteroskedasticity_detected ? "Yes" : "No"}
                        </td>
                        <td className="border px-3 py-2">
                          {d?.hausman_rejects_re == null ? "—" : d.hausman_rejects_re ? `Yes (p=${fmt(d.hausman_p_value)})` : `No (p=${fmt(d.hausman_p_value)})`}
                        </td>
                        <td className="border px-3 py-2">{fmt(d?.durbin_watson, 3)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <strong>Disclaimer:</strong> {comparison.disclaimer}
      </div>

      {/* Navigation */}
      <div className="flex justify-between text-sm">
        <Link href="/" className="text-blue-600 underline underline-offset-2">← New dataset</Link>
        <Button onClick={handleGenerateReport} disabled={generatingReport}>
          {generatingReport ? "Generating report…" : "Generate Research Report →"}
        </Button>
      </div>
    </div>
  );
}
