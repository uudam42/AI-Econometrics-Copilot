"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { createPlanFromFinding } from "@/lib/api";
import { useRouter } from "next/navigation";

interface InvestigateFindingButtonProps {
  discoveryId: string;
  findingId: string;
  datasetId: string;
}

export function InvestigateFindingButton({
  discoveryId,
  findingId,
  datasetId,
}: InvestigateFindingButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleClick = async () => {
    setLoading(true);
    setError(null);
    try {
      const plan = await createPlanFromFinding(discoveryId, findingId);
      router.push(`/datasets/${datasetId}/plan?planId=${plan.plan_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create research plan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button onClick={handleClick} disabled={loading}>
        {loading ? "Creating Plan..." : "Investigate This Relationship →"}
      </Button>
      {error && (
        <p className="mt-1 text-xs text-red-600">{error}</p>
      )}
    </div>
  );
}
