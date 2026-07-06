"use client";

import type { PublicationExportResult } from "@/types/publication_export";
import { ExportDownloadActions } from "./ExportDownloadActions";

export function PublicationExportStatus({
  result,
}: {
  result: PublicationExportResult;
}) {
  return (
    <div className="space-y-4 rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold">{result.title}</h3>
          <p className="text-xs text-muted-foreground">
            {result.source_type} export &middot;{" "}
            {new Date(result.created_at).toLocaleString()}
          </p>
        </div>
        <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
          Ready
        </span>
      </div>

      {result.sections_included.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold text-muted-foreground">
            Sections
          </p>
          <div className="flex flex-wrap gap-1">
            {result.sections_included.map((s) => (
              <span
                key={s}
                className="rounded-full bg-muted px-2 py-0.5 text-xs"
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {result.figures.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-semibold text-muted-foreground">
            Figures ({result.figures.length})
          </p>
          <ul className="list-inside list-disc text-xs text-muted-foreground">
            {result.figures.map((f) => (
              <li key={f.figure_id}>{f.caption}</li>
            ))}
          </ul>
        </div>
      )}

      <ExportDownloadActions result={result} />

      <p className="text-xs italic text-muted-foreground">
        {result.disclaimer}
      </p>
    </div>
  );
}
