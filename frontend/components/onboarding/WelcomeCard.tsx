"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { createDemoProject } from "@/lib/api";

const WORKFLOW_STEPS = [
  {
    step: 1,
    title: "Upload Dataset",
    description: "Import CSV or Excel data — panel, cross-section, or time series.",
  },
  {
    step: 2,
    title: "Profile & Plan",
    description:
      "Automatic data quality checks, structure detection, and research planning.",
  },
  {
    step: 3,
    title: "Configure Models",
    description:
      "Choose dependent/independent variables, select model type, apply transformations.",
  },
  {
    step: 4,
    title: "Run & Compare",
    description:
      "Execute regressions, view diagnostics, compare specifications side-by-side.",
  },
  {
    step: 5,
    title: "Export Results",
    description:
      "Generate reports in Markdown, HTML, DOCX, or LaTeX with publication-ready tables.",
  },
];

interface WelcomeCardProps {
  sampleDataAvailable: boolean;
}

export function WelcomeCard({ sampleDataAvailable }: WelcomeCardProps) {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStartDemo() {
    setCreating(true);
    setError(null);
    try {
      const result = await createDemoProject();
      router.push(`/projects/${result.project_id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create demo project."
      );
    } finally {
      setCreating(false);
    }
  }

  return (
    <Card>
      <CardContent className="py-8">
        <div className="text-center mb-8">
          <h2 className="text-lg font-semibold tracking-tight mb-2">
            Welcome to AI Econometrics Copilot
          </h2>
          <p className="text-sm text-muted max-w-xl mx-auto">
            An explainable, reproducible econometric analysis platform for
            economic research. Upload your data and follow the guided workflow
            below.
          </p>
        </div>

        <div className="grid gap-4 sm:grid-cols-5 mb-8">
          {WORKFLOW_STEPS.map((s) => (
            <div
              key={s.step}
              className="flex flex-col items-center text-center px-2"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full border border-border bg-surface text-xs font-semibold mb-2">
                {s.step}
              </div>
              <p className="text-xs font-medium mb-1">{s.title}</p>
              <p className="text-xs text-muted leading-snug">
                {s.description}
              </p>
            </div>
          ))}
        </div>

        <div className="flex flex-col items-center gap-3">
          <div className="flex gap-3">
            {sampleDataAvailable && (
              <Button onClick={handleStartDemo} disabled={creating}>
                {creating ? "Creating demo..." : "Try Sample Dataset"}
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => router.push("/projects/new")}
            >
              Create New Project
            </Button>
          </div>

          {error && (
            <p className="text-xs text-red-600">{error}</p>
          )}

          <p className="text-xs text-muted mt-1">
            The sample dataset uses World Bank panel data across 20 countries
            and 10 years.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
