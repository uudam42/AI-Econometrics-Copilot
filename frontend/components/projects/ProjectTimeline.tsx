"use client";

import type { TimelineEvent } from "@/types/project";

const eventIcons: Record<string, string> = {
  dataset_uploaded: "📊",
  analysis_executed: "📈",
  comparison_completed: "⚖️",
  plan_created: "📋",
  report_generated: "📄",
  discovery_completed: "🔍",
};

export function ProjectTimeline({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted">
        No activity recorded yet.
      </p>
    );
  }

  return (
    <div className="space-y-0">
      {events.map((event, i) => (
        <div key={i} className="flex gap-3 py-2">
          <div className="flex flex-col items-center">
            <span className="text-base">
              {eventIcons[event.event_type] ?? "●"}
            </span>
            {i < events.length - 1 && (
              <div className="mt-1 flex-1 border-l border-border" />
            )}
          </div>
          <div className="min-w-0 flex-1 pb-2">
            <p className="text-sm text-foreground">{event.description}</p>
            <p className="mt-0.5 text-xs text-muted">
              {new Date(event.created_at).toLocaleString(undefined, {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
