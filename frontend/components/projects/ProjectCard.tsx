"use client";

import Link from "next/link";
import { ProjectStatusBadge } from "./ProjectStatusBadge";
import type { ProjectResponse } from "@/types/project";

function timeAgo(iso: string): string {
  const seconds = Math.floor(
    (Date.now() - new Date(iso).getTime()) / 1000
  );
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function ProjectCard({ project }: { project: ProjectResponse }) {
  return (
    <Link
      href={`/projects/${project.project_id}`}
      className="block rounded-lg border border-border bg-surface p-4 transition-shadow hover:shadow-md"
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground truncate">
          {project.title}
        </h3>
        <ProjectStatusBadge status={project.status} />
      </div>

      {project.research_question && (
        <p className="mb-2 text-xs text-muted line-clamp-2">
          {project.research_question}
        </p>
      )}

      <div className="flex items-center gap-3 text-xs text-muted">
        {project.tags.length > 0 && (
          <span className="truncate">
            {project.tags.map((t) => `#${t}`).join(" ")}
          </span>
        )}
        <span className="ml-auto shrink-0">
          Updated {timeAgo(project.updated_at)}
        </span>
      </div>
    </Link>
  );
}
