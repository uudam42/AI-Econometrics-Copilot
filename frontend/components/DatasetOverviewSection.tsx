import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import type { DatasetOverview } from "@/types/dataset";

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(2);
  return String(value);
}

export function DatasetOverviewSection({ overview }: { overview: DatasetOverview }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Dataset Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-y-2 text-sm">
            <dt className="text-muted">File name</dt>
            <dd className="font-medium">{overview.filename}</dd>
            <dt className="text-muted">Rows</dt>
            <dd className="font-medium">{overview.n_rows.toLocaleString()}</dd>
            <dt className="text-muted">Columns</dt>
            <dd className="font-medium">{overview.n_columns}</dd>
            <dt className="text-muted">Uploaded</dt>
            <dd className="font-medium">
              {new Date(overview.uploaded_at).toLocaleString()}
            </dd>
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Column Types</CardTitle>
        </CardHeader>
        <CardContent className="max-h-72 overflow-y-auto">
          <Table>
            <THead>
              <TR>
                <TH>Column</TH>
                <TH>Role</TH>
                <TH>Hints</TH>
              </TR>
            </THead>
            <TBody>
              {overview.column_types.map((col) => (
                <TR key={col.name}>
                  <TD className="font-medium">{col.name}</TD>
                  <TD>
                    <Badge variant="info">{col.inferred_role}</Badge>
                  </TD>
                  <TD>
                    <div className="flex flex-wrap gap-1">
                      {col.role_hints.map((hint) => (
                        <Badge key={hint} variant="neutral">
                          {hint}
                        </Badge>
                      ))}
                    </div>
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Data Preview (first {overview.preview_rows.length} rows)</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <THead>
              <TR>
                {overview.column_types.map((col) => (
                  <TH key={col.name}>{col.name}</TH>
                ))}
              </TR>
            </THead>
            <TBody>
              {overview.preview_rows.map((row, idx) => (
                <TR key={idx}>
                  {overview.column_types.map((col) => (
                    <TD key={col.name}>{formatCell(row[col.name])}</TD>
                  ))}
                </TR>
              ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
