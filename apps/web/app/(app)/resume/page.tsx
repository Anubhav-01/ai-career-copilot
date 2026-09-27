"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileText, Trash2 } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { Resume } from "@/types/api";

const statusVariant: Record<Resume["status"], "success" | "warning" | "danger" | "neutral"> = {
  completed: "success",
  processing: "warning",
  pending: "warning",
  failed: "danger",
};

export default function ResumeListPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const { data: resumes, isLoading } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/api/resumes"),
    refetchInterval: (query) =>
      query.state.data?.some((r) => r.status === "pending" || r.status === "processing")
        ? 2000
        : false,
  });

  const deleteResume = useMutation({
    mutationFn: (id: string) => api(`/api/resumes/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resumes"] });
      toast("Resume deleted.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Delete failed.", "error"),
  });

  if (isLoading) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Resumes</h1>
          <p className="text-sm text-slate-500">
            Upload, analyze and improve your resumes.
          </p>
        </div>
        <Link href="/resume/upload">
          <Button>Upload resume</Button>
        </Link>
      </div>

      {!resumes || resumes.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No resumes yet"
          description="Upload a PDF or DOCX resume to get your AI analysis, skills extraction and ATS-style checks."
          action={
            <Link href="/resume/upload">
              <Button>Upload your first resume</Button>
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {resumes.map((resume) => (
            <Card key={resume.id} className="flex flex-col p-5">
              <div className="flex items-start justify-between">
                <FileText className="h-8 w-8 text-brand-500" aria-hidden />
                <Badge variant={statusVariant[resume.status]}>{resume.status}</Badge>
              </div>
              <h3 className="mt-3 font-semibold text-slate-900">{resume.title}</h3>
              <p className="text-xs text-slate-500">
                {resume.original_filename} · {formatDate(resume.created_at)}
              </p>
              {resume.status === "failed" && resume.error_message && (
                <p className="mt-2 text-xs text-rose-600">{resume.error_message}</p>
              )}
              <div className="mt-4 flex flex-1 items-end justify-between gap-2">
                <Link href={`/resume/${resume.id}`} className="flex-1">
                  <Button variant="outline" className="w-full" size="sm">
                    Open
                  </Button>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Delete ${resume.title}`}
                  onClick={() => {
                    if (window.confirm("Delete this resume and its analyses?")) {
                      deleteResume.mutate(resume.id);
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
