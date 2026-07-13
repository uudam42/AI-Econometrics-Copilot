"use client";

import { useEffect, useState } from "react";

type StartupStatus =
  | "starting"
  | "preparing_workspace"
  | "starting_engine"
  | "loading_tools"
  | "ready"
  | "failed";

interface StartupEvent {
  status: StartupStatus;
  message: string;
}

function ProgressDot({ active }: { active: boolean }) {
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full transition-colors duration-300 ${
        active ? "bg-accent" : "bg-border"
      }`}
    />
  );
}

export function DesktopStartupScreen({
  onReady,
}: {
  onReady: () => void;
}) {
  const [status, setStatus] = useState<StartupStatus>("starting");
  const [message, setMessage] = useState("Preparing local workspace…");
  const [showRetry, setShowRetry] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let unlisten: (() => void) | null = null;

    async function subscribe() {
      if (
        typeof window === "undefined" ||
        !("__TAURI_INTERNALS__" in window)
      ) {
        onReady();
        return;
      }

      try {
        // Poll current status (in case we missed early events)
        const { invoke } = await import("@tauri-apps/api/core");
        const current = await invoke<StartupEvent>("get_startup_status");
        setStatus(current.status);
        setMessage(current.message || "");
        if (current.status === "ready") {
          onReady();
          return;
        }
        if (current.status === "failed") {
          setShowRetry(true);
          return;
        }

        // Listen for future events
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<StartupEvent>("startup_status", (event) => {
          setStatus(event.payload.status);
          setMessage(event.payload.message || "");
          if (event.payload.status === "ready") {
            onReady();
          }
          if (event.payload.status === "failed") {
            setShowRetry(true);
          }
        });
      } catch {
        // Tauri not available or invoke failed — fall through to app
        onReady();
      }
    }

    subscribe();
    return () => {
      if (unlisten) unlisten();
    };
  }, [onReady]);

  const steps: { key: StartupStatus; label: string }[] = [
    { key: "preparing_workspace", label: "Preparing workspace" },
    { key: "starting_engine", label: "Starting analysis engine" },
    { key: "loading_tools", label: "Loading research tools" },
    { key: "ready", label: "Ready" },
  ];

  const order: StartupStatus[] = [
    "starting",
    "preparing_workspace",
    "starting_engine",
    "loading_tools",
    "ready",
    "failed",
  ];
  const currentIdx = order.indexOf(status);

  async function handleRetry() {
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("tauri", { cmd: "close" });
      } catch {
        window.location.reload();
      }
    } else {
      window.location.reload();
    }
  }

  async function handleOpenLogs() {
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("open_logs_folder");
      } catch {
        // ignore
      }
    }
  }

  async function handleOpenData() {
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("open_data_folder");
      } catch {
        // ignore
      }
    }
  }

  async function handleCopyTechnicalDetails() {
    let info: Record<string, unknown> = {};
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        const appInfo = await invoke<{
          app_version: string;
          database_path: string;
          exports_dir: string;
        }>("get_app_info");
        const backendInfo = await invoke<{
          base_url: string;
          port: number;
          data_dir: string;
        }>("get_backend_info");
        info = { ...appInfo, ...backendInfo };
      } catch {
        // collect what we can from the page
      }
    }

    const payload = JSON.stringify(
      {
        app: "AI Econometrics Copilot",
        desktop_mode: true,
        startup_status: status,
        error_message: message,
        timestamp: new Date().toISOString(),
        ...info,
      },
      null,
      2
    );

    try {
      await navigator.clipboard.writeText(payload);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard unavailable — no-op
    }
  }

  async function handleCloseApplication() {
    if (typeof window !== "undefined" && "__TAURI_INTERNALS__" in window) {
      try {
        const { invoke } = await import("@tauri-apps/api/core");
        await invoke("close_application");
      } catch {
        window.close();
      }
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-6">
      <div className="w-full max-w-sm space-y-8 text-center">
        <div>
          <h1 className="text-xl font-semibold">AI Econometrics Copilot</h1>
          <p className="mt-1 text-xs text-muted">Desktop Edition</p>
        </div>

        {status !== "failed" ? (
          <>
            <div className="flex justify-center gap-2">
              {steps.map((s) => (
                <ProgressDot
                  key={s.key}
                  active={order.indexOf(s.key) <= currentIdx}
                />
              ))}
            </div>
            <p className="text-sm text-muted">
              {message || "Initialising…"}
            </p>
          </>
        ) : (
          <div className="space-y-4 rounded-lg border border-red-300 bg-red-50 p-5">
            <p className="text-sm font-medium text-red-700">
              Could not start
            </p>
            <p className="text-xs text-red-600">
              {message || "The analysis engine failed to start."}
            </p>
            <div className="flex flex-col gap-2">
              <button
                onClick={handleRetry}
                className="rounded-md bg-red-600 px-4 py-2 text-xs font-medium text-white hover:bg-red-700"
              >
                Retry
              </button>
              <button
                onClick={handleOpenLogs}
                className="rounded-md border border-red-300 px-4 py-2 text-xs text-red-700 hover:bg-red-100"
              >
                Open Logs Folder
              </button>
              <button
                onClick={handleOpenData}
                className="rounded-md border border-red-300 px-4 py-2 text-xs text-red-700 hover:bg-red-100"
              >
                Open Data Folder
              </button>
              <button
                onClick={handleCopyTechnicalDetails}
                className="rounded-md border border-red-300 px-4 py-2 text-xs text-red-700 hover:bg-red-100"
              >
                {copied ? "Copied!" : "Copy Technical Details"}
              </button>
              <button
                onClick={handleCloseApplication}
                className="rounded-md border border-red-200 px-4 py-2 text-xs text-red-500 hover:bg-red-50"
              >
                Close Application
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
