"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ProjectTimeline } from "@/components/projects/ProjectTimeline";
import { getProject, getProjectTimeline } from "@/lib/api";
import type { ProjectResponse, TimelineEvent } from "@/types/project";

export default function ProjectTimelinePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);

  useEffect(() => {
    Promise.all([
      getProject(projectId),
      getProjectTimeline(projectId),
    ]).then(([p, e]) => {
      setProject(p);
      setEvents(e);
    });
  }, [projectId]);

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
              {project.title} — Timeline
            </h1>
          </div>
          <Link href={`/projects/${projectId}`}>
            <Button variant="ghost">Back to Project</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-3xl flex-1 px-6 py-8">
        <ProjectTimeline events={events} />
      </main>
    </div>
  );
}
