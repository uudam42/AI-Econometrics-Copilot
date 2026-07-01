import type { CorrelationMatrixResult } from "@/types/modeling";

function correlationColor(v: number | null): string {
  if (v === null) return "#e7e5e4";
  const abs = Math.abs(v);
  if (v > 0) {
    const intensity = Math.round(abs * 200);
    return `rgb(${255 - intensity}, ${255 - Math.round(intensity * 0.4)}, 255)`;
  } else {
    const intensity = Math.round(abs * 200);
    return `rgb(255, ${255 - Math.round(intensity * 0.4)}, ${255 - intensity})`;
  }
}

function textColor(v: number | null): string {
  if (v === null) return "#78716c";
  return Math.abs(v) > 0.5 ? "#ffffff" : "#1c1917";
}

export function CorrelationHeatmap({ data }: { data: CorrelationMatrixResult }) {
  if (data.variables.length === 0) {
    return <p className="text-xs text-muted">No numeric variables for correlation matrix.</p>;
  }

  const cellSize = Math.min(80, Math.floor(480 / data.variables.length));

  return (
    <div className="overflow-x-auto">
      <div
        style={{
          display: "grid",
          gridTemplateColumns: `80px repeat(${data.variables.length}, ${cellSize}px)`,
          gap: "1px",
        }}
      >
        {/* Header row */}
        <div />
        {data.variables.map((v) => (
          <div
            key={v}
            style={{ width: cellSize, fontSize: "10px" }}
            className="overflow-hidden text-ellipsis whitespace-nowrap px-1 py-1 text-center font-medium text-muted"
            title={v}
          >
            {v.length > 8 ? v.slice(0, 7) + "…" : v}
          </div>
        ))}

        {/* Data rows */}
        {data.variables.map((rowVar, r) => (
          <>
            <div
              key={`label-${rowVar}`}
              style={{ fontSize: "10px" }}
              className="flex items-center overflow-hidden text-ellipsis whitespace-nowrap pr-2 font-medium text-muted"
              title={rowVar}
            >
              {rowVar.length > 10 ? rowVar.slice(0, 9) + "…" : rowVar}
            </div>
            {data.matrix[r].map((v, c) => (
              <div
                key={`cell-${r}-${c}`}
                style={{
                  width: cellSize,
                  height: cellSize,
                  backgroundColor: correlationColor(v),
                  color: textColor(v),
                  fontSize: "10px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "2px",
                }}
                title={`${rowVar} × ${data.variables[c]}: ${v?.toFixed(3) ?? "—"}`}
              >
                {v !== null ? v.toFixed(2) : "—"}
              </div>
            ))}
          </>
        ))}
      </div>
      <p className="mt-2 text-xs text-muted">Blue = positive correlation, Red = negative correlation.</p>
    </div>
  );
}
