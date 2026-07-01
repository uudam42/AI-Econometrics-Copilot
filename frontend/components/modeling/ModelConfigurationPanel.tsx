"use client";

import type { ModelType } from "@/types/modeling";
import { MODEL_TYPE_LABELS, PANEL_MODELS, CROSS_SECTION_MODELS } from "@/types/modeling";

interface ModelConfigurationPanelProps {
  modelType: ModelType;
  setModelType: (m: ModelType) => void;
  robustSE: boolean;
  setRobustSE: (v: boolean) => void;
  clusterSE: boolean;
  setClusterSE: (v: boolean) => void;
  isPanel: boolean;
}

const MODEL_DESCRIPTIONS: Record<ModelType, string> = {
  ols: "Classic ordinary least squares. Assumes homoskedastic errors.",
  robust_ols: "OLS with HC1 heteroskedasticity-robust standard errors.",
  pooled_ols: "OLS applied to pooled panel data, ignoring panel structure.",
  fixed_effects: "Within estimator — absorbs time-invariant entity heterogeneity.",
  random_effects: "GLS estimator — assumes entity effects are uncorrelated with regressors.",
  two_way_fixed_effects: "Absorbs both entity and time fixed effects.",
};

export function ModelConfigurationPanel({
  modelType,
  setModelType,
  robustSE,
  setRobustSE,
  clusterSE,
  setClusterSE,
  isPanel,
}: ModelConfigurationPanelProps) {
  const available = isPanel ? PANEL_MODELS : CROSS_SECTION_MODELS;

  return (
    <div className="space-y-4">
      <div>
        <p className="mb-2 text-xs text-muted">Select the regression model to estimate:</p>
        <div className="space-y-2">
          {available.map((m) => (
            <label
              key={m}
              className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 transition-colors ${
                modelType === m
                  ? "border-accent bg-blue-50"
                  : "border-border bg-surface hover:bg-stone-50"
              }`}
            >
              <input
                type="radio"
                name="model_type"
                value={m}
                checked={modelType === m}
                onChange={() => {
                  setModelType(m);
                  if (m === "robust_ols") setRobustSE(true);
                  else setRobustSE(false);
                }}
                className="mt-0.5 h-3.5 w-3.5 accent-accent"
              />
              <div>
                <p className="text-sm font-medium text-foreground">{MODEL_TYPE_LABELS[m]}</p>
                <p className="text-xs text-muted">{MODEL_DESCRIPTIONS[m]}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div className="space-y-2 border-t border-border pt-4">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Standard Error Options</p>

        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={robustSE}
            onChange={(e) => setRobustSE(e.target.checked)}
            disabled={modelType === "robust_ols" || isPanel}
            className="h-3.5 w-3.5"
          />
          <span className="text-sm text-foreground">
            Heteroskedasticity-robust standard errors (HC1)
          </span>
        </label>

        {isPanel && (
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="checkbox"
              checked={clusterSE}
              onChange={(e) => setClusterSE(e.target.checked)}
              className="h-3.5 w-3.5"
            />
            <span className="text-sm text-foreground">
              Cluster standard errors by entity
            </span>
          </label>
        )}
      </div>
    </div>
  );
}
