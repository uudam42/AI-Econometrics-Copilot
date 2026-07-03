"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { ExploratoryFinding } from "@/types/discovery";
import { SUPPORT_LEVEL_LABELS, STABILITY_LABELS } from "@/types/discovery";
import { FindingWarnings } from "./FindingWarnings";

interface FindingScoreCardProps {
  finding: ExploratoryFinding;
}

const supportVariant = (level: string) => {
  switch (level) {
    case "strong": return "success" as const;
    case "moderate": return "info" as const;
    case "weak": return "warning" as const;
    default: return "danger" as const;
  }
};

export function FindingScoreCard({ finding }: FindingScoreCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <CardTitle className="text-base">
            {finding.primary_predictor} → {finding.outcome_variable}
          </CardTitle>
          <Badge variant={supportVariant(finding.support_level)}>
            {SUPPORT_LEVEL_LABELS[finding.support_level]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary stats */}
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-xs sm:grid-cols-4">
          <div>
            <p className="text-muted">Score</p>
            <p className="text-lg font-semibold">{finding.exploratory_score}</p>
          </div>
          <div>
            <p className="text-muted">Direction</p>
            <p className="font-medium capitalize">{finding.relationship_direction}</p>
          </div>
          <div>
            <p className="text-muted">Raw p-value</p>
            <p className="font-mono">
              {finding.raw_p_value != null ? finding.raw_p_value.toFixed(4) : "—"}
            </p>
          </div>
          <div>
            <p className="text-muted">Adjusted q-value</p>
            <p className="font-mono">
              {finding.adjusted_q_value != null ? finding.adjusted_q_value.toFixed(4) : "—"}
            </p>
          </div>
          <div>
            <p className="text-muted">Coefficient</p>
            <p className="font-mono">
              {finding.best_coefficient != null ? finding.best_coefficient.toFixed(4) : "—"}
            </p>
          </div>
          <div>
            <p className="text-muted">N observations</p>
            <p className="font-mono">{finding.best_n_obs ?? "—"}</p>
          </div>
          <div>
            <p className="text-muted">R²</p>
            <p className="font-mono">
              {finding.best_r_squared != null ? finding.best_r_squared.toFixed(4) : "—"}
            </p>
          </div>
          <div>
            <p className="text-muted">Stability</p>
            <p className="font-medium">{STABILITY_LABELS[finding.stability_label]}</p>
          </div>
        </div>

        {/* Score breakdown */}
        <div>
          <p className="mb-2 text-xs font-medium text-muted">Score Breakdown</p>
          <div className="space-y-1.5">
            {finding.score_breakdown.map((comp) => (
              <div key={comp.criterion} className="flex items-center gap-2 text-xs">
                <span className="w-48 shrink-0 text-muted">{comp.criterion}</span>
                <div className="flex-1">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-stone-100">
                    <div
                      className="h-full rounded-full bg-blue-500"
                      style={{ width: `${comp.score * 100}%` }}
                    />
                  </div>
                </div>
                <span className="w-8 text-right font-mono text-[10px]">
                  {(comp.score * comp.weight * 100).toFixed(0)}
                </span>
                <span className="w-56 text-muted">{comp.explanation}</span>
              </div>
            ))}
          </div>
        </div>

        <FindingWarnings warnings={finding.warnings} />
      </CardContent>
    </Card>
  );
}
