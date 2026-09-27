"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Lightbulb, Wand2 } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label, Select, Textarea } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import type { BulletImprovement, Job, TailoringSuggestion } from "@/types/api";

export function ImprovePanel({ resumeId }: { resumeId: string }) {
  const { toast } = useToast();
  const [bullet, setBullet] = useState("");
  const [selectedJob, setSelectedJob] = useState("");

  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api<Job[]>("/api/jobs"),
  });

  const improve = useMutation({
    mutationFn: () =>
      api<BulletImprovement>(`/api/resumes/${resumeId}/improve-bullet`, {
        method: "POST",
        body: { bullet: bullet.trim() },
      }),
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Improvement failed.", "error"),
  });

  const tailor = useMutation({
    mutationFn: () =>
      api<TailoringSuggestion>(`/api/resumes/${resumeId}/tailor/${selectedJob}`, {
        method: "POST",
      }),
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Tailoring failed.", "error"),
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="h-4 w-4 text-brand-500" aria-hidden />
            Improve a bullet
          </CardTitle>
          <CardDescription>
            Paste a bullet exactly as it appears on this resume. The rewrite keeps
            every fact identical — if a metric is missing, you get a suggestion for
            where to add a real one, never an invented number.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <Textarea
            aria-label="Resume bullet to improve"
            placeholder='e.g. "Built REST APIs using FastAPI serving 10k requests per day"'
            value={bullet}
            onChange={(e) => setBullet(e.target.value)}
          />
          <Button
            disabled={bullet.trim().length < 5}
            loading={improve.isPending}
            onClick={() => improve.mutate()}
          >
            Improve bullet
          </Button>

          {improve.data && (
            <div className="space-y-3 rounded-lg border border-slate-200 p-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Original</p>
                <p className="mt-1 text-sm text-slate-600">{improve.data.original}</p>
              </div>
              <div className="flex items-center gap-2 text-brand-500">
                <ArrowRight className="h-4 w-4" aria-hidden />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Improved</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{improve.data.improved}</p>
              </div>
              <p className="text-xs text-slate-500">{improve.data.rationale}</p>
              {improve.data.missing_metric_suggestion && (
                <p className="flex gap-2 rounded-md bg-amber-50 p-3 text-xs text-amber-800">
                  <Lightbulb className="h-4 w-4 shrink-0" aria-hidden />
                  {improve.data.missing_metric_suggestion}
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tailor for a job</CardTitle>
          <CardDescription>
            Get job-specific suggestions: what to emphasize, truthful keywords to add,
            and requirements where your resume lacks evidence. Nothing is fabricated.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {!jobs || jobs.length === 0 ? (
            <p className="text-sm text-slate-500">
              Analyze a job first (Jobs → Analyze) to enable tailoring.
            </p>
          ) : (
            <>
              <div>
                <Label htmlFor="tailor-job">Target job</Label>
                <Select
                  id="tailor-job"
                  value={selectedJob}
                  onChange={(e) => setSelectedJob(e.target.value)}
                >
                  <option value="">Select a job…</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} {job.company ? `— ${job.company}` : ""}
                    </option>
                  ))}
                </Select>
              </div>
              <Button
                disabled={!selectedJob}
                loading={tailor.isPending}
                onClick={() => tailor.mutate()}
              >
                Get tailoring suggestions
              </Button>
            </>
          )}

          {tailor.data && (
            <div className="space-y-4 rounded-lg border border-slate-200 p-4">
              {tailor.data.summary && (
                <p className="text-sm font-medium text-slate-900">{tailor.data.summary}</p>
              )}
              {tailor.data.skills_to_emphasize.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Skills to emphasize
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {tailor.data.skills_to_emphasize.map((skill) => (
                      <Badge key={skill} variant="success">{skill}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {tailor.data.keywords_to_include.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Keywords to include (if truthful)
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {tailor.data.keywords_to_include.map((keyword) => (
                      <Badge key={keyword}>{keyword}</Badge>
                    ))}
                  </div>
                </div>
              )}
              {tailor.data.bullets_to_improve.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Bullets worth strengthening
                  </p>
                  <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600">
                    {tailor.data.bullets_to_improve.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}
              {tailor.data.missing_evidence.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
                    Missing evidence
                  </p>
                  <ul className="mt-2 space-y-1.5">
                    {tailor.data.missing_evidence.map((item) => (
                      <li key={item} className="rounded-md bg-amber-50 p-2 text-xs text-amber-800">
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
