"use client";

import { cn } from "@/lib/utils";
import type { ProjectStatus } from "@/types/project";

const styles: Record<ProjectStatus, string> = {
  draft: "bg-stone-100 text-stone-600",
  active: "bg-emerald-50 text-emerald-700",
  archived: "bg-amber-50 text-amber-700",
};

export function ProjectStatusBadge({ status }: { status: ProjectStatus }) {
  return (
    <span
      className={cn(
        "inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize",
        styles[status]
      )}
    >
      {status}
    </span>
  );
}
