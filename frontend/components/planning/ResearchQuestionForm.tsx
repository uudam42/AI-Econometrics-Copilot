"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ResearchQuestionFormProps {
  onSubmit: (question: string, context?: string) => void;
  loading: boolean;
}

export function ResearchQuestionForm({
  onSubmit,
  loading,
}: ResearchQuestionFormProps) {
  const [question, setQuestion] = useState("");
  const [context, setContext] = useState("");
  const [showContext, setShowContext] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    onSubmit(question.trim(), context.trim() || undefined);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Research Question</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label
              htmlFor="research-question"
              className="mb-1.5 block text-xs font-medium text-muted"
            >
              Describe what you want to investigate
            </label>
            <textarea
              id="research-question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder='e.g. "Is internet penetration associated with GDP per capita across countries over time?"'
              rows={3}
              className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-foreground placeholder:text-stone-400 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
            />
          </div>

          {showContext ? (
            <div>
              <label
                htmlFor="context"
                className="mb-1.5 block text-xs font-medium text-muted"
              >
                Additional context (optional)
              </label>
              <textarea
                id="context"
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Any specific hypotheses, preferred variables, or constraints..."
                rows={2}
                className="w-full rounded-md border border-border bg-white px-3 py-2 text-sm text-foreground placeholder:text-stone-400 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
              />
            </div>
          ) : (
            <button
              type="button"
              onClick={() => setShowContext(true)}
              className="self-start text-xs text-accent hover:underline"
            >
              + Add context
            </button>
          )}

          <Button type="submit" disabled={!question.trim() || loading}>
            {loading ? "Generating Plan..." : "Generate Research Plan"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
