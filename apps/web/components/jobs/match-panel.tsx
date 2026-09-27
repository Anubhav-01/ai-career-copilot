"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Info } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label, Select } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type { Match, Resume, SkillGap } from "@/types/api";

const componentLabels: Record<string, string> = {
  semantic: "Semantic similarity",
  required_skills: "Required skills",
  preferred_skills: "Preferred skills",
  experience: "Experience fit",
  education: "Education fit",
  keywords: "Keyword overlap",
};

const gapVariant: Record<SkillGap["priority"], "danger" | "warning" | "neutral"> = {
  critical: "danger",
  important: "warning",
  nice_to_have: "neutral",
};

export function MatchPanel({ jobId }: { jobId: string }) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [resumeId, setResumeId] = useState("");
  const [match, setMatch] = useState<Match | null>(null);
  const [gaps, setGaps] = useState<SkillGap[] | null>(null);

  const { data: resumes } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/api/resumes"),
  });
  const completedResumes = resumes?.filter((r) => r.status === "completed") ?? [];

  const runMatch = useMutation({
    mutationFn: () =>
      api<Match>(`/api/jobs/${jobId}/match`, {
        method: "POST",
        body: { resume_id: resumeId },
      }),
    onSuccess: (result) => {
      setMatch(result);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Match failed.", "error"),
  });

  const runGaps = useMutation({
    mutationFn: () =>
      api<SkillGap[]>(`/api/skills/gaps/${resumeId}/${jobId}`, { method: "POST" }),
    onSuccess: (result) => {
      setGaps(result);
      queryClient.invalidateQueries({ queryKey: ["skill-gaps"] });
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Gap analysis failed.", "error"),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Match against your resume</CardTitle>
          <CardDescription>
            Hybrid score: 40% semantic similarity (embeddings), 25% required skills,
            15% preferred skills, 10% experience, 5% education, 5% keywords.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {completedResumes.length === 0 ? (
            <p className="text-sm text-slate-500">
              Upload and process a resume first to run a match.
            </p>
          ) : (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="flex-1">
                <Label htmlFor="match-resume">Resume</Label>
                <Select
                  id="match-resume"
                  value={resumeId}
                  onChange={(e) => setResumeId(e.target.value)}
                >
                  <option value="">Select a resume…</option>
                  {completedResumes.map((resume) => (
                    <option key={resume.id} value={resume.id}>
                      {resume.title}
                    </option>
                  ))}
                </Select>
              </div>
              <Button
                disabled={!resumeId}
                loading={runMatch.isPending}
                onClick={() => runMatch.mutate()}
              >
                Run match
              </Button>
            </div>
          )}

          {match && (
            <div className="space-y-5 pt-2">
              <div className="rounded-xl border border-slate-200 p-5">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Overall match</p>
                    <p className="text-4xl font-bold text-slate-900">
                      {Math.round(match.overall_score)}%
                    </p>
                  </div>
                </div>
                <Progress value={match.overall_score} colorByScore className="mt-3 h-3" />
                {match.explanation && (
                  <p className="mt-3 flex gap-2 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
                    <Info className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" aria-hidden />
                    {match.explanation}
                  </p>
                )}
              </div>

              <div>
                <h4 className="mb-3 text-sm font-semibold text-slate-900">Why this score?</h4>
                <div className="space-y-3">
                  {Object.entries(match.components).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">
                          {componentLabels[key] ?? titleCase(key)}{" "}
                          <span className="text-xs text-slate-400">
                            ({Math.round((match.weights[key] ?? 0) * 100)}%)
                          </span>
                        </span>
                        <span className="font-medium text-slate-900">{Math.round(value)}</span>
                      </div>
                      <Progress value={value} colorByScore className="mt-1" />
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-3">
                <div>
                  <h4 className="text-sm font-semibold text-emerald-700">Strong matches</h4>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {match.strong_matches.length ? (
                      match.strong_matches.map((skill) => (
                        <Badge key={skill} variant="success">{skill}</Badge>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">None</p>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-amber-700">Partial matches</h4>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {match.partial_matches.length ? (
                      match.partial_matches.map((skill) => (
                        <Badge key={skill} variant="warning">{skill}</Badge>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">None</p>
                    )}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-rose-700">Missing skills</h4>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {match.missing_skills.length ? (
                      match.missing_skills.map((skill) => (
                        <Badge key={skill} variant="danger">{skill}</Badge>
                      ))
                    ) : (
                      <p className="text-xs text-slate-500">None 🎉</p>
                    )}
                  </div>
                </div>
              </div>

              {match.evidence.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-900">Evidence from your resume</h4>
                  <div className="mt-2 space-y-2">
                    {match.evidence.slice(0, 6).map((item) => (
                      <div key={item.skill} className="rounded-lg border border-slate-200 p-3">
                        <Badge variant="success">{item.skill}</Badge>
                        <p className="mt-1.5 text-xs text-slate-600">“{item.evidence}”</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="border-t border-slate-100 pt-4">
                <Button
                  variant="outline"
                  loading={runGaps.isPending}
                  onClick={() => runGaps.mutate()}
                >
                  Run skill-gap analysis
                </Button>
                {gaps && (
                  <div className="mt-4 space-y-2">
                    {gaps.length === 0 ? (
                      <p className="text-sm text-emerald-600">
                        No gaps — your resume covers every listed skill.
                      </p>
                    ) : (
                      gaps.map((gap) => (
                        <div key={gap.id} className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                          <Badge variant={gapVariant[gap.priority]}>
                            {titleCase(gap.priority)}
                          </Badge>
                          <div>
                            <p className="text-sm font-medium text-slate-900">{gap.skill}</p>
                            {gap.reason && <p className="text-xs text-slate-500">{gap.reason}</p>}
                          </div>
                        </div>
                      ))
                    )}
                    {gaps.length > 0 && (
                      <p className="text-xs text-slate-500">
                        Generate learning roadmaps for these gaps on the{" "}
                        <a href="/skills" className="text-brand-600 underline">Skills & Gaps</a> page.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
