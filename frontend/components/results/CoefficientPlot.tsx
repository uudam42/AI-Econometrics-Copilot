"use client";

import {
  ComposedChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ErrorBar,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import type { CoefficientResult } from "@/types/modeling";

interface PlotPoint {
  variable: string;
  coeff: number;
  errorLow: number;
  errorHigh: number;
  significance: string;
}

export function CoefficientPlot({ coefficients }: { coefficients: CoefficientResult[] }) {
  const displayCoeffs = coefficients.filter((c) => c.variable !== "Intercept" && c.variable !== "const");

  if (displayCoeffs.length === 0) {
    return <p className="text-xs text-muted">No non-intercept coefficients to display.</p>;
  }

  const data: PlotPoint[] = displayCoeffs.map((c) => ({
    variable: c.variable,
    coeff: c.coefficient ?? 0,
    errorLow: c.coefficient !== null && c.ci_lower !== null ? c.coefficient - c.ci_lower : 0,
    errorHigh: c.coefficient !== null && c.ci_upper !== null ? c.ci_upper - c.coefficient : 0,
    significance: c.significance,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, data.length * 50 + 60)}>
      <ComposedChart
        layout="vertical"
        data={data}
        margin={{ top: 10, right: 30, bottom: 10, left: 120 }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
        <YAxis
          type="category"
          dataKey="variable"
          width={110}
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          formatter={(value) => [typeof value === "number" ? value.toFixed(4) : value, "Coefficient"]}
          labelFormatter={(label) => `Variable: ${label}`}
        />
        <ReferenceLine x={0} stroke="#78716c" strokeDasharray="4 4" />
        <Scatter
          dataKey="coeff"
          fill="#1d4ed8"
          shape={(props) => {
            const { cx, cy } = props as { cx: number; cy: number };
            return <circle cx={cx} cy={cy} r={5} fill="#1d4ed8" />;
          }}
        >
          <ErrorBar
            dataKey="errorLow"
            width={4}
            strokeWidth={2}
            stroke="#1d4ed8"
            direction="x"
          />
        </Scatter>
      </ComposedChart>
    </ResponsiveContainer>
  );
}
