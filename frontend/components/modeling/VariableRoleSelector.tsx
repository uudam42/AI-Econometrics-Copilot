"use client";

import { Select } from "@/components/ui/select";
import { VariableRecommendationBadge } from "@/components/modeling/VariableRecommendationBadge";
import type { ColumnTypeInfo } from "@/types/dataset";

interface VariableRoleSelectorProps {
  columns: ColumnTypeInfo[];
  depVar: string;
  setDepVar: (v: string) => void;
  primaryIV: string;
  setPrimaryIV: (v: string) => void;
  controls: string[];
  setControls: (v: string[]) => void;
  entityCol: string;
  setEntityCol: (v: string) => void;
  timeCol: string;
  setTimeCol: (v: string) => void;
  isPanel: boolean;
}

function numericColumns(columns: ColumnTypeInfo[]) {
  return columns.filter((c) => c.inferred_role === "numeric");
}

function identifierColumns(columns: ColumnTypeInfo[]) {
  return columns.filter((c) =>
    c.role_hints.some((h) => h.includes("Entity") || h.includes("Time") || c.inferred_role === "categorical" || c.inferred_role === "identifier")
  );
}

export function VariableRoleSelector({
  columns,
  depVar,
  setDepVar,
  primaryIV,
  setPrimaryIV,
  controls,
  setControls,
  entityCol,
  setEntityCol,
  timeCol,
  setTimeCol,
  isPanel,
}: VariableRoleSelectorProps) {
  const numeric = numericColumns(columns);
  const allCols = columns;

  const availableForPrimaryIV = numeric.filter((c) => c.name !== depVar);
  const availableForControls = numeric.filter(
    (c) => c.name !== depVar && c.name !== primaryIV
  );

  function toggleControl(name: string) {
    setControls(
      controls.includes(name)
        ? controls.filter((c) => c !== name)
        : [...controls, name]
    );
  }

  return (
    <div className="space-y-5">
      {/* Dependent variable */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-foreground">
          Dependent Variable <span className="text-red-500">*</span>
        </label>
        <p className="mb-2 text-xs text-muted">The outcome you want to explain (must be numeric).</p>
        <Select value={depVar} onChange={(e) => setDepVar(e.target.value)}>
          <option value="">— select —</option>
          {numeric.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </Select>
        {depVar && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {columns
              .find((c) => c.name === depVar)
              ?.role_hints.map((h) => (
                <VariableRecommendationBadge key={h} hint={h} />
              ))}
          </div>
        )}
      </div>

      {/* Primary independent variable */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-foreground">
          Primary Independent Variable <span className="text-red-500">*</span>
        </label>
        <p className="mb-2 text-xs text-muted">The main explanatory variable of interest.</p>
        <Select
          value={primaryIV}
          onChange={(e) => setPrimaryIV(e.target.value)}
          disabled={!depVar}
        >
          <option value="">— select —</option>
          {availableForPrimaryIV.map((c) => (
            <option key={c.name} value={c.name}>
              {c.name}
            </option>
          ))}
        </Select>
        {primaryIV && (
          <div className="mt-1.5 flex flex-wrap gap-1">
            {columns
              .find((c) => c.name === primaryIV)
              ?.role_hints.map((h) => (
                <VariableRecommendationBadge key={h} hint={h} />
              ))}
          </div>
        )}
      </div>

      {/* Control variables */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-foreground">
          Control Variables
        </label>
        <p className="mb-2 text-xs text-muted">
          Additional covariates to include. Check all that apply.
        </p>
        <div className="max-h-40 overflow-y-auto rounded-md border border-border bg-surface p-2">
          {availableForControls.length === 0 ? (
            <p className="py-2 text-center text-xs text-muted">No additional numeric columns available.</p>
          ) : (
            availableForControls.map((c) => (
              <label key={c.name} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1 hover:bg-stone-50">
                <input
                  type="checkbox"
                  checked={controls.includes(c.name)}
                  onChange={() => toggleControl(c.name)}
                  className="h-3.5 w-3.5 rounded border-border text-accent"
                />
                <span className="text-sm">{c.name}</span>
                <div className="ml-auto flex gap-1">
                  {c.role_hints.slice(0, 1).map((h) => (
                    <VariableRecommendationBadge key={h} hint={h} />
                  ))}
                </div>
              </label>
            ))
          )}
        </div>
        {controls.length > 0 && (
          <p className="mt-1 text-xs text-muted">
            Selected: {controls.join(", ")}
          </p>
        )}
      </div>

      {/* Panel structure columns */}
      {isPanel && (
        <div className="rounded-md border border-purple-200 bg-purple-50 p-4">
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-purple-700">
            Panel Structure
          </p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Entity Column <span className="text-red-500">*</span>
              </label>
              <Select value={entityCol} onChange={(e) => setEntityCol(e.target.value)}>
                <option value="">— select —</option>
                {allCols.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-foreground">
                Time Column <span className="text-red-500">*</span>
              </label>
              <Select value={timeCol} onChange={(e) => setTimeCol(e.target.value)}>
                <option value="">— select —</option>
                {allCols.map((c) => (
                  <option key={c.name} value={c.name}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
