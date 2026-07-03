"use client";

import { useState } from "react";
import type { ReportArtifact } from "@/types/comparison";
import { getReportMarkdown } from "@/lib/api";

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function ReportExportActions({ report }: { report: ReportArtifact }) {
  const [copying, setCopying] = useState(false);

  async function copyMarkdown() {
    setCopying(true);
    try {
      await navigator.clipboard.writeText(report.markdown_content);
    } finally {
      setTimeout(() => setCopying(false), 1500);
    }
  }

  function downloadMarkdown() {
    downloadBlob(report.markdown_content, `report_${report.report_id}.md`, "text/markdown");
  }

  function downloadHtml() {
    downloadBlob(report.html_content, `report_${report.report_id}.html`, "text/html");
  }

  function downloadJson() {
    downloadBlob(JSON.stringify(report, null, 2), `report_${report.report_id}.json`, "application/json");
  }

  return (
    <div className="flex flex-wrap gap-2">
      <button
        onClick={copyMarkdown}
        className="rounded border px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors"
      >
        {copying ? "Copied!" : "Copy Markdown"}
      </button>
      <button
        onClick={downloadMarkdown}
        className="rounded border px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors"
      >
        ↓ Markdown (.md)
      </button>
      <button
        onClick={downloadHtml}
        className="rounded border px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors"
      >
        ↓ HTML
      </button>
      <button
        onClick={downloadJson}
        className="rounded border px-3 py-1.5 text-xs font-semibold hover:bg-muted transition-colors"
      >
        ↓ JSON
      </button>
    </div>
  );
}
