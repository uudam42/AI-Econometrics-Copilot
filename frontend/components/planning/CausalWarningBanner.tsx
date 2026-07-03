"use client";

import type { AnalysisIntent } from "@/types/planning";
import { INTENT_LABELS } from "@/types/planning";
import { Badge } from "@/components/ui/badge";

interface CausalWarningBannerProps {
  intent: AnalysisIntent;
  causalWarning: string;
}

export function CausalWarningBanner({
  intent,
  causalWarning,
}: CausalWarningBannerProps) {
  const isCausal = intent === "causal_claim_requested";

  return (
    <div
      className={`rounded-md border px-4 py-3 text-sm ${
        isCausal
          ? "border-amber-300 bg-amber-50 text-amber-900"
          : "border-blue-200 bg-blue-50 text-blue-800"
      }`}
    >
      <div className="mb-1 flex items-center gap-2">
        <span className="font-medium">
          {isCausal ? "Causal Language Detected" : "Analysis Intent"}
        </span>
        <Badge variant={isCausal ? "warning" : "info"}>
          {INTENT_LABELS[intent]}
        </Badge>
      </div>
      <p className="text-xs leading-relaxed">{causalWarning}</p>
    </div>
  );
}
