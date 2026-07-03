"use client";

import type { CandidateVariable, VariableRole } from "@/types/planning";
import { VARIABLE_ROLE_LABELS } from "@/types/planning";
import { Badge } from "@/components/ui/badge";

interface CandidateVariableCardProps {
  candidate: CandidateVariable;
  selected: boolean;
  selectedRole: VariableRole | null;
  onToggle: (columnName: string) => void;
  onRoleChange: (columnName: string, role: VariableRole) => void;
}

const roleBadgeVariant = (role: VariableRole) => {
  switch (role) {
    case "dependent_variable":
      return "info" as const;
    case "primary_independent_variable":
      return "success" as const;
    case "control_variable":
      return "neutral" as const;
    case "entity_column":
    case "time_column":
      return "warning" as const;
    default:
      return "danger" as const;
  }
};

const ASSIGNABLE_ROLES: VariableRole[] = [
  "dependent_variable",
  "primary_independent_variable",
  "control_variable",
];

export function CandidateVariableCard({
  candidate,
  selected,
  selectedRole,
  onToggle,
  onRoleChange,
}: CandidateVariableCardProps) {
  const isStructural =
    candidate.role === "entity_column" || candidate.role === "time_column";
  const displayRole = selectedRole ?? candidate.role;
  const confidence = Math.round(candidate.confidence * 100);

  return (
    <div
      className={`rounded-md border px-4 py-3 transition-colors ${
        selected
          ? "border-accent bg-blue-50/50"
          : "border-border bg-white hover:bg-stone-50"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          {!isStructural && (
            <input
              type="checkbox"
              checked={selected}
              onChange={() => onToggle(candidate.column_name)}
              className="mt-0.5 h-3.5 w-3.5 rounded border-stone-300 text-accent focus:ring-accent"
            />
          )}
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-foreground">
                {candidate.column_name}
              </span>
              <Badge variant={roleBadgeVariant(displayRole)}>
                {VARIABLE_ROLE_LABELS[displayRole]}
              </Badge>
              <span className="text-[11px] text-muted">{confidence}%</span>
            </div>
          </div>
        </div>

        {!isStructural && selected && (
          <select
            value={displayRole}
            onChange={(e) =>
              onRoleChange(
                candidate.column_name,
                e.target.value as VariableRole
              )
            }
            className="rounded border border-border bg-white px-2 py-1 text-xs text-foreground focus:border-accent focus:outline-none"
          >
            {ASSIGNABLE_ROLES.map((r) => (
              <option key={r} value={r}>
                {VARIABLE_ROLE_LABELS[r]}
              </option>
            ))}
          </select>
        )}
      </div>

      {candidate.evidence.length > 0 && (
        <ul className="mt-2 space-y-0.5 pl-5 text-xs text-muted">
          {candidate.evidence.map((e, i) => (
            <li key={i} className="list-disc">
              {e}
            </li>
          ))}
        </ul>
      )}

      {candidate.warnings.length > 0 && (
        <div className="mt-1.5 space-y-0.5">
          {candidate.warnings.map((w, i) => (
            <p key={i} className="text-xs text-amber-700">
              {w}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
