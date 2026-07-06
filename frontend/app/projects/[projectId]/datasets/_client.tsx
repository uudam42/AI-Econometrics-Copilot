"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ProjectDatasetList } from "@/components/projects/ProjectDatasetList";
import { getProject, getProjectArtifacts } from "@/lib/api";
import type { ProjectResponse, DatasetSummary } from "@/types/project";

export default function ProjectDatasetsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);

  const load = useCallback(async () => {
    const [p, a] = await Promise.all([
      getProject(projectId),
      getProjectArtifacts(projectId),
    ]);
    setProject(p);
    setDatasets(a.datasets);
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  if (!project) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              {project.title} — Datasets
            </h1>
          </div>
          <Link href={`/projects/${projectId}`}>
            <Button variant="ghost">Back to Project</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-8">
        <ProjectDatasetList
          projectId={projectId}
          datasets={datasets}
          onDatasetAdded={load}
        />
      </main>
    </div>
  );
}
