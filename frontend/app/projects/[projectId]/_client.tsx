"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { useI18n } from "@/lib/i18n";
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
  const { t } = useI18n();
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [artifacts, setArtifacts] = useState<ProjectArtifacts | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    try {
      const [p, a, tl] = await Promise.all([
        getProject(projectId),
        getProjectArtifacts(projectId),
        getProjectTimeline(projectId),
      ]);
      setProject(p);
      setArtifacts(a);
      setTimeline(tl);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("project.error_load"));
    }
  }, [projectId, t]);

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
        <p className="text-sm text-muted">{t("project.loading")}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-base font-semibold tracking-tight">
            {t("project.workspace")}
          </h1>
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <Link href="/projects">
              <Button variant="ghost">{t("projects.all_projects")}</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-6 py-8">
        <ProjectOverview project={project} onUpdated={setProject} />

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <section className="rounded-lg border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                {t("project.artifacts")}
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
                {t("project.timeline")}
              </h3>
              <ProjectTimeline events={timeline.slice(0, 10)} />
              {timeline.length > 10 && (
                <Link
                  href={`/projects/${projectId}/timeline`}
                  className="mt-2 block text-xs text-accent hover:underline"
                >
                  {t("project.view_all_events")} {timeline.length} {t("project.events")}
                </Link>
              )}
            </section>

            <section className="rounded-lg border border-border bg-surface p-5">
              <h3 className="mb-3 text-sm font-semibold text-foreground">
                {t("project.export_section")}
              </h3>
              <ProjectExportActions projectId={projectId} />
              <Link
                href={`/projects/${projectId}/exports`}
                className="mt-3 block text-xs text-accent hover:underline"
              >
                {t("project.pub_exports")}
              </Link>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}
