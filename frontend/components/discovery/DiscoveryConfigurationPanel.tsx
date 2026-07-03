"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ColumnTypeInfo } from "@/types/dataset";
import type { DiscoveryMode, MultipleTestingMethod } from "@/types/discovery";
import { CORRECTION_LABELS } from "@/types/discovery";

interface DiscoveryConfigurationPanelProps {
  columns: ColumnTypeInfo[];
  onRun: (config: {
    mode: DiscoveryMode;
    outcomeVariables: string[];
    excludedVariables: string[];
    maxOutcomes: number;
    maxPredictors: number;
    maxControls: number;
    maxSpecs: number;
    correctionMethod: MultipleTestingMethod;
    significanceLevel: number;
  }) => void;
  loading: boolean;
}

export function DiscoveryConfigurationPanel({
  columns,
  onRun,
  loading,
}: DiscoveryConfigurationPanelProps) {
  const [mode, setMode] = useState<DiscoveryMode>("open");
  const [selectedOutcome, setSelectedOutcome] = useState("");
  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [maxOutcomes, setMaxOutcomes] = useState(5);
  const [maxPredictors, setMaxPredictors] = useState(10);
  const [maxControls, setMaxControls] = useState(4);
  const [maxSpecs, setMaxSpecs] = useState(30);
  const [correction, setCorrection] = useState<MultipleTestingMethod>("benjamini_hochberg");
  const [alpha, setAlpha] = useState(0.05);

  const numericCols = columns.filter(
    (c) => c.inferred_role === "numeric" || c.inferred_role === "datetime"
  );

  const toggleExclude = (col: string) => {
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(col)) next.delete(col);
      else next.add(col);
      return next;
    });
  };

  const handleRun = () => {
    onRun({
      mode,
      outcomeVariables: mode === "guided" && selectedOutcome ? [selectedOutcome] : [],
      excludedVariables: Array.from(excluded),
      maxOutcomes,
      maxPredictors,
      maxControls,
      maxSpecs,
      correctionMethod: correction,
      significanceLevel: alpha,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Discovery Configuration</CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {/* Mode selection */}
        <div>
          <p className="mb-2 text-xs font-medium text-muted">Discovery Mode</p>
          <div className="flex gap-3">
            <label className="flex items-center gap-1.5 text-sm">
              <input
                type="radio"
                name="mode"
                checked={mode === "open"}
                onChange={() => setMode("open")}
                className="text-accent"
              />
              Open Discovery
            </label>
            <label className="flex items-center gap-1.5 text-sm">
              <input
                type="radio"
                name="mode"
                checked={mode === "guided"}
                onChange={() => setMode("guided")}
                className="text-accent"
              />
              Guided Discovery
            </label>
          </div>
          <p className="mt-1 text-[11px] text-muted">
            {mode === "open"
              ? "The system selects candidate outcome variables automatically. More exploratory, higher false-positive risk."
              : "You specify the outcome variable. The system explores candidate predictors."}
          </p>
        </div>

        {/* Guided: outcome selection */}
        {mode === "guided" && (
          <div>
            <label className="mb-1.5 block text-xs font-medium text-muted">
              Outcome Variable
            </label>
            <select
              value={selectedOutcome}
              onChange={(e) => setSelectedOutcome(e.target.value)}
              className="w-full rounded border border-border bg-white px-3 py-2 text-sm"
            >
              <option value="">Select...</option>
              {numericCols.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Excluded variables */}
        <div>
          <p className="mb-1.5 text-xs font-medium text-muted">
            Excluded Variables
          </p>
          <div className="flex flex-wrap gap-2">
            {columns.map((c) => (
              <label
                key={c.name}
                className={`inline-flex items-center gap-1 rounded border px-2 py-1 text-xs transition-colors ${
                  excluded.has(c.name)
                    ? "border-red-300 bg-red-50 text-red-700"
                    : "border-border bg-white text-foreground"
                }`}
              >
                <input
                  type="checkbox"
                  checked={excluded.has(c.name)}
                  onChange={() => toggleExclude(c.name)}
                  className="h-3 w-3"
                />
                {c.name}
              </label>
            ))}
          </div>
        </div>

        {/* Limits */}
        <div className="grid grid-cols-2 gap-4">
          {mode === "open" && (
            <div>
              <label className="mb-1 block text-xs text-muted">Max Outcomes</label>
              <input type="number" min={1} max={10} value={maxOutcomes}
                onChange={(e) => setMaxOutcomes(Number(e.target.value))}
                className="w-full rounded border border-border px-2 py-1.5 text-sm" />
            </div>
          )}
          <div>
            <label className="mb-1 block text-xs text-muted">Max Predictors/Outcome</label>
            <input type="number" min={1} max={20} value={maxPredictors}
              onChange={(e) => setMaxPredictors(Number(e.target.value))}
              className="w-full rounded border border-border px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Max Controls/Model</label>
            <input type="number" min={0} max={8} value={maxControls}
              onChange={(e) => setMaxControls(Number(e.target.value))}
              className="w-full rounded border border-border px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted">Max Specifications</label>
            <input type="number" min={1} max={100} value={maxSpecs}
              onChange={(e) => setMaxSpecs(Number(e.target.value))}
              className="w-full rounded border border-border px-2 py-1.5 text-sm" />
          </div>
        </div>

        {/* Correction method */}
        <div>
          <label className="mb-1.5 block text-xs font-medium text-muted">
            Multiple-Testing Correction
          </label>
          <select
            value={correction}
            onChange={(e) => setCorrection(e.target.value as MultipleTestingMethod)}
            className="w-full rounded border border-border bg-white px-3 py-2 text-sm"
          >
            {(Object.entries(CORRECTION_LABELS) as [MultipleTestingMethod, string][]).map(
              ([key, label]) => (
                <option key={key} value={key}>{label}</option>
              )
            )}
          </select>
          {correction === "none" && (
            <p className="mt-1 text-[11px] text-red-600">
              No correction applied. Results are highly susceptible to false positives.
            </p>
          )}
        </div>

        {/* Significance */}
        <div>
          <label className="mb-1 block text-xs text-muted">Significance Level</label>
          <select
            value={alpha}
            onChange={(e) => setAlpha(Number(e.target.value))}
            className="w-full rounded border border-border bg-white px-3 py-2 text-sm"
          >
            <option value={0.01}>0.01</option>
            <option value={0.05}>0.05</option>
            <option value={0.10}>0.10</option>
          </select>
        </div>

        {/* Warning */}
        <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3 text-xs text-amber-900">
          Exploratory results are generated from multiple tested specifications.
          They should be treated as hypothesis-generating and require theory-driven
          validation, pre-specified analysis, or independent-sample confirmation.
        </div>

        <Button
          onClick={handleRun}
          disabled={loading || (mode === "guided" && !selectedOutcome)}
          className="w-full"
        >
          {loading ? "Running Discovery..." : "Run Exploratory Discovery"}
        </Button>
      </CardContent>
    </Card>
  );
}
