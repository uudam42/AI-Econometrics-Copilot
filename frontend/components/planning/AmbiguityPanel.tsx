"use client";

interface AmbiguityPanelProps {
  ambiguities: string[];
}

export function AmbiguityPanel({ ambiguities }: AmbiguityPanelProps) {
  if (ambiguities.length === 0) return null;

  return (
    <div className="rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
      <p className="mb-2 text-sm font-medium text-amber-900">
        Ambiguities Detected
      </p>
      <ul className="space-y-1">
        {ambiguities.map((a, i) => (
          <li key={i} className="text-xs text-amber-800">
            &bull; {a}
          </li>
        ))}
      </ul>
    </div>
  );
}
