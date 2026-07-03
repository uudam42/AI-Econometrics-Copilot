"use client";

import { useState } from "react";
import type { PublicationExportResult, ExportFormat } from "@/types/publication_export";
import { downloadPublicationExportFile } from "@/lib/api";

const FORMAT_LABELS: Record<ExportFormat, string> = {
  docx: "Word (.docx)",
  latex: "LaTeX (.tex)",
  markdown: "Markdown (.md)",
  html: "HTML",
  json: "JSON",
};

export function ExportDownloadActions({
  result,
}: {
  result: PublicationExportResult;
}) {
  const [downloading, setDownloading] = useState<string | null>(null);

  async function download(fmt: ExportFormat) {
    setDownloading(fmt);
    try {
      const blob = await downloadPublicationExportFile(result.export_id, fmt);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const ext = fmt === "markdown" ? "md" : fmt === "latex" ? "tex" : fmt;
      a.download = `export_${result.export_id}.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {result.available_formats.map((fmt) => (
        <button
          key={fmt}
          onClick={() => download(fmt)}
          disabled={downloading === fmt}
          className="rounded border px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors disabled:opacity-50"
        >
          {downloading === fmt ? "Downloading..." : `↓ ${FORMAT_LABELS[fmt]}`}
        </button>
      ))}
    </div>
  );
}
