"use client";

import type { TransformationOperation } from "@/types/modeling";
import type { ColumnTypeInfo } from "@/types/dataset";
import { Button } from "@/components/ui/button";

interface TransformationPanelProps {
  columns: ColumnTypeInfo[];
  transformations: TransformationOperation[];
  setTransformations: (t: TransformationOperation[]) => void;
  suggestedColumns: string[]; // columns profiler recommended for log transform
}

const OPERATIONS: { op: string; label: string; needsColumns: boolean; description: string }[] = [
  { op: "drop_duplicates", label: "Drop duplicate rows", needsColumns: false, description: "Remove exact duplicate rows from the dataset." },
  { op: "drop_missing_rows", label: "Drop rows with missing values", needsColumns: true, description: "Remove rows where selected variables are missing." },
  { op: "median_imputation", label: "Median imputation", needsColumns: true, description: "Fill missing values with the column median." },
  { op: "mean_imputation", label: "Mean imputation", needsColumns: true, description: "Fill missing values with the column mean." },
  { op: "log_transform", label: "Natural log transform", needsColumns: true, description: "Apply ln(x) — requires strictly positive values. Creates log_col." },
  { op: "winsorize", label: "Winsorize", needsColumns: true, description: "Clip extreme values at percentile bounds. Creates col_wins." },
  { op: "standardize", label: "Standardize (z-score)", needsColumns: true, description: "Subtract mean, divide by std. Creates col_std." },
];

function numericColNames(columns: ColumnTypeInfo[]) {
  return columns.filter((c) => c.inferred_role === "numeric").map((c) => c.name);
}

export function TransformationPanel({
  columns,
  transformations,
  setTransformations,
  suggestedColumns,
}: TransformationPanelProps) {
  const numericCols = numericColNames(columns);

  function addTransformation(op: string) {
    const newOp: TransformationOperation = {
      operation: op as TransformationOperation["operation"],
      columns: op === "drop_duplicates" ? [] : suggestedColumns.length > 0 ? [suggestedColumns[0]] : [],
      parameters: op === "winsorize" ? { lower_quantile: 0.01, upper_quantile: 0.99 } : {},
    };
    setTransformations([...transformations, newOp]);
  }

  function removeTransformation(index: number) {
    setTransformations(transformations.filter((_, i) => i !== index));
  }

  function updateColumns(index: number, cols: string[]) {
    const updated = [...transformations];
    updated[index] = { ...updated[index], columns: cols };
    setTransformations(updated);
  }

  function updateParam(index: number, key: string, value: unknown) {
    const updated = [...transformations];
    updated[index] = {
      ...updated[index],
      parameters: { ...updated[index].parameters, [key]: value },
    };
    setTransformations(updated);
  }

  function toggleCol(index: number, col: string) {
    const current = transformations[index].columns;
    const next = current.includes(col)
      ? current.filter((c) => c !== col)
      : [...current, col];
    updateColumns(index, next);
  }

  const activeOps = new Set(transformations.map((t) => t.operation));

  return (
    <div className="space-y-4">
      {/* Add transformation buttons */}
      <div>
        <p className="mb-2 text-xs text-muted">Click to add a transformation step:</p>
        <div className="flex flex-wrap gap-2">
          {OPERATIONS.map(({ op, label }) => (
            <button
              key={op}
              type="button"
              onClick={() => addTransformation(op)}
              className="rounded border border-border bg-surface px-2.5 py-1 text-xs hover:bg-stone-50"
            >
              + {label}
            </button>
          ))}
        </div>
      </div>

      {/* Active transformations */}
      {transformations.length === 0 && (
        <p className="text-xs text-muted italic">No transformations selected. The original data will be used as-is.</p>
      )}

      {transformations.map((t, i) => {
        const meta = OPERATIONS.find((o) => o.op === t.operation);
        return (
          <div key={i} className="rounded-md border border-border bg-stone-50 p-3">
            <div className="mb-2 flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">
                  Step {i + 1}: {meta?.label ?? t.operation}
                </p>
                <p className="text-xs text-muted">{meta?.description}</p>
              </div>
              <button
                type="button"
                onClick={() => removeTransformation(i)}
                className="ml-2 text-xs text-red-500 hover:text-red-700"
              >
                Remove
              </button>
            </div>

            {meta?.needsColumns && (
              <div className="mt-2">
                <p className="mb-1 text-xs font-medium text-foreground">Apply to columns:</p>
                <div className="flex flex-wrap gap-2">
                  {numericCols.map((col) => (
                    <label key={col} className="flex cursor-pointer items-center gap-1.5">
                      <input
                        type="checkbox"
                        checked={t.columns.includes(col)}
                        onChange={() => toggleCol(i, col)}
                        className="h-3 w-3"
                      />
                      <span className="text-xs">{col}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}

            {t.operation === "winsorize" && (
              <div className="mt-2 flex gap-4">
                <label className="text-xs text-foreground">
                  Lower %{" "}
                  <input
                    type="number"
                    min={0}
                    max={0.49}
                    step={0.01}
                    value={(t.parameters.lower_quantile as number) ?? 0.01}
                    onChange={(e) => updateParam(i, "lower_quantile", parseFloat(e.target.value))}
                    className="ml-1 w-16 rounded border border-border px-1 py-0.5 text-xs"
                  />
                </label>
                <label className="text-xs text-foreground">
                  Upper %{" "}
                  <input
                    type="number"
                    min={0.51}
                    max={1}
                    step={0.01}
                    value={(t.parameters.upper_quantile as number) ?? 0.99}
                    onChange={(e) => updateParam(i, "upper_quantile", parseFloat(e.target.value))}
                    className="ml-1 w-16 rounded border border-border px-1 py-0.5 text-xs"
                  />
                </label>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
