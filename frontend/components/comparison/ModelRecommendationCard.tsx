"use client";

import type { ModelSelectionRecommendation } from "@/types/comparison";
import { MODEL_TYPE_LABELS } from "@/types/modeling";

const CONFIDENCE_COLORS = {
  high: "text-green-700 bg-green-50 border-green-200",
  medium: "text-amber-700 bg-amber-50 border-amber-200",
  low: "text-red-700 bg-red-50 border-red-200",
};

export function ModelRecommendationCard({ rec }: { rec: ModelSelectionRecommendation }) {
  const label = MODEL_TYPE_LABELS[rec.recommended_model] ?? rec.recommended_model;
  const confBadge = CONFIDENCE_COLORS[rec.confidence] ?? "";

  return (
    <div className="rounded-lg border-2 border-blue-200 bg-blue-50 p-4 space-y-3">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-blue-600">
            Recommended Model
          </p>
          <p className="mt-0.5 text-lg font-bold text-blue-900">{label}</p>
        </div>
        <div className="text-right space-y-1">
          <span className={`rounded border px-2 py-0.5 text-xs font-semibold ${confBadge}`}>
            {rec.confidence} confidence
          </span>
          <p className="text-2xl font-bold text-blue-700">{rec.score}<span className="text-sm font-normal text-blue-500">/100</span></p>
        </div>
      </div>

      {rec.reasons.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-blue-700 mb-1">Why this model:</p>
          <ul className="space-y-1">
            {rec.reasons.map((r, i) => (
              <li key={i} className="flex gap-2 text-xs text-blue-800">
                <span className="mt-0.5 text-blue-400">•</span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {rec.warnings.length > 0 && (
        <div className="rounded border border-amber-200 bg-amber-50 p-2">
          <p className="text-xs font-semibold text-amber-700 mb-1">Warnings:</p>
          {rec.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-800">• {w}</p>
          ))}
        </div>
      )}

      {rec.alternative_models.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-blue-700 mb-1">Alternative models:</p>
          {rec.alternative_models.map((alt, i) => (
            <p key={i} className="text-xs text-blue-700">
              • {alt.model_label ?? MODEL_TYPE_LABELS[alt.model_type] ?? alt.model_type} — {alt.reason}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
