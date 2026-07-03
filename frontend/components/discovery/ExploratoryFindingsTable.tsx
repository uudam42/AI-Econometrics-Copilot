"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ExploratoryFinding } from "@/types/discovery";
import { SUPPORT_LEVEL_LABELS, STABILITY_LABELS } from "@/types/discovery";
import { FindingScoreCard } from "./FindingScoreCard";

interface ExploratoryFindingsTableProps {
  findings: ExploratoryFinding[];
  onInvestigate?: (findingId: string) => void;
  loading?: boolean;
}

const supportVariant = (level: string) => {
  switch (level) {
    case "strong": return "success" as const;
    case "moderate": return "info" as const;
    case "weak": return "warning" as const;
    default: return "danger" as const;
  }
};

export function ExploratoryFindingsTable({
  findings,
  onInvestigate,
  loading,
}: ExploratoryFindingsTableProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (findings.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted">
          No exploratory findings were generated. All candidate relationships either
          failed estimation or did not meet minimum quality thresholds.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Exploratory Findings (Ranked)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-800">
          All findings are exploratory associations — not causal evidence. Each
          requires theory-driven validation before informing policy or conclusions.
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-left text-muted">
                <th className="pb-2 pr-3 font-medium">#</th>
                <th className="pb-2 pr-3 font-medium">Predictor → Outcome</th>
                <th className="pb-2 pr-3 font-medium">Score</th>
                <th className="pb-2 pr-3 font-medium">Support</th>
                <th className="pb-2 pr-3 font-medium">Direction</th>
                <th className="pb-2 pr-3 font-medium">Raw p</th>
                <th className="pb-2 pr-3 font-medium">Adj. q</th>
                <th className="pb-2 pr-3 font-medium">Stability</th>
                <th className="pb-2 font-medium" />
              </tr>
            </thead>
            <tbody>
              {findings.map((f, idx) => (
                <tr
                  key={f.finding_id}
                  className="cursor-pointer border-b border-stone-100 transition-colors hover:bg-stone-50"
                  onClick={() =>
                    setExpanded(expanded === f.finding_id ? null : f.finding_id)
                  }
                >
                  <td className="py-2 pr-3 text-muted">{idx + 1}</td>
                  <td className="py-2 pr-3 font-medium">
                    {f.primary_predictor} → {f.outcome_variable}
                  </td>
                  <td className="py-2 pr-3 font-mono font-semibold">
                    {f.exploratory_score}
                  </td>
                  <td className="py-2 pr-3">
                    <Badge variant={supportVariant(f.support_level)}>
                      {SUPPORT_LEVEL_LABELS[f.support_level]}
                    </Badge>
                  </td>
                  <td className="py-2 pr-3 capitalize">{f.relationship_direction}</td>
                  <td className="py-2 pr-3 font-mono">
                    {f.raw_p_value != null ? f.raw_p_value.toFixed(4) : "—"}
                  </td>
                  <td className="py-2 pr-3 font-mono">
                    {f.adjusted_q_value != null ? f.adjusted_q_value.toFixed(4) : "—"}
                  </td>
                  <td className="py-2 pr-3">
                    <Badge
                      variant={
                        f.stability_label === "stable"
                          ? "success"
                          : f.stability_label === "partially_stable"
                            ? "info"
                            : "warning"
                      }
                    >
                      {f.stability_label.replace("_", " ")}
                    </Badge>
                  </td>
                  <td className="py-2">
                    {onInvestigate && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onInvestigate(f.finding_id);
                        }}
                        disabled={loading}
                        className="whitespace-nowrap rounded bg-blue-600 px-2.5 py-1 text-[11px] font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
                      >
                        Investigate →
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {expanded && (
          <div className="mt-3">
            <FindingScoreCard
              finding={findings.find((f) => f.finding_id === expanded)!}
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
