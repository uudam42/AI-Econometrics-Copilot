"use client";

import { useState } from "react";
import Link from "next/link";
import { uploadDatasetToProject } from "@/lib/api";
import type { DatasetSummary } from "@/types/project";

interface ProjectDatasetListProps {
  projectId: string;
  datasets: DatasetSummary[];
  onDatasetAdded: () => void;
}

export function ProjectDatasetList({
  projectId,
  datasets,
  onDatasetAdded,
}: ProjectDatasetListProps) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDatasetToProject(projectId, file);
      onDatasetAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Datasets</h3>
        <label className="cursor-pointer">
          <span className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-white px-3.5 py-2 text-sm font-medium text-foreground transition-colors hover:bg-stone-50">
            {uploading ? "Uploading..." : "Upload Dataset"}
          </span>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            className="hidden"
            onChange={handleFileChange}
            disabled={uploading}
          />
        </label>
      </div>

      {error && <p className="mb-2 text-xs text-red-600">{error}</p>}

      {datasets.length === 0 ? (
        <p className="py-4 text-center text-sm text-muted">
          No datasets uploaded yet.
        </p>
      ) : (
        <div className="space-y-2">
          {datasets.map((ds) => (
            <div
              key={ds.dataset_id}
              className="flex items-center justify-between rounded-md border border-border bg-white px-3 py-2"
            >
              <div>
                <p className="text-sm font-medium text-foreground">
                  {ds.filename}
                </p>
                <p className="text-xs text-muted">
                  {ds.n_rows.toLocaleString()} rows x {ds.n_columns} columns
                </p>
              </div>
              <Link
                href={`/datasets/${ds.dataset_id}/model`}
                className="text-xs text-accent hover:underline"
              >
                Analyze
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
