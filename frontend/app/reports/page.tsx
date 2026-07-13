"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAllReports, type ReportListItem } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function ReportsIndexPage() {
  const { t } = useI18n();
  const [reports, setReports] = useState<ReportListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAllReports()
      .then(setReports)
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
              {t("reports.title")}
            </h1>
            <p className="text-xs text-muted">{t("reports.subtitle")}</p>
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
        {!error && reports === null && (
          <p className="text-sm text-muted">{t("common.loading")}</p>
        )}
        {reports !== null && reports.length === 0 && (
          <p className="text-sm text-muted">{t("reports.empty")}</p>
        )}
        {reports !== null && reports.length > 0 && (
          <div className="space-y-3">
            {reports.map((r) => (
              <Link
                key={r.report_id}
                href={`/reports/${r.report_id}`}
                className="block rounded-lg border border-border bg-surface px-5 py-4 transition-colors hover:border-accent/50"
              >
                <p className="text-sm font-medium">
                  {r.title ?? r.report_id}
                </p>
                <p className="mt-0.5 text-xs text-muted">
                  {r.source_type && (
                    <>
                      {t("reports.source")}: {r.source_type}
                    </>
                  )}
                  {r.created_at && (
                    <>
                      {" · "}
                      {t("common.created")}{" "}
                      {new Date(r.created_at).toLocaleString()}
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
