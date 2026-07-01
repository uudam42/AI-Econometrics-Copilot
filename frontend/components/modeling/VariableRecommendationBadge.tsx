import { cn } from "@/lib/utils";

const HINT_STYLES: Record<string, string> = {
  "Potential Outcome": "bg-blue-50 text-blue-700 border-blue-200",
  "Potential Explanatory Variable": "bg-green-50 text-green-700 border-green-200",
  "Potential Control": "bg-amber-50 text-amber-700 border-amber-200",
  "Possible Entity ID": "bg-purple-50 text-purple-700 border-purple-200",
  "Possible Time Variable": "bg-teal-50 text-teal-700 border-teal-200",
  "Categorical Variable": "bg-rose-50 text-rose-700 border-rose-200",
  "Not Recommended for Regression": "bg-stone-50 text-stone-500 border-stone-200",
};

export function VariableRecommendationBadge({ hint }: { hint: string }) {
  const style = HINT_STYLES[hint] ?? "bg-stone-50 text-stone-500 border-stone-200";
  return (
    <span
      className={cn(
        "inline-block rounded border px-1.5 py-0.5 text-xs font-medium",
        style
      )}
    >
      {hint}
    </span>
  );
}
