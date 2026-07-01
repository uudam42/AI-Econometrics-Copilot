import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { MissingValueBarChart } from "@/components/charts/MissingValueBarChart";
import type { DatasetQualityReport } from "@/types/dataset";

function formatPercent(value: number | null): string {
  return value === null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function DataQualitySection({ quality }: { quality: DatasetQualityReport }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Missing Values by Column</CardTitle>
        </CardHeader>
        <CardContent>
          <MissingValueBarChart columns={quality.columns} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Data Quality Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-muted">Duplicate rows</span>
            <span className="font-medium">
              {quality.duplicate_row_count} ({formatPercent(quality.duplicate_row_rate)})
            </span>
          </div>
          <div>
            <span className="text-muted">Constant columns</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {quality.constant_columns.length === 0 ? (
                <span className="text-xs text-muted">None detected</span>
              ) : (
                quality.constant_columns.map((c) => (
                  <Badge key={c} variant="warning">
                    {c}
                  </Badge>
                ))
              )}
            </div>
          </div>
          <div>
            <span className="text-muted">Potential ID columns</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {quality.potential_id_columns.length === 0 ? (
                <span className="text-xs text-muted">None detected</span>
              ) : (
                quality.potential_id_columns.map((c) => (
                  <Badge key={c} variant="info">
                    {c}
                  </Badge>
                ))
              )}
            </div>
          </div>
          <div>
            <span className="text-muted">Potential time columns</span>
            <div className="mt-1 flex flex-wrap gap-1">
              {quality.potential_time_columns.length === 0 ? (
                <span className="text-xs text-muted">None detected</span>
              ) : (
                quality.potential_time_columns.map((c) => (
                  <Badge key={c} variant="info">
                    {c}
                  </Badge>
                ))
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Column Quality Detail</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <THead>
              <TR>
                <TH>Column</TH>
                <TH>Missing</TH>
                <TH>Outliers</TH>
                <TH>Skewness</TH>
                <TH>Suggested transform</TH>
                <TH>Reason</TH>
              </TR>
            </THead>
            <TBody>
              {quality.columns.map((col) => (
                <TR key={col.column}>
                  <TD className="font-medium">{col.column}</TD>
                  <TD>{formatPercent(col.missing_rate)}</TD>
                  <TD>
                    {col.outlier_count === null
                      ? "—"
                      : `${col.outlier_count} (${col.outlier_method})`}
                  </TD>
                  <TD>{col.skewness === null ? "—" : col.skewness.toFixed(2)}</TD>
                  <TD>
                    {col.suggested_transformation ? (
                      <Badge variant="success">{col.suggested_transformation}</Badge>
                    ) : (
                      "—"
                    )}
                  </TD>
                  <TD className="max-w-xs whitespace-normal text-xs text-muted">
                    {col.reason ?? "—"}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
