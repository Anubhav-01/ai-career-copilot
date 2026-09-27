"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useParams } from "next/navigation";

import { MatchPanel } from "@/components/jobs/match-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { JobDetail } from "@/types/api";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const jobId = params.id;

  const { data: job, isLoading, isError } = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => api<JobDetail>(`/api/jobs/${jobId}`),
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !job) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Job not found"
        description="It may have been deleted, or you may not have access to it."
      />
    );
  }

  const analysis = job.analysis;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{job.title}</h1>
        <p className="text-sm text-slate-500">
          {job.company ?? "Unknown company"}
          {job.location ? ` · ${job.location}` : ""}
          {analysis?.seniority ? ` · ${analysis.seniority}` : ""}
          {analysis?.experience_years_min != null
            ? ` · ${analysis.experience_years_min}+ years`
            : ""}
        </p>
      </div>

      <Tabs defaultValue="match">
        <TabsList>
          <TabsTrigger value="match">Match & gaps</TabsTrigger>
          <TabsTrigger value="analysis">Extracted requirements</TabsTrigger>
          <TabsTrigger value="description">Full description</TabsTrigger>
        </TabsList>

        <TabsContent value="match">
          <MatchPanel jobId={jobId} />
        </TabsContent>

        <TabsContent value="analysis">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Required skills</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-1.5">
                {analysis?.required_skills.length ? (
                  analysis.required_skills.map((skill) => (
                    <Badge key={skill} variant="danger">{skill}</Badge>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">None detected.</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Preferred skills</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-1.5">
                {analysis?.preferred_skills.length ? (
                  analysis.preferred_skills.map((skill) => (
                    <Badge key={skill} variant="warning">{skill}</Badge>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">None detected.</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Responsibilities</CardTitle>
              </CardHeader>
              <CardContent>
                {analysis?.responsibilities.length ? (
                  <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
                    {analysis.responsibilities.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">None detected.</p>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Keywords & education</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-1.5">
                  {analysis?.keywords.map((keyword) => (
                    <Badge key={keyword} variant="neutral">{keyword}</Badge>
                  ))}
                </div>
                {analysis?.education.length ? (
                  <ul className="list-inside list-disc space-y-1 text-sm text-slate-600">
                    {analysis.education.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                ) : null}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="description">
          <Card>
            <CardContent className="pt-5">
              <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-700">
                {job.description_text}
              </pre>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
