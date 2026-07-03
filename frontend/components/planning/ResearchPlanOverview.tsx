"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { ResearchPlan, VariableRole } from "@/types/planning";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CausalWarningBanner } from "./CausalWarningBanner";
import { CandidateVariableCard } from "./CandidateVariableCard";
import { AmbiguityPanel } from "./AmbiguityPanel";
import { SuggestedModelList } from "./SuggestedModelList";
import { approvePlan } from "@/lib/api";

interface ResearchPlanOverviewProps {
  plan: ResearchPlan;
}

export function ResearchPlanOverview({ plan }: ResearchPlanOverviewProps) {
  const router = useRouter();

  const initialSelected = new Set(
    plan.candidate_variables
      .filter(
        (c) =>
          c.role !== "unresolved" && c.confidence >= 0.3
      )
      .map((c) => c.column_name)
  );
  const [selectedVars, setSelectedVars] = useState<Set<string>>(initialSelected);

  const initialRoles: Record<string, VariableRole> = {};
  for (const c of plan.candidate_variables) {
    initialRoles[c.column_name] = c.role;
  }
  const [roles, setRoles] = useState<Record<string, VariableRole>>(initialRoles);

  const initialModels = plan.suggested_models
    .filter((m) => m.confidence >= 0.5)
    .map((m) => m.model_type);
  const [selectedModels, setSelectedModels] = useState<string[]>(initialModels);

  const [approving, setApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const toggleVar = (name: string) => {
    setSelectedVars((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  const changeRole = (name: string, role: VariableRole) => {
    setRoles((prev) => ({ ...prev, [name]: role }));
  };

  const toggleModel = (modelType: string) => {
    setSelectedModels((prev) =>
      prev.includes(modelType)
        ? prev.filter((m) => m !== modelType)
        : [...prev, modelType]
    );
  };

  const depVar = Object.entries(roles).find(
    ([name, role]) => role === "dependent_variable" && selectedVars.has(name)
  )?.[0];

  const primaryIv = Object.entries(roles).find(
    ([name, role]) =>
      role === "primary_independent_variable" && selectedVars.has(name)
  )?.[0];

  const controlVars = Object.entries(roles)
    .filter(
      ([name, role]) => role === "control_variable" && selectedVars.has(name)
    )
    .map(([name]) => name);

  const entityCol =
    Object.entries(roles).find(
      ([, role]) => role === "entity_column"
    )?.[0] ?? null;

  const timeCol =
    Object.entries(roles).find(
      ([, role]) => role === "time_column"
    )?.[0] ?? null;

  const canApprove =
    !!depVar && !!primaryIv && selectedModels.length > 0;

  const handleApprove = async () => {
    if (!depVar || !primaryIv) return;
    setApproving(true);
    setError(null);
    try {
      const result = await approvePlan(plan.plan_id, {
        dependent_variable: depVar,
        primary_independent_variable: primaryIv,
        control_variables: controlVars,
        entity_column: entityCol,
        time_column: timeCol,
        approved_transformations: plan.suggested_transformations
          .filter((t) => t.requires_user_confirmation)
          .map((t) => ({
            operation: t.operation,
            columns: t.columns,
          })),
        selected_candidate_models: selectedModels,
      });
      router.push(result.redirect_path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setApproving(false);
    }
  };

  return (
    <div className="space-y-5">
      <CausalWarningBanner
        intent={plan.inferred_analysis_intent}
        causalWarning={plan.causal_warning}
      />

      <Card>
        <CardHeader>
          <CardTitle>Dataset Structure</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted">
            {plan.detected_structure_summary}
          </p>
        </CardContent>
      </Card>

      <AmbiguityPanel ambiguities={plan.ambiguities} />

      <Card>
        <CardHeader>
          <CardTitle>Candidate Variables</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-3 text-xs text-muted">
            Review and adjust variable roles. Select the variables to include in
            your analysis.
          </p>
          <div className="space-y-2">
            {plan.candidate_variables.map((c) => (
              <CandidateVariableCard
                key={c.column_name}
                candidate={c}
                selected={selectedVars.has(c.column_name)}
                selectedRole={roles[c.column_name] ?? null}
                onToggle={toggleVar}
                onRoleChange={changeRole}
              />
            ))}
          </div>
        </CardContent>
      </Card>

      {plan.suggested_transformations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Suggested Transformations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {plan.suggested_transformations.map((t, i) => (
                <div
                  key={i}
                  className="rounded-md border border-border bg-white px-4 py-3"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">
                      {t.operation.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-muted">
                      on {t.columns.join(", ")}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted">{t.reason}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Suggested Models</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-3 text-xs text-muted">
            Select which models to run in the comparison.
          </p>
          <SuggestedModelList
            models={plan.suggested_models}
            selected={selectedModels}
            onToggle={toggleModel}
          />
        </CardContent>
      </Card>

      {error && (
        <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div className="flex items-center justify-between gap-4 rounded-md border border-border bg-stone-50 px-5 py-4">
        <div className="text-xs text-muted">
          {depVar ? (
            <>
              DV: <strong>{depVar}</strong>
            </>
          ) : (
            <span className="text-amber-700">No dependent variable selected</span>
          )}
          {primaryIv && (
            <>
              {" | "}IV: <strong>{primaryIv}</strong>
            </>
          )}
          {controlVars.length > 0 && (
            <>
              {" | "}Controls: {controlVars.join(", ")}
            </>
          )}
          {" | "}Models: {selectedModels.length}
        </div>
        <Button
          onClick={handleApprove}
          disabled={!canApprove || approving}
        >
          {approving
            ? "Approving..."
            : "Approve & Configure Model"}
        </Button>
      </div>
    </div>
  );
}
