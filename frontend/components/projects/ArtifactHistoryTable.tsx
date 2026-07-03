"use client";

import Link from "next/link";
import type { ProjectArtifacts } from "@/types/project";

interface ArtifactRow {
  type: string;
  id: string;
  label: string;
  created_at: string;
  href: string;
}

function flattenArtifacts(artifacts: ProjectArtifacts): ArtifactRow[] {
  const rows: ArtifactRow[] = [];

  for (const d of artifacts.datasets) {
    rows.push({
      type: "Dataset",
      id: d.dataset_id,
      label: d.filename,
      created_at: d.uploaded_at,
      href: `/datasets/${d.dataset_id}/model`,
    });
  }
  for (const a of artifacts.analyses) {
    rows.push({
      type: "Analysis",
      id: a.analysis_id,
      label: a.dataset_filename,
      created_at: a.created_at,
      href: `/analyses/${a.analysis_id}`,
    });
  }
  for (const c of artifacts.comparisons) {
    rows.push({
      type: "Comparison",
      id: c.comparison_id,
      label: c.dataset_id.slice(0, 8),
      created_at: c.created_at,
      href: `/comparisons/${c.comparison_id}`,
    });
  }
  for (const p of artifacts.plans) {
    rows.push({
      type: "Plan",
      id: p.plan_id,
      label: p.approved ? "Approved" : "Draft",
      created_at: p.created_at,
      href: `/datasets/${p.dataset_id}/plan`,
    });
  }
  for (const r of artifacts.reports) {
    rows.push({
      type: "Report",
      id: r.report_id,
      label: `${r.source_type}`,
      created_at: r.created_at,
      href: `/reports/${r.report_id}`,
    });
  }
  for (const d of artifacts.discoveries) {
    rows.push({
      type: "Discovery",
      id: d.discovery_id,
      label: d.dataset_id.slice(0, 8),
      created_at: d.created_at,
      href: `/datasets/${d.dataset_id}/discover`,
    });
  }

  rows.sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );
  return rows;
}

export function ArtifactHistoryTable({
  artifacts,
}: {
  artifacts: ProjectArtifacts;
}) {
  const rows = flattenArtifacts(artifacts);

  if (rows.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted">
        No artifacts yet. Upload a dataset to get started.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted">
            <th className="pb-2 pr-4 font-medium">Type</th>
            <th className="pb-2 pr-4 font-medium">Label</th>
            <th className="pb-2 pr-4 font-medium">Date</th>
            <th className="pb-2 font-medium" />
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-border/50">
              <td className="py-2 pr-4">
                <span className="rounded bg-stone-100 px-1.5 py-0.5 text-xs font-medium text-stone-600">
                  {row.type}
                </span>
              </td>
              <td className="py-2 pr-4 text-foreground">{row.label}</td>
              <td className="py-2 pr-4 text-muted">
                {new Date(row.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </td>
              <td className="py-2 text-right">
                <Link
                  href={row.href}
                  className="text-xs text-accent hover:underline"
                >
                  View
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
