"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ProjectCard } from "@/components/projects/ProjectCard";
import { createDemoProject, listProjects } from "@/lib/api";
import type { ProjectResponse } from "@/types/project";

export default function ProjectsPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [creatingDemo, setCreatingDemo] = useState(false);

  useEffect(() => {
    setLoading(true);
    listProjects(showArchived)
      .then(setProjects)
      .finally(() => setLoading(false));
  }, [showArchived]);

  async function handleStartDemo() {
    setCreatingDemo(true);
    try {
      const result = await createDemoProject();
      router.push(`/projects/${result.project_id}`);
    } catch {
      setCreatingDemo(false);
    }
  }

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
            <p className="mb-2 text-sm font-medium">No projects yet</p>
            <p className="mb-6 text-sm text-muted max-w-md mx-auto">
              Create a new project to start organizing your research, or try the
              sample dataset to explore the platform.
            </p>
            <div className="flex justify-center gap-3">
              <Button onClick={handleStartDemo} disabled={creatingDemo}>
                {creatingDemo ? "Creating..." : "Try Sample Dataset"}
              </Button>
              <Link href="/projects/new">
                <Button variant="secondary">Create New Project</Button>
              </Link>
            </div>
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
