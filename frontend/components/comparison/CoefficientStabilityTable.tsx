"use client";

import type { CoefficientStabilityEntry } from "@/types/comparison";

function fmt(v: number | null | undefined, dec = 4): string {
  if (v == null) return "—";
  return v.toFixed(dec);
}

const DIR_COLORS: Record<string, string> = {
  positive: "text-green-700",
  negative: "text-red-700",
  zero: "text-muted",
  unavailable: "text-muted",
};

const SIG_COLORS: Record<string, string> = {
  "***": "text-green-700 font-bold",
  "**": "text-amber-700 font-bold",
  "*": "text-amber-600",
  "": "text-muted",
};

export function CoefficientStabilityTable({
  entries,
  primaryIv,
}: {
  entries: CoefficientStabilityEntry[];
  primaryIv: string;
}) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted">
        Shows how the coefficient for <strong>{primaryIv}</strong> behaves across
        completed model specifications.
      </p>
      <p className="text-xs text-muted bg-amber-50 border border-amber-200 rounded px-2 py-1">
        Consistency across specifications may indicate stability under the tested models,
        but does not independently establish causality.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-muted/40 text-left">
              <th className="border px-3 py-2">Model</th>
              <th className="border px-3 py-2">Coefficient</th>
              <th className="border px-3 py-2">Std. Error</th>
              <th className="border px-3 py-2">p-value</th>
              <th className="border px-3 py-2">95% CI</th>
              <th className="border px-3 py-2">Sig.</th>
              <th className="border px-3 py-2">Direction</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.model_type} className="hover:bg-muted/20">
                <td className="border px-3 py-2 font-medium">{e.model_label}</td>
                <td className="border px-3 py-2 font-mono">{fmt(e.coefficient)}</td>
                <td className="border px-3 py-2 font-mono">{fmt(e.std_error)}</td>
                <td className="border px-3 py-2 font-mono">{fmt(e.p_value)}</td>
                <td className="border px-3 py-2 font-mono">
                  [{fmt(e.ci_lower)}, {fmt(e.ci_upper)}]
                </td>
                <td className={`border px-3 py-2 ${SIG_COLORS[e.significance] ?? ""}`}>
                  {e.significance || "n.s."}
                </td>
                <td className={`border px-3 py-2 ${DIR_COLORS[e.direction] ?? ""}`}>
                  {e.direction}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">
        Significance codes: *** p &lt; 0.01, ** p &lt; 0.05, * p &lt; 0.10
      </p>
    </div>
  );
}
