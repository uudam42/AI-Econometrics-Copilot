import type { ModelDiagnosticsResponse, VIFResult } from "@/types/modeling";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function fmt(v: number | null, d = 4): string {
  if (v === null || v === undefined) return "—";
  return v.toFixed(d);
}

function RiskBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    low: "bg-green-50 text-green-700",
    moderate: "bg-amber-50 text-amber-700",
    severe: "bg-red-50 text-red-700",
    unknown: "bg-stone-50 text-stone-500",
  };
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${styles[level] ?? styles.unknown}`}>
      {level}
    </span>
  );
}

function DiagCard({
  name,
  statistic,
  pValue,
  interpretation,
  available,
  unavailableReason,
}: {
  name: string;
  statistic: number | null;
  pValue: number | null;
  interpretation: string;
  available: boolean;
  unavailableReason?: string | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{name}</CardTitle>
      </CardHeader>
      <CardContent>
        {!available ? (
          <p className="text-xs text-muted italic">{unavailableReason ?? "Not available."}</p>
        ) : (
          <>
            <div className="mb-2 flex gap-6 text-sm">
              {statistic !== null && (
                <span>
                  Statistic: <strong className="font-mono">{fmt(statistic, 3)}</strong>
                </span>
              )}
              {pValue !== null && (
                <span>
                  p-value: <strong className="font-mono">{pValue < 0.001 ? "< 0.001" : fmt(pValue)}</strong>
                </span>
              )}
            </div>
            <p className="text-xs text-foreground">{interpretation}</p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export function DiagnosticsPanel({ diagnostics }: { diagnostics: ModelDiagnosticsResponse }) {
  return (
    <div className="space-y-6">
      {/* Descriptive statistics */}
      <div>
        <h4 className="mb-2 text-sm font-semibold">Descriptive Statistics</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border text-left font-semibold uppercase tracking-wide text-muted">
                <th className="pb-1 pr-3">Variable</th>
                <th className="pb-1 pr-3 text-right">N</th>
                <th className="pb-1 pr-3 text-right">Mean</th>
                <th className="pb-1 pr-3 text-right">Std</th>
                <th className="pb-1 pr-3 text-right">Min</th>
                <th className="pb-1 pr-3 text-right">Median</th>
                <th className="pb-1 pr-3 text-right">Max</th>
                <th className="pb-1 pr-3 text-right">Missing</th>
                <th className="pb-1 text-right">Skewness</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {diagnostics.descriptive_stats.map((s) => (
                <tr key={s.variable} className="hover:bg-stone-50">
                  <td className="py-1 pr-3 font-medium">{s.variable}</td>
                  <td className="py-1 pr-3 text-right font-mono">{s.count}</td>
                  <td className="py-1 pr-3 text-right font-mono">{fmt(s.mean, 3)}</td>
                  <td className="py-1 pr-3 text-right font-mono">{fmt(s.std, 3)}</td>
                  <td className="py-1 pr-3 text-right font-mono">{fmt(s.min, 3)}</td>
                  <td className="py-1 pr-3 text-right font-mono">{fmt(s.median, 3)}</td>
                  <td className="py-1 pr-3 text-right font-mono">{fmt(s.max, 3)}</td>
                  <td className="py-1 pr-3 text-right font-mono">{s.missing_count}</td>
                  <td className="py-1 text-right font-mono">{fmt(s.skewness, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* VIF */}
      {diagnostics.vif.length > 0 && (
        <div>
          <h4 className="mb-2 text-sm font-semibold">Variance Inflation Factors (VIF)</h4>
          <div className="space-y-1.5">
            {diagnostics.vif.map((v) => (
              <div key={v.variable} className="flex items-center gap-3 rounded border border-border px-3 py-2 text-sm">
                <span className="w-40 truncate font-medium">{v.variable}</span>
                <span className="font-mono">{v.vif >= 0 ? v.vif.toFixed(2) : "—"}</span>
                <RiskBadge level={v.risk_level} />
                <span className="text-xs text-muted">{v.interpretation}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistical tests */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <DiagCard
          name={diagnostics.breusch_pagan.name}
          statistic={diagnostics.breusch_pagan.statistic}
          pValue={diagnostics.breusch_pagan.p_value}
          interpretation={diagnostics.breusch_pagan.interpretation}
          available={diagnostics.breusch_pagan.available}
          unavailableReason={diagnostics.breusch_pagan.unavailable_reason}
        />
        <DiagCard
          name={diagnostics.jarque_bera.name}
          statistic={diagnostics.jarque_bera.statistic}
          pValue={diagnostics.jarque_bera.p_value}
          interpretation={diagnostics.jarque_bera.interpretation}
          available={diagnostics.jarque_bera.available}
          unavailableReason={diagnostics.jarque_bera.unavailable_reason}
        />
        <DiagCard
          name={diagnostics.durbin_watson.name}
          statistic={diagnostics.durbin_watson.statistic}
          pValue={null}
          interpretation={diagnostics.durbin_watson.interpretation}
          available={diagnostics.durbin_watson.available}
          unavailableReason={diagnostics.durbin_watson.unavailable_reason}
        />
        <Card>
          <CardHeader>
            <CardTitle>Hausman Test (FE vs RE)</CardTitle>
          </CardHeader>
          <CardContent>
            {!diagnostics.hausman.available ? (
              <p className="text-xs text-muted italic">
                {diagnostics.hausman.unavailable_reason ?? "Not available."}
              </p>
            ) : (
              <>
                <div className="mb-2 flex gap-6 text-sm">
                  <span>χ² = <strong className="font-mono">{fmt(diagnostics.hausman.statistic, 3)}</strong></span>
                  <span>df = <strong className="font-mono">{diagnostics.hausman.degrees_of_freedom}</strong></span>
                  <span>p = <strong className="font-mono">{diagnostics.hausman.p_value !== null && diagnostics.hausman.p_value < 0.001 ? "< 0.001" : fmt(diagnostics.hausman.p_value)}</strong></span>
                </div>
                <p className="text-xs text-foreground">{diagnostics.hausman.recommendation}</p>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
