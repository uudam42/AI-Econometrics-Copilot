"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { VariableRoleSelector } from "@/components/modeling/VariableRoleSelector";
import { TransformationPanel } from "@/components/modeling/TransformationPanel";
import { ModelConfigurationPanel } from "@/components/modeling/ModelConfigurationPanel";
import { ModelValidationAlert } from "@/components/modeling/ModelValidationAlert";
import {
  ApiError,
  getDatasetOverview,
  getDatasetProfile,
  runAnalysis,
} from "@/lib/api";
import type { DatasetOverview, DatasetProfileResponse, ColumnTypeInfo } from "@/types/dataset";
import type { ModelType, TransformationOperation } from "@/types/modeling";

export default function ModelPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const router = useRouter();

  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Variable selection state
  const [depVar, setDepVar] = useState("");
  const [primaryIV, setPrimaryIV] = useState("");
  const [controls, setControls] = useState<string[]>([]);
  const [entityCol, setEntityCol] = useState("");
  const [timeCol, setTimeCol] = useState("");

  // Transformation state
  const [transformations, setTransformations] = useState<TransformationOperation[]>([]);

  // Model config state
  const [modelType, setModelType] = useState<ModelType>("ols");
  const [robustSE, setRobustSE] = useState(false);
  const [clusterSE, setClusterSE] = useState(false);

  // Run state
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const isPanel =
    profile?.structure.dataset_type === "panel" ||
    profile?.structure.dataset_type === "time_series";

  useEffect(() => {
    async function load() {
      try {
        const [ov, prof] = await Promise.all([
          getDatasetOverview(datasetId),
          getDatasetProfile(datasetId),
        ]);
        setOverview(ov);
        setProfile(prof);

        // Pre-fill from profile recommendations
        const structure = prof.structure;
        if (structure.entity_column) setEntityCol(structure.entity_column);
        if (structure.time_column) setTimeCol(structure.time_column);

        // Auto-select dependent variable from "Potential Outcome" hints
        const potentialOutcome = ov.column_types.find((c) =>
          c.role_hints.includes("Potential Outcome")
        );
        if (potentialOutcome) setDepVar(potentialOutcome.name);

        // Auto-select primary IV from "Potential Explanatory Variable"
        const potentialIV = ov.column_types.find(
          (c) =>
            c.role_hints.includes("Potential Explanatory Variable") &&
            c.name !== potentialOutcome?.name
        );
        if (potentialIV) setPrimaryIV(potentialIV.name);

        // Default to panel model if panel detected
        if (structure.dataset_type === "panel") {
          setModelType("fixed_effects");
        }
      } catch (e) {
        setError(
          e instanceof ApiError || e instanceof Error
            ? e.message
            : "Failed to load dataset."
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [datasetId]);

  function validate(): string[] {
    const errors: string[] = [];
    if (!depVar) errors.push("Dependent variable is required.");
    if (!primaryIV) errors.push("Primary independent variable is required.");
    if (depVar && primaryIV && depVar === primaryIV) {
      errors.push("Dependent variable and primary independent variable must be different.");
    }
    if (controls.includes(depVar)) {
      errors.push("Dependent variable cannot also be a control variable.");
    }
    if (controls.includes(primaryIV)) {
      errors.push("Primary independent variable cannot also be a control variable.");
    }
    if (
      ["pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"].includes(
        modelType
      )
    ) {
      if (!entityCol) errors.push("Entity column is required for panel models.");
      if (!timeCol) errors.push("Time column is required for panel models.");
    }
    return errors;
  }

  async function handleRun() {
    const errors = validate();
    if (errors.length > 0) return;

    setRunning(true);
    setRunError(null);

    try {
      const result = await runAnalysis({
        dataset_id: datasetId,
        variable_selection: {
          dataset_id: datasetId,
          dependent_variable: depVar,
          primary_independent_variable: primaryIV,
          control_variables: controls,
          entity_column: entityCol || null,
          time_column: timeCol || null,
        },
        transformations,
        model_type: modelType,
        include_intercept: true,
        robust_standard_errors: robustSE,
        cluster_standard_errors_by_entity: clusterSE,
      });
      router.push(`/analyses/${result.analysis_id}`);
    } catch (e) {
      setRunError(
        e instanceof ApiError || e instanceof Error
          ? e.message
          : "Analysis failed."
      );
      setRunning(false);
    }
  }

  const validationErrors = validate();
  const suggestedLogCols =
    profile?.quality.columns
      .filter((c) => c.suggested_transformation === "log")
      .map((c) => c.column) ?? [];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-sm text-muted">Loading dataset…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12">
        <p className="text-sm text-red-600">{error}</p>
        <Button variant="secondary" className="mt-4" onClick={() => router.push("/")}>
          Back to upload
        </Button>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-base font-semibold">Configure Analysis</h1>
            <p className="text-xs text-muted">{overview?.filename}</p>
          </div>
          <Button variant="secondary" onClick={() => router.push("/")}>
            ← Back
          </Button>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 space-y-6 px-6 py-8">
        {/* Dataset summary chip */}
        <div className="flex flex-wrap gap-3 text-xs text-muted">
          <span className="rounded border border-border bg-surface px-2.5 py-1">
            {overview?.n_rows} rows × {overview?.n_columns} columns
          </span>
          {profile && (
            <span className="rounded border border-border bg-surface px-2.5 py-1">
              {profile.structure.dataset_type.replace("_", " ")}
              {profile.structure.entity_count
                ? ` · ${profile.structure.entity_count} entities`
                : ""}
              {profile.structure.time_period_count
                ? ` · ${profile.structure.time_period_count} periods`
                : ""}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
          {/* Left column */}
          <div className="space-y-6">
            {/* Variable selection */}
            <Card>
              <CardHeader>
                <CardTitle>Variable Roles</CardTitle>
                <CardDescription>
                  Assign columns to regression roles. Suggestions are pre-filled from
                  the data profiler but you can override any selection.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {overview && (
                  <VariableRoleSelector
                    columns={overview.column_types}
                    depVar={depVar}
                    setDepVar={setDepVar}
                    primaryIV={primaryIV}
                    setPrimaryIV={setPrimaryIV}
                    controls={controls}
                    setControls={setControls}
                    entityCol={entityCol}
                    setEntityCol={setEntityCol}
                    timeCol={timeCol}
                    setTimeCol={setTimeCol}
                    isPanel={isPanel ?? false}
                  />
                )}
              </CardContent>
            </Card>

            {/* Transformations */}
            <Card>
              <CardHeader>
                <CardTitle>Data Transformations</CardTitle>
                <CardDescription>
                  Optional. Applied to a fresh copy of the data before estimation.
                  The original dataset is never modified.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {overview && (
                  <TransformationPanel
                    columns={overview.column_types}
                    transformations={transformations}
                    setTransformations={setTransformations}
                    suggestedColumns={suggestedLogCols}
                  />
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right column — sticky panel */}
          <div className="space-y-4">
            <Card className="lg:sticky lg:top-6">
              <CardHeader>
                <CardTitle>Model Configuration</CardTitle>
                <CardDescription>
                  {isPanel
                    ? "Panel data detected — panel models are available."
                    : "Cross-sectional or time-series data."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ModelConfigurationPanel
                  modelType={modelType}
                  setModelType={setModelType}
                  robustSE={robustSE}
                  setRobustSE={setRobustSE}
                  clusterSE={clusterSE}
                  setClusterSE={setClusterSE}
                  isPanel={isPanel ?? false}
                />
              </CardContent>
            </Card>

            {/* Run panel */}
            <Card>
              <CardContent className="pt-4">
                <ModelValidationAlert errors={validationErrors} />
                {runError && (
                  <div className="mb-3 mt-2 rounded border border-red-200 bg-red-50 p-3 text-xs text-red-700">
                    <strong>Error:</strong> {runError}
                  </div>
                )}
                <Button
                  className="mt-3 w-full"
                  onClick={handleRun}
                  disabled={running || validationErrors.length > 0}
                >
                  {running ? "Running analysis…" : "Run Analysis →"}
                </Button>
                <p className="mt-2 text-center text-xs text-muted">
                  All calculations performed by Python statistical libraries.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-3 text-center text-xs text-muted">
        This analysis identifies statistical associations and does not establish causal
        effects unless additional identification assumptions are justified.
      </footer>
    </div>
  );
}
