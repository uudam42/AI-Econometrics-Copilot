"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { VariableEligibility } from "@/types/discovery";

interface EligibilitySummaryProps {
  results: VariableEligibility[];
}

export function EligibilitySummary({ results }: EligibilitySummaryProps) {
  const eligible = results.filter((r) => r.eligible);
  const excluded = results.filter((r) => !r.eligible);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Variable Screening</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-4 text-sm">
          <span>
            <span className="font-semibold text-emerald-700">{eligible.length}</span>{" "}
            eligible
          </span>
          <span>
            <span className="font-semibold text-red-600">{excluded.length}</span>{" "}
            excluded
          </span>
          <span className="text-muted">{results.length} total screened</span>
        </div>

        {excluded.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-muted">Excluded Variables</p>
            <div className="space-y-1.5">
              {excluded.map((v) => (
                <div
                  key={v.column_name}
                  className="flex items-start gap-2 rounded border border-red-100 bg-red-50/50 px-3 py-2 text-xs"
                >
                  <span className="shrink-0 font-medium text-red-700">
                    {v.column_name}
                  </span>
                  <span className="text-red-600">
                    {v.exclusion_reasons.join("; ")}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {eligible.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-medium text-muted">Eligible Variables</p>
            <div className="flex flex-wrap gap-1.5">
              {eligible.map((v) => (
                <Badge key={v.column_name} variant="success">
                  {v.column_name}
                  {v.quality_score > 0 && (
                    <span className="ml-1 opacity-60">
                      ({(v.quality_score * 100).toFixed(0)}%)
                    </span>
                  )}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
