"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { PublicationExportStatus } from "@/components/publication-exports/PublicationExportStatus";
import { getPublicationExport } from "@/lib/api";
import type { PublicationExportResult } from "@/types/publication_export";

export default function PublicationExportDetailPage() {
  const { exportId } = useParams<{ exportId: string }>();
  const [result, setResult] = useState<PublicationExportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const r = await getPublicationExport(exportId);
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load export");
    }
  }, [exportId]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) {
    return <p className="p-8 text-sm text-red-600">{error}</p>;
  }
  if (!result) {
    return <p className="p-8 text-sm text-muted-foreground">Loading...</p>;
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-8">
      <div>
        {result.project_id && (
          <Link
            href={`/projects/${result.project_id}/exports`}
            className="text-xs text-accent hover:underline"
          >
            &larr; Back to Project Exports
          </Link>
        )}
        <h1 className="mt-2 text-2xl font-bold">{result.title}</h1>
      </div>

      <PublicationExportStatus result={result} />
    </div>
  );
}
