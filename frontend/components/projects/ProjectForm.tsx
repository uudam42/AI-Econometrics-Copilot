"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { ProjectCreateRequest } from "@/types/project";

interface ProjectFormProps {
  onSubmit: (req: ProjectCreateRequest) => Promise<void>;
  submitting?: boolean;
}

export function ProjectForm({ onSubmit, submitting }: ProjectFormProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [researchQuestion, setResearchQuestion] = useState("");
  const [tagsText, setTagsText] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const tags = tagsText
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);
    await onSubmit({
      title,
      description: description || undefined,
      research_question: researchQuestion || undefined,
      tags: tags.length ? tags : undefined,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="mb-1 block text-xs font-medium text-foreground">
          Project Title *
        </label>
        <input
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Trade & GDP Growth Study"
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-foreground">
          Research Question
        </label>
        <input
          type="text"
          value={researchQuestion}
          onChange={(e) => setResearchQuestion(e.target.value)}
          placeholder="e.g. Does international trade openness affect GDP growth?"
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-foreground">
          Description
        </label>
        <textarea
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Brief description of the project scope and goals..."
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
      </div>

      <div>
        <label className="mb-1 block text-xs font-medium text-foreground">
          Tags
        </label>
        <input
          type="text"
          value={tagsText}
          onChange={(e) => setTagsText(e.target.value)}
          placeholder="macro, trade, panel (comma-separated)"
          className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm focus:border-accent focus:outline-none"
        />
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={!title.trim() || submitting}>
          {submitting ? "Creating..." : "Create Project"}
        </Button>
      </div>
    </form>
  );
}
