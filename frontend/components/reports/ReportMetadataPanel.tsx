"use client";

import type { ReportArtifact } from "@/types/comparison";

export function ReportMetadataPanel({ report }: { report: ReportArtifact }) {
  const created = new Date(report.created_at).toLocaleString();
  return (
    <div className="rounded-lg border p-4 space-y-2 text-xs">
      <p className="font-semibold uppercase tracking-wide text-muted text-xs">Report Metadata</p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-1">
        <span className="text-muted">Report ID</span>
        <span className="font-mono text-xs break-all">{report.report_id}</span>
        <span className="text-muted">Source type</span>
        <span className="capitalize">{report.source_type}</span>
        <span className="text-muted">Source ID</span>
        <span className="font-mono text-xs break-all">{report.source_id}</span>
        <span className="text-muted">Generated</span>
        <span>{created}</span>
        <span className="text-muted">Significance level</span>
        <span>{(report.significance_level * 100).toFixed(0)}%</span>
        <span className="text-muted">Writing rules</span>
        <span>v{report.writing_rules_version}</span>
      </div>
      {report.sections_included.length > 0 && (
        <div>
          <p className="text-muted mb-1">Sections included:</p>
          <div className="flex flex-wrap gap-1">
            {report.sections_included.map((s) => (
              <span key={s} className="rounded bg-muted/50 px-1.5 py-0.5 text-xs">{s}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
