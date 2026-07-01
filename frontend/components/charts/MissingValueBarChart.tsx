"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ColumnQualityReport } from "@/types/dataset";

export function MissingValueBarChart({ columns }: { columns: ColumnQualityReport[] }) {
  const data = columns.map((c) => ({
    column: c.column,
    missingRate: Math.round(c.missing_rate * 1000) / 10,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(180, data.length * 28)}>
      <BarChart data={data} layout="vertical" margin={{ left: 24, right: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" horizontal={false} />
        <XAxis
          type="number"
          unit="%"
          domain={[0, 100]}
          tick={{ fontSize: 11, fill: "#78716c" }}
        />
        <YAxis
          type="category"
          dataKey="column"
          width={140}
          tick={{ fontSize: 11, fill: "#1c1917" }}
        />
        <Tooltip
          formatter={(value) => [`${value}%`, "Missing rate"]}
          contentStyle={{ fontSize: 12, borderRadius: 6 }}
        />
        <Bar dataKey="missingRate" fill="#1d4ed8" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
