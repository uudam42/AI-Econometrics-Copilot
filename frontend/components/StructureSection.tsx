import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DatasetType, StructureDetectionResult } from "@/types/dataset";

const LABELS: Record<DatasetType, string> = {
  panel: "Panel Data",
  time_series: "Time Series",
  cross_sectional: "Cross-Sectional",
  unknown: "Unknown / Mixed Structure",
};

export function StructureSection({ structure }: { structure: StructureDetectionResult }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Detected Structure</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <Badge variant="info" className="text-sm">
          {LABELS[structure.dataset_type]}
        </Badge>
        <p className="text-muted">{structure.explanation}</p>
        <dl className="grid grid-cols-2 gap-y-1 text-xs sm:grid-cols-4">
          {structure.entity_column && (
            <>
              <dt className="text-muted">Entity column</dt>
              <dd className="font-medium">{structure.entity_column}</dd>
            </>
          )}
          {structure.time_column && (
            <>
              <dt className="text-muted">Time column</dt>
              <dd className="font-medium">{structure.time_column}</dd>
            </>
          )}
          {structure.entity_count !== null && (
            <>
              <dt className="text-muted">Entities</dt>
              <dd className="font-medium">{structure.entity_count}</dd>
            </>
          )}
          {structure.time_period_count !== null && (
            <>
              <dt className="text-muted">Time periods</dt>
              <dd className="font-medium">{structure.time_period_count}</dd>
            </>
          )}
          {structure.is_balanced_panel !== null && (
            <>
              <dt className="text-muted">Balanced panel</dt>
              <dd className="font-medium">{structure.is_balanced_panel ? "Yes" : "No"}</dd>
            </>
          )}
        </dl>
      </CardContent>
    </Card>
  );
}
