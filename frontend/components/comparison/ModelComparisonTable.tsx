"use client";

import type { ModelComparisonEntry } from "@/types/comparison";

const STATUS_COLORS: Record<string, string> = {
  completed: "text-green-700 bg-green-50 border-green-200",
  failed: "text-red-700 bg-red-50 border-red-200",
  unavailable: "text-amber-700 bg-amber-50 border-amber-200",
};

function fmt(v: number | null | undefined, decimals = 3): string {
  if (v == null) return "—";
  return v.toFixed(decimals);
}

export function ModelComparisonTable({ models }: { models: ModelComparisonEntry[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-muted/40 text-left">
            <th className="border px-3 py-2">Model</th>
            <th className="border px-3 py-2">Status</th>
            <th className="border px-3 py-2">N</th>
            <th className="border px-3 py-2">R²</th>
            <th className="border px-3 py-2">Adj. R²</th>
            <th className="border px-3 py-2">AIC</th>
            <th className="border px-3 py-2">BIC</th>
            <th className="border px-3 py-2">Max VIF</th>
            <th className="border px-3 py-2">Hetero.</th>
            <th className="border px-3 py-2">SE Type</th>
          </tr>
        </thead>
        <tbody>
          {models.map((m) => {
            const fm = m.fit_metrics;
            const dm = m.diagnostic_summary;
            const badge = STATUS_COLORS[m.status] ?? "";
            return (
              <tr key={m.model_type} className="hover:bg-muted/20">
                <td className="border px-3 py-2 font-medium">{m.model_label}</td>
                <td className="border px-3 py-2">
                  <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${badge}`}>
                    {m.status}
                  </span>
                  {m.reason && m.status !== "completed" && (
                    <p className="mt-1 text-muted" title={m.reason}>
                      {m.reason.slice(0, 80)}{m.reason.length > 80 ? "…" : ""}
                    </p>
                  )}
                </td>
                <td className="border px-3 py-2">{fm?.n_obs ?? "—"}</td>
                <td className="border px-3 py-2">{fmt(fm?.r_squared)}</td>
                <td className="border px-3 py-2">{fmt(fm?.adj_r_squared)}</td>
                <td className="border px-3 py-2">{fmt(fm?.aic, 1)}</td>
                <td className="border px-3 py-2">{fmt(fm?.bic, 1)}</td>
                <td className="border px-3 py-2">{fmt(dm?.max_vif, 1)}</td>
                <td className="border px-3 py-2">
                  {dm?.heteroskedasticity_detected == null
                    ? "—"
                    : dm.heteroskedasticity_detected
                    ? "Yes"
                    : "No"}
                </td>
                <td className="border px-3 py-2">{m.standard_error_type ?? "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
