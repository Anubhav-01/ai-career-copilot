"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Info } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import type { ResumeAnalysis } from "@/types/api";

const severityVariant = {
  critical: "danger",
  warning: "warning",
  info: "neutral",
} as const;

export function AnalysisPanel({ resumeId }: { resumeId: string }) {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: analysis, isLoading } = useQuery({
    queryKey: ["resume-analysis", resumeId],
    queryFn: () => api<ResumeAnalysis | null>(`/api/resumes/${resumeId}/analysis`),
  });

  const analyze = useMutation({
    mutationFn: () =>
      api<ResumeAnalysis>(`/api/resumes/${resumeId}/analyze`, { method: "POST" }),
    onSuccess: (result) => {
      queryClient.setQueryData(["resume-analysis", resumeId], result);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast("Analysis complete.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Analysis failed.", "error"),
  });

  if (isLoading) return <Skeleton className="h-64" />;

  if (!analysis) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center py-12 text-center">
          <p className="font-medium text-slate-900">No analysis yet</p>
          <p className="mt-1 max-w-md text-sm text-slate-500">
            Run the analysis to get your weighted resume score, ATS-style checks and
            actionable recommendations.
          </p>
          <Button className="mt-4" loading={analyze.isPending} onClick={() => analyze.mutate()}>
            Analyze resume
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row">
        <Card className="flex-1 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-500">Overall score</p>
              <p className="mt-1 text-4xl font-bold text-slate-900">
                {Math.round(analysis.overall_score)}
                <span className="text-lg font-normal text-slate-400">/100</span>
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              loading={analyze.isPending}
              onClick={() => analyze.mutate()}
            >
              Re-analyze
            </Button>
          </div>
          <Progress value={analysis.overall_score} colorByScore className="mt-4 h-3" />
          {analysis.explanation && (
            <p className="mt-4 flex gap-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
              <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" aria-hidden />
              {analysis.explanation}
            </p>
          )}
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Score breakdown</CardTitle>
          <CardDescription>
            Overall = weighted average of these components. Weights are configurable
            and documented — nothing arbitrary.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {analysis.scores.components.map((component) => (
            <div key={component.key}>
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">
                  {component.label}{" "}
                  <span className="text-xs text-slate-400">
                    ({Math.round(component.weight * 100)}% weight)
                  </span>
                </span>
                <span className="font-semibold text-slate-900">
                  {Math.round(component.score)}
                </span>
              </div>
              <Progress value={component.score} colorByScore className="mt-1.5" />
              <p className="mt-1 text-xs text-slate-500">{component.explanation}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>ATS-style analysis</CardTitle>
          <CardDescription>
            Heuristic checks modeled on common applicant-tracking-system behavior.
            This is a simulation for guidance — not an actual proprietary ATS.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2 text-xs text-slate-500">
            <span>
              Action verbs: <strong>{analysis.ats.action_verb_count}</strong>
            </span>
            <span>·</span>
            <span>
              Quantified bullets:{" "}
              <strong>{Math.round(analysis.ats.quantified_bullet_ratio * 100)}%</strong>
            </span>
            <span>·</span>
            <span>
              Sections detected: <strong>{analysis.ats.detected_sections.join(", ") || "none"}</strong>
            </span>
          </div>
          {analysis.ats.findings.length === 0 ? (
            <p className="text-sm text-emerald-600">No issues detected. Well done!</p>
          ) : (
            analysis.ats.findings.map((finding, index) => (
              <div key={index} className="rounded-lg border border-slate-200 p-4">
                <div className="flex items-center gap-2">
                  <Badge variant={severityVariant[finding.severity]}>{finding.severity}</Badge>
                  <span className="text-xs uppercase tracking-wide text-slate-400">
                    {finding.category}
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium text-slate-900">{finding.problem}</p>
                <p className="mt-1 text-sm text-slate-600">{finding.recommendation}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
