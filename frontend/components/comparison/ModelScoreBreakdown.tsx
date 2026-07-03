"use client";

import type { ModelScoreComponent } from "@/types/comparison";

function ScoreBar({ score }: { score: number }) {
  const color =
    score >= 80 ? "bg-green-500" : score >= 50 ? "bg-amber-500" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 w-24 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-mono">{score}/100</span>
    </div>
  );
}

export function ModelScoreBreakdown({ components }: { components: ModelScoreComponent[] }) {
  return (
    <div className="space-y-3">
      {components.map((c) => (
        <div key={c.criterion} className="rounded border px-3 py-2">
          <div className="flex items-center justify-between gap-4 mb-1">
            <div>
              <span className="text-xs font-semibold">{c.criterion}</span>
              <span className="ml-2 text-xs text-muted">weight: {(c.weight * 100).toFixed(0)}%</span>
            </div>
            <ScoreBar score={c.score} />
          </div>
          <p className="text-xs text-muted leading-snug">{c.explanation}</p>
        </div>
      ))}
    </div>
  );
}
