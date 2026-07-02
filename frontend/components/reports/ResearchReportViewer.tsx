"use client";

import { useState } from "react";
import type { ReportArtifact } from "@/types/comparison";

export function ResearchReportViewer({ report }: { report: ReportArtifact }) {
  const [view, setView] = useState<"rendered" | "markdown">("rendered");

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setView("rendered")}
          className={`rounded px-3 py-1.5 text-xs font-semibold transition-colors ${
            view === "rendered"
              ? "bg-foreground text-background"
              : "bg-muted hover:bg-muted/80"
          }`}
        >
          Rendered HTML
        </button>
        <button
          onClick={() => setView("markdown")}
          className={`rounded px-3 py-1.5 text-xs font-semibold transition-colors ${
            view === "markdown"
              ? "bg-foreground text-background"
              : "bg-muted hover:bg-muted/80"
          }`}
        >
          Markdown Source
        </button>
      </div>

      {view === "rendered" ? (
        <div className="rounded-lg border bg-white overflow-hidden">
          <iframe
            srcDoc={report.html_content}
            title="Research Report"
            className="w-full"
            style={{ height: "800px", border: "none" }}
          />
        </div>
      ) : (
        <div className="relative rounded-lg border bg-muted/30">
          <pre className="overflow-auto p-4 text-xs leading-relaxed whitespace-pre-wrap max-h-[800px]">
            {report.markdown_content}
          </pre>
        </div>
      )}
    </div>
  );
}
