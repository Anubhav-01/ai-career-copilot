"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Trash2 } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Job } from "@/types/api";

export default function JobsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api<Job[]>("/api/jobs"),
  });

  const deleteJob = useMutation({
    mutationFn: (id: string) => api(`/api/jobs/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      toast("Job deleted.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Delete failed.", "error"),
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Jobs</h1>
          <p className="text-sm text-slate-500">
            Analyzed job descriptions, ready for semantic matching.
          </p>
        </div>
        <Link href="/jobs/analyze">
          <Button>Analyze a job</Button>
        </Link>
      </div>

      {!jobs || jobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No jobs analyzed yet"
          description="Paste a job description to extract its required skills, keywords and requirements — then match it against your resume."
          action={
            <Link href="/jobs/analyze">
              <Button>Analyze your first job</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <Card key={job.id} className="flex flex-col p-5">
              <Briefcase className="h-8 w-8 text-brand-500" aria-hidden />
              <h3 className="mt-3 font-semibold text-slate-900">{job.title}</h3>
              <p className="text-xs text-slate-500">
                {job.company ?? "Unknown company"}
                {job.location ? ` · ${job.location}` : ""} · {formatDate(job.created_at)}
              </p>
              <div className="mt-4 flex flex-1 items-end justify-between gap-2">
                <Link href={`/jobs/${job.id}`} className="flex-1">
                  <Button variant="outline" size="sm" className="w-full">
                    Open
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Delete ${job.title}`}
                  onClick={() => {
                    if (window.confirm("Delete this job and its matches?")) {
                      deleteJob.mutate(job.id);
                    }
                  }}
                >
                  <Trash2 className="h-4 w-4 text-slate-400" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
