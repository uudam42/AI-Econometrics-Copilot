"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listAllDatasets, type DatasetListItem } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default function DatasetsIndexPage() {
  const { t } = useI18n();
  const [datasets, setDatasets] = useState<DatasetListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listAllDatasets()
      .then(setDatasets)
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
              {t("datasets.title")}
            </h1>
            <p className="text-xs text-muted">{t("datasets.subtitle")}</p>
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
        {!error && datasets === null && (
          <p className="text-sm text-muted">{t("common.loading")}</p>
        )}
        {datasets !== null && datasets.length === 0 && (
          <p className="text-sm text-muted">{t("datasets.empty")}</p>
        )}
        {datasets !== null && datasets.length > 0 && (
          <div className="space-y-3">
            {datasets.map((d) => (
              <div
                key={d.dataset_id}
                className="flex items-center justify-between rounded-lg border border-border bg-surface px-5 py-4"
              >
                <div>
                  <p className="text-sm font-medium">{d.filename}</p>
                  <p className="mt-0.5 text-xs text-muted">
                    {d.n_rows ?? "?"} {t("common.rows")} ·{" "}
                    {d.n_columns ?? "?"} {t("common.columns")}
                    {d.uploaded_at && (
                      <>
                        {" "}
                        · {t("common.uploaded")}{" "}
                        {new Date(d.uploaded_at).toLocaleString()}
                      </>
                    )}
                    {" · "}
                    {d.project_id ? (
                      <Link
                        href={`/projects/${d.project_id}`}
                        className="text-accent hover:underline"
                      >
                        {t("common.project")}
                      </Link>
                    ) : (
                      t("common.no_project")
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Link
                    href={`/datasets/${d.dataset_id}/model`}
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:border-accent/50 hover:text-accent"
                  >
                    {t("datasets.model")}
                  </Link>
                  <Link
                    href={`/datasets/${d.dataset_id}/plan`}
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:border-accent/50 hover:text-accent"
                  >
                    {t("datasets.plan")}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
