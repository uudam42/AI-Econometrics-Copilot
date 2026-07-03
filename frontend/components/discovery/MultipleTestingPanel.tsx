"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CorrectedResult } from "@/types/discovery";

interface MultipleTestingPanelProps {
  results: CorrectedResult[];
  method: string;
}

export function MultipleTestingPanel({ results, method }: MultipleTestingPanelProps) {
  if (results.length === 0) return null;

  const passing = results.filter((r) => r.passes_threshold);
  const failing = results.filter((r) => !r.passes_threshold);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Multiple-Testing Correction</CardTitle>
          <Badge variant="info">{method.replace("_", "-")}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-4 text-xs">
          <span>
            <span className="font-semibold text-emerald-700">{passing.length}</span>{" "}
            pass threshold
          </span>
          <span>
            <span className="font-semibold text-red-600">{failing.length}</span>{" "}
            below threshold
          </span>
          <span className="text-muted">{results.length} total tested</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-left text-muted">
                <th className="pb-2 pr-3 font-medium">Spec ID</th>
                <th className="pb-2 pr-3 font-medium">Raw p-value</th>
                <th className="pb-2 pr-3 font-medium">Adjusted p-value</th>
                <th className="pb-2 font-medium">Passes</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.spec_id} className="border-b border-stone-100">
                  <td className="py-1.5 pr-3 font-mono">{r.spec_id}</td>
                  <td className="py-1.5 pr-3 font-mono">
                    {r.raw_p_value != null ? r.raw_p_value.toFixed(4) : "—"}
                  </td>
                  <td className="py-1.5 pr-3 font-mono">
                    {r.adjusted_p_value != null ? r.adjusted_p_value.toFixed(4) : "—"}
                  </td>
                  <td className="py-1.5">
                    <Badge variant={r.passes_threshold ? "success" : "danger"}>
                      {r.passes_threshold ? "Yes" : "No"}
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
