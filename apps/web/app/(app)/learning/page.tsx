"use client";

import { useQuery } from "@tanstack/react-query";
import { GraduationCap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type { LearningRoadmap } from "@/types/api";

export default function LearningPage() {
  const { data: roadmaps, isLoading } = useQuery({
    queryKey: ["roadmaps"],
    queryFn: () => api<LearningRoadmap[]>("/api/learning/roadmaps"),
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Learning Roadmaps</h1>
        <p className="text-sm text-slate-500">
          Week-by-week plans for closing your skill gaps, tailored to what you already
          know. No fabricated course links — just focused practice.
        </p>
      </div>

      {!roadmaps || roadmaps.length === 0 ? (
        <EmptyState
          icon={GraduationCap}
          title="No roadmaps yet"
          description="Generate a roadmap from any skill gap on the Skills & Gaps page."
          action={
            <Link href="/skills">
              <Button>Go to Skills & Gaps</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {roadmaps.map((roadmap) => (
            <Card key={roadmap.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{roadmap.skill}</CardTitle>
                  <Badge
                    variant={
                      roadmap.priority === "critical"
                        ? "danger"
                        : roadmap.priority === "important"
                          ? "warning"
                          : "neutral"
                    }
                  >
                    {titleCase(roadmap.priority)}
                  </Badge>
                </div>
                <CardDescription>
                  Estimated effort: {roadmap.estimated_weeks} week
                  {roadmap.estimated_weeks === 1 ? "" : "s"}
                  {roadmap.content.prerequisites.length > 0 &&
                    ` · builds on: ${roadmap.content.prerequisites.join(", ")}`}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="relative space-y-4 border-l border-slate-200 pl-5">
                  {roadmap.content.stages.map((stage) => (
                    <li key={stage.period} className="relative">
                      <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full bg-brand-500" aria-hidden />
                      <p className="text-sm font-semibold text-slate-900">{stage.period}</p>
                      <p className="text-sm text-slate-600">{stage.focus}</p>
                      <p className="mt-1 rounded-md bg-slate-50 p-2 text-xs text-slate-500">
                        Practice: {stage.practice_task}
                      </p>
                    </li>
                  ))}
                </ol>
                {roadmap.content.project_idea && (
                  <div className="mt-4 rounded-lg border border-brand-100 bg-brand-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">
                      Portfolio project idea
                    </p>
                    <p className="mt-1 text-sm text-brand-900">{roadmap.content.project_idea}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
