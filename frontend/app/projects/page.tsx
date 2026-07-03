"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { listProjects } from "@/lib/api";
import type { ProjectResponse } from "@/types/project";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    listProjects(showArchived)
      .then(setProjects)
      .finally(() => setLoading(false));
  }, [showArchived]);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              Research Projects
            </h1>
            <p className="text-xs text-muted">
              Persistent workspaces for reproducible econometric research
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/">
              <Button variant="ghost">Home</Button>
            </Link>
            <Link href="/projects/new">
              <Button>New Project</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-muted">
            {projects.length} project{projects.length !== 1 ? "s" : ""}
          </p>
          <label className="flex items-center gap-1.5 text-xs text-muted">
            <input
              type="checkbox"
              checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)}
              className="rounded"
            />
            Show archived
          </label>
        </div>

        {loading ? (
          <p className="py-10 text-center text-sm text-muted">
            Loading projects...
          </p>
        ) : projects.length === 0 ? (
          <div className="py-16 text-center">
            <p className="mb-4 text-sm text-muted">
              No projects yet. Create one to start organizing your research.
            </p>
            <Link href="/projects/new">
              <Button>Create First Project</Button>
            </Link>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <ProjectCard key={p.project_id} project={p} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
