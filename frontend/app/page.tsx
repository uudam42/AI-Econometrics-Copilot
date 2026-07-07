"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ApiError, createDemoProject, getOnboardingStatus } from "@/lib/api";
import type { OnboardingStatus } from "@/types/onboarding";

function ActionCard({
  icon,
  title,
  description,
  href,
  onClick,
  primary,
}: {
  icon: string;
  title: string;
  description: string;
  href?: string;
  onClick?: () => void;
  primary?: boolean;
}) {
  const inner = (
    <div
      className={`group flex h-full cursor-pointer flex-col rounded-xl border p-6 transition-all hover:shadow-md ${
        primary
          ? "border-accent bg-accent/5 hover:bg-accent/10"
          : "border-border bg-surface hover:border-accent/50"
      }`}
    >
      <span className="mb-3 text-3xl">{icon}</span>
      <h3 className="mb-1 text-sm font-semibold">{title}</h3>
      <p className="text-xs text-muted">{description}</p>
    </div>
  );

  if (href) {
    return <Link href={href} className="block h-full">{inner}</Link>;
  }
  return (
    <button type="button" onClick={onClick} className="block h-full w-full text-left">
      {inner}
    </button>
  );
}

export default function Home() {
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [creatingDemo, setCreatingDemo] = useState(false);
  const [demoError, setDemoError] = useState<string | null>(null);

  useEffect(() => {
    getOnboardingStatus()
      .then(setOnboarding)
      .catch(() =>
        setOnboarding({ has_projects: false, has_demo: false, sample_data_available: false })
      );
  }, []);

  async function handleDemo() {
    setCreatingDemo(true);
    setDemoError(null);
    try {
      const resp = await createDemoProject();
      window.location.href = `/projects/${resp.project_id}`;
    } catch (err) {
      setDemoError(
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Could not create demo project."
      );
      setCreatingDemo(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              AI Econometrics Copilot
            </h1>
            <p className="text-xs text-muted">
              Explainable, reproducible econometric analysis
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/projects">
              <Button variant="ghost">My Projects</Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-12">
        {/* Hero */}
        <div className="mb-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight">
            What would you like to do?
          </h2>
          <p className="mt-2 text-sm text-muted">
            Choose a path below — you can always switch to the full Research Workspace later.
          </p>
        </div>

        {/* 3 large action cards */}
        <div className="mb-10 grid gap-4 sm:grid-cols-3">
          <ActionCard
            icon="📊"
            title="Analyse My Excel / CSV"
            description="Upload your file, answer one question, and get a plain-language result in under a minute."
            href="/quick-analyze"
            primary
          />
          <ActionCard
            icon="🎓"
            title="Try a Demo Dataset"
            description={
              onboarding?.sample_data_available
                ? "Load a sample World Bank panel dataset and explore the full workflow."
                : "Demo data not available on this installation."
            }
            onClick={onboarding?.sample_data_available ? handleDemo : undefined}
          />
          <ActionCard
            icon="📁"
            title="Open Previous Project"
            description="Return to a project you have already started and continue your research."
            href="/projects"
          />
        </div>

        {demoError && (
          <p className="mb-6 rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
            {demoError}
          </p>
        )}
        {creatingDemo && (
          <p className="mb-6 text-sm text-muted">Creating demo project…</p>
        )}

        {/* Advanced workflow divider */}
        <div className="relative mb-8">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center">
            <span className="bg-background px-3 text-xs text-muted">
              Advanced workflow
            </span>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { href: "/datasets", label: "📂 All Datasets" },
            { href: "/projects", label: "🗂 All Projects" },
            { href: "/reports", label: "📄 Reports" },
            { href: "/analyses", label: "🔬 Analyses" },
          ].map(({ href, label }) => (
            <Link key={href} href={href}>
              <div className="rounded-lg border border-border bg-surface px-4 py-3 text-center text-xs font-medium transition-colors hover:border-accent/50 hover:text-accent">
                {label}
              </div>
            </Link>
          ))}
        </div>
      </main>

      <footer className="border-t border-border py-4 text-center text-xs text-muted">
        Statistical associations only — not causal effects unless additional
        identification assumptions are justified.
      </footer>
    </div>
  );
}
