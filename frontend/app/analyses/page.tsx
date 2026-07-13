"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAllAnalyses, type AnalysisListItem } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function AnalysesIndexPage() {
  const { t } = useI18n();
  const [analyses, setAnalyses] = useState<AnalysisListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAllAnalyses()
      .then(setAnalyses)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load")
      );
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              {t("analyses.title")}
            </h1>
            <p className="text-xs text-muted">{t("analyses.subtitle")}</p>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <Link
              href="/"
              className="text-xs font-medium text-muted hover:text-accent"
            >
              {t("common.back_home")}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        {error && (
          <p className="rounded border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </p>
        )}
        {!error && analyses === null && (
          <p className="text-sm text-muted">{t("common.loading")}</p>
        )}
        {analyses !== null && analyses.length === 0 && (
          <p className="text-sm text-muted">{t("analyses.empty")}</p>
        )}
        {analyses !== null && analyses.length > 0 && (
          <div className="space-y-3">
            {analyses.map((a) => (
              <Link
                key={a.analysis_id}
                href={`/analyses/${a.analysis_id}`}
                className="block rounded-lg border border-border bg-surface px-5 py-4 transition-colors hover:border-accent/50"
              >
                <p className="text-sm font-medium">
                  {a.dataset_filename ?? a.dataset_id}
                </p>
                <p className="mt-0.5 text-xs text-muted">
                  {a.model_type && (
                    <>
                      {t("analyses.model_type")}:{" "}
                      <span className="font-mono">{a.model_type}</span>
                    </>
                  )}
                  {a.dependent_variable && (
                    <>
                      {" · "}
                      {t("analyses.dependent")}:{" "}
                      <span className="font-mono">{a.dependent_variable}</span>
                    </>
                  )}
                  {typeof a.r_squared === "number" && (
                    <> · R² = {a.r_squared.toFixed(3)}</>
                  )}
                  {a.created_at && (
                    <>
                      {" · "}
                      {t("common.created")}{" "}
                      {new Date(a.created_at).toLocaleString()}
                    </>
                  )}
                </p>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
