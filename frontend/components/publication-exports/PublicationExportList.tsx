"use client";

import Link from "next/link";
import type { PublicationExportListItem } from "@/types/publication_export";

const FORMAT_LABELS: Record<string, string> = {
  docx: "DOCX",
  latex: "LaTeX",
  markdown: "MD",
  html: "HTML",
  json: "JSON",
};

export function PublicationExportList({
  exports,
}: {
  exports: PublicationExportListItem[];
}) {
  if (exports.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No publication exports yet.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {exports.map((ex) => (
        <Link
          key={ex.export_id}
          href={`/publication-exports/${ex.export_id}`}
          className="block rounded-lg border p-3 hover:bg-muted/40 transition-colors"
        >
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold">{ex.title}</h4>
            <span className="text-xs text-muted-foreground">
              {new Date(ex.created_at).toLocaleDateString()}
            </span>
          </div>
          <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
            <span className="capitalize">{ex.source_type}</span>
            <span>&middot;</span>
            <span>
              {ex.available_formats
                .map((f) => FORMAT_LABELS[f] || f)
                .join(", ")}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
