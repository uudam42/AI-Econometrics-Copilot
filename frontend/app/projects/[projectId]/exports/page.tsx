"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PublicationExportForm } from "@/components/publication-exports/PublicationExportForm";
import { PublicationExportList } from "@/components/publication-exports/PublicationExportList";
import { PublicationExportStatus } from "@/components/publication-exports/PublicationExportStatus";
import {
  createPublicationExport,
  getProject,
  getProjectArtifacts,
  listProjectPublicationExports,
} from "@/lib/api";
import type { ProjectResponse, ProjectArtifacts } from "@/types/project";
import type {
  ExportSourceType,
  PublicationExportConfig,
  PublicationExportListItem,
  PublicationExportResult,
} from "@/types/publication_export";

export default function ProjectExportsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [artifacts, setArtifacts] = useState<ProjectArtifacts | null>(null);
  const [exports, setExports] = useState<PublicationExportListItem[]>([]);
  const [latestResult, setLatestResult] =
    useState<PublicationExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [selectedSource, setSelectedSource] = useState<{
    type: ExportSourceType;
    id: string;
  } | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [p, a, e] = await Promise.all([
        getProject(projectId),
        getProjectArtifacts(projectId),
        listProjectPublicationExports(projectId),
      ]);
      setProject(p);
      setArtifacts(a);
      setExports(e);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleSubmit(config: PublicationExportConfig) {
    setLoading(true);
    setError(null);
    try {
      const result = await createPublicationExport(config);
      setLatestResult(result);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setLoading(false);
    }
  }

  if (error && !project) {
    return <p className="p-8 text-sm text-red-600">{error}</p>;
  }
  if (!project) {
    return <p className="p-8 text-sm text-muted-foreground">Loading...</p>;
  }

  const sources: { type: ExportSourceType; id: string; label: string }[] = [];
  if (artifacts) {
    artifacts.analyses.forEach((a) =>
      sources.push({
        type: "analysis",
        id: a.analysis_id,
        label: `Analysis ${a.analysis_id.slice(0, 8)}`,
      })
    );
    artifacts.comparisons.forEach((c) =>
      sources.push({
        type: "comparison",
        id: c.comparison_id,
        label: `Comparison ${c.comparison_id.slice(0, 8)}`,
      })
    );
    artifacts.reports.forEach((r) =>
      sources.push({
        type: "report",
        id: r.report_id,
        label: `Report ${r.report_id.slice(0, 8)}`,
      })
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-8">
      <div>
        <Link
          href={`/projects/${projectId}`}
          className="text-xs text-accent hover:underline"
        >
          &larr; Back to {project.title}
        </Link>
        <h1 className="mt-2 text-2xl font-bold">Publication Exports</h1>
        <p className="text-sm text-muted-foreground">
          Generate publication-ready reports from your analysis artifacts.
        </p>
      </div>

      {error && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {latestResult && <PublicationExportStatus result={latestResult} />}

      <div className="space-y-2">
        <h2 className="text-sm font-semibold">1. Select Source Artifact</h2>
        {sources.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No artifacts available. Run an analysis or comparison first.
          </p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {sources.map((s) => (
              <button
                key={`${s.type}-${s.id}`}
                onClick={() => setSelectedSource({ type: s.type, id: s.id })}
                className={`rounded border px-3 py-1.5 text-xs font-medium transition-colors ${
                  selectedSource?.id === s.id
                    ? "border-accent bg-accent/10 text-accent"
                    : "hover:bg-muted"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {selectedSource && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">2. Configure Export</h2>
          <PublicationExportForm
            sourceType={selectedSource.type}
            sourceId={selectedSource.id}
            projectId={projectId}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </div>
      )}

      {exports.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold">Previous Exports</h2>
          <PublicationExportList exports={exports} />
        </div>
      )}
    </div>
  );
}
