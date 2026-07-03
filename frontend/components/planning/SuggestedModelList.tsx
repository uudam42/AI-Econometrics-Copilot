"use client";

import type { SuggestedModel } from "@/types/planning";
import { MODEL_TYPE_LABELS } from "@/types/modeling";
import type { ModelType } from "@/types/modeling";
import { Badge } from "@/components/ui/badge";

interface SuggestedModelListProps {
  models: SuggestedModel[];
  selected: string[];
  onToggle: (modelType: string) => void;
}

export function SuggestedModelList({
  models,
  selected,
  onToggle,
}: SuggestedModelListProps) {
  return (
    <div className="space-y-2">
      {models.map((model) => {
        const isSelected = selected.includes(model.model_type);
        const label =
          MODEL_TYPE_LABELS[model.model_type as ModelType] ?? model.model_type;
        const confidence = Math.round(model.confidence * 100);

        return (
          <div
            key={model.model_type}
            className={`rounded-md border px-4 py-3 transition-colors ${
              isSelected
                ? "border-accent bg-blue-50/50"
                : "border-border bg-white hover:bg-stone-50"
            }`}
          >
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={isSelected}
                onChange={() => onToggle(model.model_type)}
                className="h-3.5 w-3.5 rounded border-stone-300 text-accent focus:ring-accent"
              />
              <span className="text-sm font-medium text-foreground">
                {label}
              </span>
              <Badge
                variant={
                  confidence >= 70
                    ? "success"
                    : confidence >= 50
                      ? "info"
                      : "neutral"
                }
              >
                {confidence}% confidence
              </Badge>
            </div>

            <ul className="mt-1.5 space-y-0.5 pl-5 text-xs text-muted">
              {model.reasons.map((r, i) => (
                <li key={i} className="list-disc">
                  {r}
                </li>
              ))}
            </ul>

            {model.warnings.length > 0 && (
              <div className="mt-1.5 space-y-0.5 pl-5">
                {model.warnings.map((w, i) => (
                  <p key={i} className="text-xs text-amber-700">
                    {w}
                  </p>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
