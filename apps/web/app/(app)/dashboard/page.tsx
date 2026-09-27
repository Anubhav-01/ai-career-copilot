"use client";

import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  FileText,
  GitCompareArrows,
  KanbanSquare,
  Target,
} from "lucide-react";
import Link from "next/link";

import { DistributionBarChart, ScoreLineChart } from "@/components/charts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Progress } from "@/components/ui/progress";
import { PageSkeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type { Dashboard } from "@/types/api";

export default function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/api/dashboard"),
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Could not load your dashboard"
        description="The API may be unavailable. Please try again in a moment."
      />
    );
  }

  const isEmpty = data.resume_count === 0;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Career Dashboard</h1>
          <p className="text-sm text-slate-500">
            Your resume health, job matches and interview progress at a glance.
          </p>
        </div>
        <Link href="/resume/upload">
          <Button>Upload resume</Button>
        </Link>
      </div>

      {isEmpty ? (
        <EmptyState
          icon={FileText}
          title="Start by uploading your resume"
          description="Resume analysis unlocks job matching, skill-gap analysis and grounded interview prep."
          action={
            <Link href="/resume/upload">
              <Button>Upload your first resume</Button>
            </Link>
          }
        />
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">Resume score</p>
                <BarChart3 className="h-4 w-4 text-slate-400" aria-hidden />
              </div>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {data.latest_resume_score !== null ? `${Math.round(data.latest_resume_score)}/100` : "Not analyzed"}
              </p>
              {data.latest_resume_score !== null && (
                <Progress value={data.latest_resume_score} colorByScore className="mt-3" />
              )}
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">Profile completeness</p>
                <Target className="h-4 w-4 text-slate-400" aria-hidden />
              </div>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {Math.round(data.profile_completeness)}%
              </p>
              <Progress value={data.profile_completeness} className="mt-3" />
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">Best job match</p>
                <GitCompareArrows className="h-4 w-4 text-slate-400" aria-hidden />
              </div>
              <p className="mt-2 text-2xl font-semibold text-slate-900">
                {data.best_match_score !== null ? `${Math.round(data.best_match_score)}%` : "—"}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                {data.match_count} match{data.match_count === 1 ? "" : "es"} across {data.job_count} job{data.job_count === 1 ? "" : "s"}
              </p>
            </Card>
            <Card className="p-5">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-slate-500">Applications</p>
                <KanbanSquare className="h-4 w-4 text-slate-400" aria-hidden />
              </div>
              <p className="mt-2 text-2xl font-semibold text-slate-900">{data.application_count}</p>
              <p className="mt-1 text-xs text-slate-500">{data.skill_gap_count} open skill gaps</p>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Resume score over time</CardTitle>
              </CardHeader>
              <CardContent>
                {data.score_history.length > 0 ? (
                  <ScoreLineChart data={data.score_history} />
                ) : (
                  <p className="py-12 text-center text-sm text-slate-500">
                    Run a resume analysis to start tracking your score.
                  </p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Job match distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {data.match_distribution.length > 0 ? (
                  <DistributionBarChart data={data.match_distribution} xKey="bucket" yKey="count" />
                ) : (
                  <p className="py-12 text-center text-sm text-slate-500">
                    Analyze a job and run a match to see your distribution.
                  </p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Application funnel</CardTitle>
              </CardHeader>
              <CardContent>
                <DistributionBarChart
                  data={data.application_funnel.map((f) => ({ ...f, status: titleCase(f.status) }))}
                  xKey="status"
                  yKey="count"
                />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Interview performance</CardTitle>
              </CardHeader>
              <CardContent>
                {data.interview_performance.length > 0 ? (
                  <ScoreLineChart data={data.interview_performance} />
                ) : (
                  <p className="py-12 text-center text-sm text-slate-500">
                    Complete a mock interview to track your performance.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Top skills</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {data.top_skills.length > 0 ? (
                  data.top_skills.map((s) => (
                    <Badge key={s.skill} variant="default">
                      {s.skill}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No skills extracted yet.</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Critical skill gaps</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {data.top_gaps.length > 0 ? (
                  data.top_gaps.map((gap) => (
                    <Badge key={gap} variant="danger">
                      {gap}
                    </Badge>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">
                    No critical gaps found. Run a skill-gap analysis from a job page.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
