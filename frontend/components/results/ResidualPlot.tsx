"use client";

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { PlotData } from "@/types/modeling";

export function ResidualPlot({ plotData }: { plotData: PlotData }) {
  const residualData = plotData.fitted_values.map((f, i) => ({
    fitted: parseFloat(f.toFixed(4)),
    residual: parseFloat(plotData.residuals[i].toFixed(4)),
  }));

  const actualVsFitted = plotData.actual_values.map((a, i) => ({
    actual: parseFloat(a.toFixed(4)),
    fitted: parseFloat(plotData.fitted_values[i].toFixed(4)),
  }));

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
          Residuals vs. Fitted Values
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <ScatterChart margin={{ top: 5, right: 10, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="fitted"
              name="Fitted"
              tick={{ fontSize: 10 }}
              label={{ value: "Fitted", position: "insideBottom", offset: -10, fontSize: 11 }}
            />
            <YAxis
              dataKey="residual"
              name="Residual"
              tick={{ fontSize: 10 }}
              label={{ value: "Residual", angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              formatter={(v) => typeof v === "number" ? v.toFixed(4) : String(v)}
            />
            <ReferenceLine y={0} stroke="#78716c" strokeDasharray="4 4" />
            <Scatter data={residualData} fill="#1d4ed8" opacity={0.5} r={3} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div>
        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
          Actual vs. Predicted Values
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <ScatterChart margin={{ top: 5, right: 10, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="actual"
              name="Actual"
              tick={{ fontSize: 10 }}
              label={{ value: "Actual", position: "insideBottom", offset: -10, fontSize: 11 }}
            />
            <YAxis
              dataKey="fitted"
              name="Fitted"
              tick={{ fontSize: 10 }}
              label={{ value: "Fitted", angle: -90, position: "insideLeft", fontSize: 11 }}
            />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              formatter={(v) => typeof v === "number" ? v.toFixed(4) : String(v)}
            />
            <Scatter data={actualVsFitted} fill="#059669" opacity={0.5} r={3} />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
