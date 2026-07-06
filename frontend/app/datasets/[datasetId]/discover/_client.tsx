"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { DatasetOverview } from "@/types/dataset";
import type { DiscoveryResult } from "@/types/discovery";
import { getDatasetOverview, runDiscovery, createPlanFromFinding } from "@/lib/api";
import { DiscoveryConfigurationPanel } from "@/components/discovery/DiscoveryConfigurationPanel";
import { EligibilitySummary } from "@/components/discovery/EligibilitySummary";
import { ExploratoryFindingsTable } from "@/components/discovery/ExploratoryFindingsTable";
import { MultipleTestingPanel } from "@/components/discovery/MultipleTestingPanel";
import { StabilityPanel } from "@/components/discovery/StabilityPanel";

export default function DiscoverPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const router = useRouter();
  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [result, setResult] = useState<DiscoveryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDatasetOverview(datasetId)
      .then(setOverview)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load dataset")
      );
  }, [datasetId]);

  const handleRun = async (config: {
    mode: "guided" | "open";
    outcomeVariables: string[];
    excludedVariables: string[];
    maxOutcomes: number;
    maxPredictors: number;
    maxControls: number;
    maxSpecs: number;
    correctionMethod: "benjamini_hochberg" | "bonferroni" | "none";
    significanceLevel: number;
  }) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runDiscovery({
        dataset_id: datasetId,
        mode: config.mode,
        outcome_variables: config.outcomeVariables,
        excluded_variables: config.excludedVariables,
        maximum_outcomes: config.maxOutcomes,
        maximum_predictors_per_outcome: config.maxPredictors,
        maximum_controls_per_model: config.maxControls,
        maximum_specifications: config.maxSpecs,
        multiple_testing_method: config.correctionMethod,
        significance_level: config.significanceLevel,
        min_observations: 50,
        max_missing_rate: 0.3,
        min_unique_values: 8,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Discovery failed");
    } finally {
      setLoading(false);
    }
  };

  const handleInvestigate = async (findingId: string) => {
    if (!result) return;
    setInvestigating(true);
    try {
      const plan = await createPlanFromFinding(result.discovery_id, findingId);
      router.push(`/datasets/${datasetId}/plan?planId=${plan.plan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create plan from finding");
    } finally {
      setInvestigating(false);
    }
  };

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-6">
        <h1 className="text-lg font-bold tracking-tight text-foreground">
          Exploratory Relationship Discovery
        </h1>
        <p className="mt-1 text-sm text-muted">
          Systematically screen variables, run bounded specification searches,
          and apply multiple-testing corrections. All results are labeled as
          exploratory and require theory-driven validation.
        </p>
      </div>

      <div className="space-y-6">
        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {overview && (
          <DiscoveryConfigurationPanel
            columns={overview.column_types}
            onRun={handleRun}
            loading={loading}
          />
        )}

        {loading && (
          <div className="rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
            Running exploratory discovery — screening variables, generating
            specifications, executing models, and applying corrections...
          </div>
        )}

        {result && (
          <>
            {/* Summary banner */}
            <div className="rounded-md border border-emerald-300 bg-emerald-50 px-4 py-3">
              <p className="text-sm font-medium text-emerald-900">
                Discovery complete
              </p>
              <p className="mt-0.5 text-xs text-emerald-700">
                {result.specifications_generated} specifications generated,{" "}
                {result.specifications_completed} completed,{" "}
                {result.specifications_failed} failed.{" "}
                {result.findings.length} finding(s) ranked.
              </p>
            </div>

            <EligibilitySummary results={result.eligibility_results} />

            <ExploratoryFindingsTable
              findings={result.findings}
              onInvestigate={handleInvestigate}
              loading={investigating}
            />

            <MultipleTestingPanel
              results={result.corrected_results}
              method={result.config.multiple_testing_method}
            />

            <StabilityPanel assessments={result.stability_assessments} />

            {/* Disclaimer */}
            <div className="rounded-md border border-stone-300 bg-stone-50 px-4 py-3 text-xs text-stone-700">
              {result.disclaimer}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
