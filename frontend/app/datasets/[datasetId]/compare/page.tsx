"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { VariableRoleSelector } from "@/components/modeling/VariableRoleSelector";
import { TransformationPanel } from "@/components/modeling/TransformationPanel";
import { ModelValidationAlert } from "@/components/modeling/ModelValidationAlert";
import { ApiError, getDatasetOverview, getDatasetProfile, runComparison } from "@/lib/api";
import type { DatasetOverview, DatasetProfileResponse } from "@/types/dataset";
import type { ModelType, TransformationOperation } from "@/types/modeling";

const ALL_MODELS: { type: ModelType; label: string; panel: boolean }[] = [
  { type: "ols", label: "OLS", panel: false },
  { type: "robust_ols", label: "Robust OLS (HC1)", panel: false },
  { type: "pooled_ols", label: "Pooled OLS", panel: true },
  { type: "fixed_effects", label: "Fixed Effects", panel: true },
  { type: "random_effects", label: "Random Effects", panel: true },
  { type: "two_way_fixed_effects", label: "Two-Way Fixed Effects", panel: true },
];

export default function ComparePage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const router = useRouter();

  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const [depVar, setDepVar] = useState("");
  const [primaryIV, setPrimaryIV] = useState("");
  const [controls, setControls] = useState<string[]>([]);
  const [entityCol, setEntityCol] = useState("");
  const [timeCol, setTimeCol] = useState("");
  const [transformations, setTransformations] = useState<TransformationOperation[]>([]);

  const [selectedModels, setSelectedModels] = useState<ModelType[]>(["ols", "robust_ols"]);
  const [clusterSE, setClusterSE] = useState(false);

  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const isPanel =
    profile?.structure.dataset_type === "panel" ||
    profile?.structure.dataset_type === "time_series";

  useEffect(() => {
    async function load() {
      try {
        const [ov, pr] = await Promise.all([
          getDatasetOverview(datasetId),
          getDatasetProfile(datasetId),
        ]);
        setOverview(ov);
        setProfile(pr);

        // Pre-fill from structure detection
        if (pr.structure.entity_column) setEntityCol(pr.structure.entity_column);
        if (pr.structure.time_column) setTimeCol(pr.structure.time_column);

        // Auto-select panel models if panel data detected
        if (pr.structure.dataset_type === "panel") {
          setSelectedModels(["ols", "pooled_ols", "fixed_effects", "random_effects"]);
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [datasetId]);

  function toggleModel(type: ModelType) {
    setSelectedModels((prev) =>
      prev.includes(type) ? prev.filter((m) => m !== type) : [...prev, type]
    );
  }

  function validate(): string[] {
    const errs: string[] = [];
    if (!depVar) errs.push("Dependent variable is required.");
    if (!primaryIV) errs.push("Primary independent variable is required.");
    const all = [depVar, primaryIV, ...controls].filter(Boolean);
    if (new Set(all).size !== all.length) errs.push("Variables must be distinct.");
    if (selectedModels.length === 0) errs.push("Select at least one candidate model.");
    const hasPanelModel = selectedModels.some((m) =>
      ["pooled_ols", "fixed_effects", "random_effects", "two_way_fixed_effects"].includes(m)
    );
    if (hasPanelModel && (!entityCol || !timeCol)) {
      errs.push("Panel models require entity and time columns to be selected.");
    }
    return errs;
  }

  async function handleRun() {
    const errs = validate();
    if (errs.length > 0) {
      setValidationErrors(errs);
      return;
    }
    setValidationErrors([]);
    setRunning(true);
    setRunError(null);
    try {
      const result = await runComparison({
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
        candidate_models: selectedModels,
        cluster_standard_errors_by_entity: clusterSE,
      });
      router.push(`/comparisons/${result.comparison_id}`);
    } catch (e) {
      setRunError(e instanceof ApiError ? e.message : "Comparison failed. Please check your configuration.");
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-muted">Loading dataset…</div>;
  }

  const columns = overview?.column_types ?? [];
  const suggestedLogColumns = profile?.quality.columns
    .filter((c) => c.suggested_transformation === "log_transform")
    .map((c) => c.column) ?? [];

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Multi-Model Comparison</h1>
        <p className="mt-1 text-sm text-muted">
          {overview?.filename} — Run multiple models on the same variables and compare results.
        </p>
      </div>

      {validationErrors.length > 0 && <ModelValidationAlert errors={validationErrors} />}

      <Card>
        <CardHeader>
          <CardTitle>Variable Roles</CardTitle>
          <CardDescription>Select the same variable roles used across all candidate models.</CardDescription>
        </CardHeader>
        <CardContent>
          <VariableRoleSelector
            columns={columns}
            isPanel={isPanel}
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
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data Transformations</CardTitle>
          <CardDescription>Applied once before all models are estimated.</CardDescription>
        </CardHeader>
        <CardContent>
          <TransformationPanel
            columns={columns}
            transformations={transformations}
            setTransformations={setTransformations}
            suggestedColumns={suggestedLogColumns}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Candidate Models</CardTitle>
          <CardDescription>
            Select which models to run. Panel models require entity and time columns.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {ALL_MODELS.map((m) => {
              const requiresPanel = m.panel && (!entityCol || !timeCol);
              return (
                <label
                  key={m.type}
                  className={`flex cursor-pointer items-center gap-2 rounded border p-2 text-sm transition-colors
                    ${selectedModels.includes(m.type) ? "border-foreground bg-muted/30" : "hover:bg-muted/20"}
                    ${requiresPanel ? "opacity-40" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(m.type)}
                    onChange={() => toggleModel(m.type)}
                    disabled={requiresPanel}
                    className="accent-foreground"
                  />
                  <span>{m.label}</span>
                </label>
              );
            })}
          </div>

          <div className="flex items-center gap-2">
            <input
              id="clusterSE"
              type="checkbox"
              checked={clusterSE}
              onChange={(e) => setClusterSE(e.target.checked)}
              className="accent-foreground"
            />
            <label htmlFor="clusterSE" className="text-sm">
              Cluster standard errors by entity (panel models only)
            </label>
          </div>
        </CardContent>
      </Card>

      {runError && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {runError}
        </div>
      )}

      <div className="flex justify-end">
        <Button onClick={handleRun} disabled={running}>
          {running ? "Running Comparison…" : `Run Comparison (${selectedModels.length} model${selectedModels.length !== 1 ? "s" : ""})`}
        </Button>
      </div>
    </div>
  );
}
