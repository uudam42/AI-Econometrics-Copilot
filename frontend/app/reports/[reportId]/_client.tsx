"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResearchReportViewer } from "@/components/reports/ResearchReportViewer";
import { ReportMetadataPanel } from "@/components/reports/ReportMetadataPanel";
import { ReportExportActions } from "@/components/reports/ReportExportActions";
import { getReport } from "@/lib/api";
import type { ReportArtifact } from "@/types/comparison";

export default function ReportPage() {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ReportArtifact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getReport(reportId)
      .then(setReport)
      .catch(() => setError("Report not found."))
      .finally(() => setLoading(false));
  }, [reportId]);

  if (loading) return <div className="p-8 text-center text-muted">Loading report…</div>;
  if (error || !report) return <div className="p-8 text-center text-red-600">{error ?? "Error."}</div>;

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">{report.title}</h1>
          {report.research_question && (
            <p className="mt-1 text-sm text-muted italic">&ldquo;{report.research_question}&rdquo;</p>
          )}
          <p className="mt-1 text-xs text-muted font-mono">{report.report_id}</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Export</CardTitle>
        </CardHeader>
        <CardContent>
          <ReportExportActions report={report} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Report</CardTitle>
        </CardHeader>
        <CardContent>
          <ResearchReportViewer report={report} />
        </CardContent>
      </Card>

      <ReportMetadataPanel report={report} />

      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        <strong>Disclaimer:</strong> {report.disclaimer}
      </div>

      <div className="flex justify-between text-sm">
        <Link href="/" className="text-blue-600 underline underline-offset-2">← New dataset</Link>
        <Link
          href={`/${report.source_type === "comparison" ? "comparisons" : "analyses"}/${report.source_id}`}
          className="text-blue-600 underline underline-offset-2"
        >
          View source {report.source_type} →
        </Link>
      </div>
    </div>
  );
}
