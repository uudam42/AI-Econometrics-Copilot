"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ApiError, uploadDataset } from "@/lib/api";
import { isDesktopMode } from "@/lib/api-base";
import type { DatasetOverview } from "@/types/dataset";

interface UploadPanelProps {
  onUploaded: (overview: DatasetOverview) => void;
}

const ACCEPTED_EXTENSIONS = [".csv", ".xlsx", ".xls"];

export function UploadPanel({ onUploaded }: UploadPanelProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [desktop, setDesktop] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setDesktop(isDesktopMode());
  }, []);

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

  async function handleNativePicker() {
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({
        multiple: false,
        filters: [
          {
            name: "Dataset",
            extensions: ["csv", "xlsx", "xls"],
          },
        ],
      });
      if (!selected || typeof selected !== "string") return;

      const { readFile } = await import("@tauri-apps/plugin-fs");
      const bytes = await readFile(selected);
      const filename = selected.replace(/\\/g, "/").split("/").pop() ?? "dataset";
      const file = new File([bytes], filename);
      await handleFile(file);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not open file picker.");
      }
    }
  }

  function handleChooseFile() {
    if (desktop) {
      void handleNativePicker();
    } else {
      inputRef.current?.click();
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
        {!desktop && (
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
        )}
        <Button
          type="button"
          disabled={isUploading}
          onClick={handleChooseFile}
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
