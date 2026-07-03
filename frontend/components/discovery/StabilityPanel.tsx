"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { StabilityAssessment } from "@/types/discovery";
import { STABILITY_LABELS } from "@/types/discovery";

interface StabilityPanelProps {
  assessments: StabilityAssessment[];
}

const stabilityVariant = (label: string) => {
  switch (label) {
    case "stable": return "success" as const;
    case "partially_stable": return "info" as const;
    case "sensitive": return "warning" as const;
    default: return "neutral" as const;
  }
};

export function StabilityPanel({ assessments }: StabilityPanelProps) {
  if (assessments.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stability Assessments</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-left text-muted">
                <th className="pb-2 pr-3 font-medium">Predictor → Outcome</th>
                <th className="pb-2 pr-3 font-medium">Specs</th>
                <th className="pb-2 pr-3 font-medium">Completed</th>
                <th className="pb-2 pr-3 font-medium">Corrected Sig.</th>
                <th className="pb-2 pr-3 font-medium">Direction</th>
                <th className="pb-2 pr-3 font-medium">Coeff. Range</th>
                <th className="pb-2 font-medium">Stability</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((a) => (
                <tr
                  key={`${a.primary_predictor}_${a.outcome_variable}`}
                  className="border-b border-stone-100"
                >
                  <td className="py-2 pr-3 font-medium">
                    {a.primary_predictor} → {a.outcome_variable}
                  </td>
                  <td className="py-2 pr-3 font-mono">{a.n_specifications}</td>
                  <td className="py-2 pr-3 font-mono">{a.n_completed}</td>
                  <td className="py-2 pr-3 font-mono">
                    {a.n_corrected_significant}/{a.n_completed}
                  </td>
                  <td className="py-2 pr-3">
                    <Badge variant={a.direction_consistent ? "success" : "warning"}>
                      {a.direction_consistent ? "Consistent" : "Inconsistent"}
                    </Badge>
                  </td>
                  <td className="py-2 pr-3 font-mono">
                    {a.coefficient_range
                      ? `[${a.coefficient_range[0].toFixed(4)}, ${a.coefficient_range[1].toFixed(4)}]`
                      : "—"}
                  </td>
                  <td className="py-2">
                    <Badge variant={stabilityVariant(a.stability_label)}>
                      {STABILITY_LABELS[a.stability_label]}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
