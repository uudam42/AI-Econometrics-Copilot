"use client";

import { useParams } from "next/navigation";
import { useState } from "react";
import type { ResearchPlan } from "@/types/planning";
import { generatePlan } from "@/lib/api";
import { ResearchQuestionForm } from "@/components/planning/ResearchQuestionForm";
import { ResearchPlanOverview } from "@/components/planning/ResearchPlanOverview";

export default function PlanPage() {
  const { datasetId } = useParams<{ datasetId: string }>();
  const [plan, setPlan] = useState<ResearchPlan | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (question: string, context?: string) => {
    setLoading(true);
    setError(null);
    setPlan(null);
    try {
      const result = await generatePlan({
        dataset_id: datasetId,
        research_question: question,
        context,
      });
      setPlan(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Plan generation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-6">
        <h1 className="text-lg font-bold tracking-tight text-foreground">
          Research Planning
        </h1>
        <p className="mt-1 text-sm text-muted">
          Describe your research question in natural language. The system will
          inspect your dataset and generate a structured research plan for your
          review.
        </p>
      </div>

      <div className="space-y-6">
        <ResearchQuestionForm onSubmit={handleSubmit} loading={loading} />

        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800">
            {error}
          </div>
        )}

        {plan && (
          <>
            <div className="rounded-md border border-emerald-300 bg-emerald-50 px-4 py-3">
              <p className="text-sm font-medium text-emerald-900">
                Research plan generated
              </p>
              <p className="mt-0.5 text-xs text-emerald-700">
                Review the suggestions below. Adjust variable roles, select
                models, then approve to proceed.
              </p>
            </div>
            <ResearchPlanOverview plan={plan} />
          </>
        )}
      </div>
    </main>
  );
}
