"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import { updateProject } from "@/lib/api";
import type { ProjectResponse, ProjectStatus } from "@/types/project";

interface ProjectOverviewProps {
  project: ProjectResponse;
  onUpdated: (p: ProjectResponse) => void;
}

export function ProjectOverview({ project, onUpdated }: ProjectOverviewProps) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(project.title);
  const [description, setDescription] = useState(project.description);
  const [researchQuestion, setResearchQuestion] = useState(
    project.research_question
  );
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setSaving(true);
    try {
      const updated = await updateProject(project.project_id, {
        title,
        description,
        research_question: researchQuestion,
      });
      onUpdated(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  async function handleStatusChange(status: ProjectStatus) {
    const updated = await updateProject(project.project_id, { status });
    onUpdated(updated);
  }

  if (editing) {
    return (
      <div className="rounded-lg border border-border bg-surface p-5 space-y-3">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm font-semibold focus:border-accent focus:outline-none"
        />
        <input
          value={researchQuestion}
          onChange={(e) => setResearchQuestion(e.target.value)}
          placeholder="Research question"
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
        <textarea
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description"
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setEditing(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <div className="mb-3 flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">
            {project.title}
          </h2>
          {project.research_question && (
            <p className="mt-1 text-sm text-muted italic">
              {project.research_question}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ProjectStatusBadge status={project.status} />
          <Button variant="ghost" onClick={() => setEditing(true)}>
            Edit
          </Button>
        </div>
      </div>

      {project.description && (
        <p className="mb-3 text-sm text-foreground">{project.description}</p>
      )}

      {project.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1">
          {project.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-stone-100 px-2 py-0.5 text-xs text-stone-600"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 text-xs text-muted">
        <span>
          Created{" "}
          {new Date(project.created_at).toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
          })}
        </span>
        <span className="mx-1">|</span>
        {project.status === "draft" && (
          <button
            className="text-emerald-600 hover:underline"
            onClick={() => handleStatusChange("active")}
          >
            Activate
          </button>
        )}
        {project.status === "active" && (
          <button
            className="text-amber-600 hover:underline"
            onClick={() => handleStatusChange("archived")}
          >
            Archive
          </button>
        )}
        {project.status === "archived" && (
          <button
            className="text-emerald-600 hover:underline"
            onClick={() => handleStatusChange("active")}
          >
            Reactivate
          </button>
        )}
      </div>
    </div>
  );
}
