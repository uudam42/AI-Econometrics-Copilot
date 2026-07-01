"use client";

import { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError, uploadDataset } from "@/lib/api";
import type { DatasetOverview } from "@/types/dataset";

interface UploadPanelProps {
  onUploaded: (overview: DatasetOverview) => void;
}

const ACCEPTED_EXTENSIONS = [".csv", ".xlsx", ".xls"];

export function UploadPanel({ onUploaded }: UploadPanelProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    setError(null);
    setIsUploading(true);
    try {
      const overview = await uploadDataset(file);
      onUploaded(overview);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Upload failed for an unknown reason.");
      }
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center">
      <p className="text-sm font-medium text-foreground">
        Upload a dataset to begin
      </p>
      <p className="mt-1 text-xs text-muted">
        Supported formats: {ACCEPTED_EXTENSIONS.join(", ")}
      </p>
      <div className="mt-4 flex justify-center">
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(",")}
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
        <Button
          type="button"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
        >
          {isUploading ? "Uploading..." : "Choose file"}
        </Button>
      </div>
      {error && (
        <p className="mt-3 text-xs font-medium text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
