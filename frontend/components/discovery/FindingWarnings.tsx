"use client";

interface FindingWarningsProps {
  warnings: string[];
}

export function FindingWarnings({ warnings }: FindingWarningsProps) {
  if (warnings.length === 0) return null;

  return (
    <div className="space-y-1">
      {warnings.map((w, i) => (
        <p
          key={i}
          className="rounded border border-amber-200 bg-amber-50 px-3 py-1.5 text-[11px] text-amber-800"
        >
          {w}
        </p>
      ))}
    </div>
  );
}
