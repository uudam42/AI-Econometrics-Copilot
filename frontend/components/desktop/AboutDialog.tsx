"use client";

import { useEffect, useState } from "react";

interface AppInfo {
  app_version: string;
  backend_version: string;
  database_path: string;
  exports_dir: string;
  uploads_dir: string;
}

interface AboutDialogProps {
  open: boolean;
  onClose: () => void;
}

export function AboutDialog({ open, onClose }: AboutDialogProps) {
  const [info, setInfo] = useState<AppInfo | null>(null);

  useEffect(() => {
    if (!open) return;
    if (typeof window === "undefined" || !("__TAURI_INTERNALS__" in window))
      return;

    import("@tauri-apps/api/core")
      .then(({ invoke }) => invoke<AppInfo>("get_app_info"))
      .then(setInfo)
      .catch(() => {});
  }, [open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="About AI Econometrics Copilot"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="w-full max-w-md rounded-lg border border-border bg-surface p-6 shadow-xl">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-base font-semibold">AI Econometrics Copilot</h2>
            <p className="text-xs text-muted">Desktop Edition</p>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 text-muted hover:text-foreground"
            aria-label="Close"
          >
            &#x2715;
          </button>
        </div>

        <div className="mt-4 space-y-3 text-xs">
          <Row label="App Version" value={info?.app_version ?? "—"} />
          <Row label="Backend Version" value={info?.backend_version ?? "—"} />
          <Row label="Frontend Mode" value="Static (Next.js export)" />
          <Row
            label="Backend URL"
            value={
              typeof window !== "undefined" && "__TAURI_INTERNALS__" in window
                ? "http://127.0.0.1:auto"
                : "N/A"
            }
          />
          <hr className="border-border" />
          <Row
            label="Database"
            value={info?.database_path ?? "—"}
            mono
          />
          <Row
            label="Exports"
            value={info?.exports_dir ?? "—"}
            mono
          />
          <Row
            label="Uploads"
            value={info?.uploads_dir ?? "—"}
            mono
          />
          <hr className="border-border" />
          <Row label="Export Formats" value="CSV, Excel (.xlsx), PDF" />
          <p className="text-muted">
            All data is stored locally on your machine. No telemetry or network
            requests are made to external servers.
          </p>
          <p className="text-muted">
            License: MIT &nbsp;·&nbsp; github.com/uudam42/ai-econometrics-copilot
          </p>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-md bg-accent px-4 py-2 text-xs font-medium text-white hover:opacity-90"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

function Row({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex gap-2">
      <span className="w-32 shrink-0 font-medium text-foreground">{label}</span>
      <span
        className={`break-all text-muted ${mono ? "font-mono text-[10px]" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
