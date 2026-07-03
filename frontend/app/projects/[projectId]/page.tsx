"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ProjectOverview } from "@/components/projects/ProjectOverview";
import { ProjectTimeline } from "@/components/projects/ProjectTimeline";
import { ArtifactHistoryTable } from "@/components/projects/ArtifactHistoryTable";
import { ProjectDatasetList } from "@/components/projects/ProjectDatasetList";
import { ProjectExportActions } from "@/components/projects/ProjectExportActions";
import {
  getProject,
  getProjectTimeline,
  getProjectArtifacts,
} from "@/lib/api";
import type {
  ProjectResponse,
  ProjectArtifacts,
  TimelineEvent,
} from "@/types/project";

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [artifacts, setArtifacts] = useState<ProjectArtifacts | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [p, a, t] = await Promise.all([
        getProject(projectId),
        getProjectArtifacts(projectId),
        getProjectTimeline(projectId),
      ]);
      setProject(p);
      setArtifacts(a);
      setTimeline(t);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project");
    }
  }, [projectId]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (!project || !artifacts) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted">Loading project...</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-base font-semibold tracking-tight">
            Project Workspace
          </h1>
          <Link href="/projects">
            <Button variant="ghost">All Projects</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-6 py-8">
        <ProjectOverview project={project} onUpdated={setProject} />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <section className="rounded-lg border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                Artifacts
              </h3>
              <ArtifactHistoryTable artifacts={artifacts} />
            </section>

            <section className="rounded-lg border border-border bg-surface p-5">
              <ProjectDatasetList
                projectId={projectId}
                datasets={artifacts.datasets}
                onDatasetAdded={loadAll}
              />
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-lg border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                Timeline
              </h3>
              <ProjectTimeline events={timeline.slice(0, 10)} />
              {timeline.length > 10 && (
                <Link
                  href={`/projects/${projectId}/timeline`}
                  className="mt-2 block text-xs text-accent hover:underline"
                >
                  View all {timeline.length} events
                </Link>
              )}
            </section>

            <section className="rounded-lg border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                Export
              </h3>
              <ProjectExportActions projectId={projectId} />
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
