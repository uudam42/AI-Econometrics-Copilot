"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { exportProjectJson, downloadProjectBundle } from "@/lib/api";

export function ProjectExportActions({ projectId }: { projectId: string }) {
  const [exporting, setExporting] = useState(false);

  async function handleJsonExport() {
    setExporting(true);
    try {
      const data = await exportProjectJson(projectId);
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      downloadBlob(blob, `project_${projectId.slice(0, 8)}.json`);
    } finally {
      setExporting(false);
    }
  }

  async function handleBundleDownload(includeRaw: boolean) {
    setExporting(true);
    try {
      const blob = await downloadProjectBundle(projectId, includeRaw);
      downloadBlob(
        blob,
        `project_${projectId.slice(0, 8)}${includeRaw ? "_with_data" : ""}.zip`
      );
    } finally {
      setExporting(false);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="secondary"
        onClick={handleJsonExport}
        disabled={exporting}
      >
        Export JSON
      </Button>
      <Button
        variant="secondary"
        onClick={() => handleBundleDownload(false)}
        disabled={exporting}
      >
        Download Bundle
      </Button>
      <Button
        variant="secondary"
        onClick={() => handleBundleDownload(true)}
        disabled={exporting}
      >
        Bundle + Raw Data
      </Button>
    </div>
  );
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
