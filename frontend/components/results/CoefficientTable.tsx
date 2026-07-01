import type { CoefficientResult } from "@/types/modeling";

function fmt(v: number | null, decimals = 4): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(decimals);
}

function pFmt(p: number | null): string {
  if (p === null || p === undefined) return "—";
  if (p < 0.001) return "< 0.001";
  return p.toFixed(4);
}

export function CoefficientTable({ coefficients }: { coefficients: CoefficientResult[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wide text-muted">
            <th className="pb-2 pr-4">Variable</th>
            <th className="pb-2 pr-4 text-right">Coeff.</th>
            <th className="pb-2 pr-4 text-right">Std. Err.</th>
            <th className="pb-2 pr-4 text-right">t-stat</th>
            <th className="pb-2 pr-4 text-right">p-value</th>
            <th className="pb-2 pr-4 text-right">95% CI Lower</th>
            <th className="pb-2 text-right">95% CI Upper</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {coefficients.map((c) => (
            <tr key={c.variable} className="hover:bg-stone-50">
              <td className="py-2 pr-4 font-medium">
                {c.variable}
                {c.significance && (
                  <span className="ml-1 font-bold text-accent">{c.significance}</span>
                )}
              </td>
              <td className="py-2 pr-4 text-right font-mono">{fmt(c.coefficient)}</td>
              <td className="py-2 pr-4 text-right font-mono">{fmt(c.std_error)}</td>
              <td className="py-2 pr-4 text-right font-mono">{fmt(c.t_stat, 3)}</td>
              <td className="py-2 pr-4 text-right font-mono">{pFmt(c.p_value)}</td>
              <td className="py-2 pr-4 text-right font-mono">{fmt(c.ci_lower)}</td>
              <td className="py-2 text-right font-mono">{fmt(c.ci_upper)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-muted">
        Significance: <strong>***</strong> p &lt; 0.01 &nbsp; <strong>**</strong> p &lt; 0.05 &nbsp;{" "}
        <strong>*</strong> p &lt; 0.10
      </p>
    </div>
  );
}
