"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { UploadPanel } from "@/components/UploadPanel";
import { DatasetOverviewSection } from "@/components/DatasetOverviewSection";
import { DataQualitySection } from "@/components/DataQualitySection";
import { StructureSection } from "@/components/StructureSection";
import { ApiError, getDatasetProfile } from "@/lib/api";
import type { DatasetOverview, DatasetProfileResponse } from "@/types/dataset";

export default function Home() {
  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [isProfiling, setIsProfiling] = useState(false);

  async function handleUploaded(next: DatasetOverview) {
    setOverview(next);
    setProfile(null);
    setProfileError(null);
    setIsProfiling(true);
    try {
      const nextProfile = await getDatasetProfile(next.dataset_id);
      setProfile(nextProfile);
    } catch (err) {
      setProfileError(
        err instanceof ApiError || err instanceof Error
          ? err.message
          : "Failed to load the data quality profile."
      );
    } finally {
      setIsProfiling(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold tracking-tight">
              AI Econometrics Copilot
            </h1>
            <p className="text-xs text-muted">
              Explainable, reproducible econometric analysis for economic research
            </p>
          </div>
          {overview && (
            <Button variant="secondary" onClick={() => setOverview(null)}>
              New dataset
            </Button>
          )}
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 space-y-6 px-6 py-8">
        {!overview && <UploadPanel onUploaded={handleUploaded} />}

        {overview && (
          <>
            <DatasetOverviewSection overview={overview} />

            {isProfiling && (
              <p className="text-sm text-muted">Running data quality analysis…</p>
            )}
            {profileError && (
              <p className="text-sm font-medium text-red-600">{profileError}</p>
            )}
            {profile && (
              <>
                <StructureSection structure={profile.structure} />
                <DataQualitySection quality={profile.quality} />
              </>
            )}
          </>
        )}
      </main>

      <footer className="border-t border-border py-4 text-center text-xs text-muted">
        This analysis identifies statistical associations and does not establish causal
        effects unless additional identification assumptions are justified.
      </footer>
    </div>
  );
}
