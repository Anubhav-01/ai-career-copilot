"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BrainCircuit, GraduationCap } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type { LearningRoadmap, ResumeSkill, SkillGap } from "@/types/api";

const priorityOrder: SkillGap["priority"][] = ["critical", "important", "nice_to_have"];
const priorityVariant = {
  critical: "danger",
  important: "warning",
  nice_to_have: "neutral",
} as const;

export default function SkillsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data: skills, isLoading: skillsLoading } = useQuery({
    queryKey: ["skills"],
    queryFn: () => api<ResumeSkill[]>("/api/skills"),
  });
  const { data: gaps, isLoading: gapsLoading } = useQuery({
    queryKey: ["skill-gaps"],
    queryFn: () => api<SkillGap[]>("/api/skills/gaps"),
  });

  const generateRoadmap = useMutation({
    mutationFn: (gapId: string) =>
      api<LearningRoadmap>(`/api/learning/roadmaps/${gapId}`, { method: "POST" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["roadmaps"] });
      toast("Roadmap generated — see the Learning page.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Roadmap generation failed.", "error"),
  });

  if (skillsLoading || gapsLoading) return <PageSkeleton />;

  const byCategory = new Map<string, ResumeSkill[]>();
  for (const skill of skills ?? []) {
    const key = skill.category ?? "other";
    byCategory.set(key, [...(byCategory.get(key) ?? []), skill]);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Skills & Gaps</h1>
        <p className="text-sm text-slate-500">
          Everything here is evidence-backed: skills come from your resumes, gaps come
          from real job requirements.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your skills</CardTitle>
          <CardDescription>Extracted from your uploaded resumes.</CardDescription>
        </CardHeader>
        <CardContent>
          {byCategory.size === 0 ? (
            <EmptyState
              icon={BrainCircuit}
              title="No skills yet"
              description="Upload a resume to extract your skills with supporting evidence."
              action={
                <Link href="/resume/upload">
                  <Button>Upload resume</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-4">
              {Array.from(byCategory.entries()).map(([category, items]) => (
                <div key={category}>
                  <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {titleCase(category)}
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {items.map((skill) => (
                      <Badge key={skill.normalized} title={skill.evidence ?? undefined}>
                        {skill.normalized}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Skill gaps</CardTitle>
          <CardDescription>
            From your job-vs-resume analyses. Generate a learning roadmap for any gap.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!gaps || gaps.length === 0 ? (
            <p className="text-sm text-slate-500">
              No gaps yet. Open a job (Jobs page) and run “Skill-gap analysis” after a match.
            </p>
          ) : (
            <div className="space-y-4">
              {priorityOrder.map((priority) => {
                const items = gaps.filter((gap) => gap.priority === priority);
                if (items.length === 0) return null;
                return (
                  <div key={priority}>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                      {titleCase(priority)} ({items.length})
                    </h4>
                    <div className="space-y-2">
                      {items.map((gap) => (
                        <div
                          key={gap.id}
                          className="flex flex-col gap-2 rounded-lg border border-slate-200 p-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <div className="flex items-start gap-3">
                            <Badge variant={priorityVariant[gap.priority]}>{gap.skill}</Badge>
                            {gap.reason && (
                              <p className="text-xs text-slate-500">{gap.reason}</p>
                            )}
                          </div>
                          <Button
                            variant="outline"
                            size="sm"
                            loading={generateRoadmap.isPending && generateRoadmap.variables === gap.id}
                            onClick={() => generateRoadmap.mutate(gap.id)}
                          >
                            <GraduationCap className="h-3.5 w-3.5" aria-hidden />
                            Roadmap
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
