"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ProjectForm } from "@/components/projects/ProjectForm";
import { createProject } from "@/lib/api";
import type { ProjectCreateRequest } from "@/types/project";

export default function NewProjectPage() {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(req: ProjectCreateRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const project = await createProject(req);
      router.push(`/projects/${project.project_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <h1 className="text-base font-semibold tracking-tight">
            New Project
          </h1>
          <Link href="/projects">
            <Button variant="ghost">Back to Projects</Button>
          </Link>
        </div>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 px-6 py-8">
        {error && (
          <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        <ProjectForm onSubmit={handleCreate} submitting={submitting} />
      </main>
    </div>
  );
}
