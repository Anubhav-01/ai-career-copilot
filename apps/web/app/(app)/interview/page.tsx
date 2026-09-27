"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquareText } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { FieldError, Input, Label, Select } from "@/components/ui/input";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { formatDate, titleCase } from "@/lib/utils";
import type { Interview, InterviewDetail, Job, Resume } from "@/types/api";

const schema = z.object({
  target_role: z.string().min(2, "Target role is required").max(255),
  resume_id: z.string().optional(),
  job_id: z.string().optional(),
  difficulty: z.enum(["easy", "medium", "hard"]),
  question_count: z.coerce.number().min(3).max(15),
});

type FormValues = z.infer<typeof schema>;

const statusVariant = {
  created: "neutral",
  in_progress: "warning",
  completed: "success",
} as const;

export default function InterviewListPage() {
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: interviews, isLoading } = useQuery({
    queryKey: ["interviews"],
    queryFn: () => api<Interview[]>("/api/interviews"),
  });
  const { data: resumes } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/api/resumes"),
  });
  const { data: jobs } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => api<Job[]>("/api/jobs"),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { difficulty: "medium", question_count: 6 },
  });

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      api<InterviewDetail>("/api/interviews", {
        method: "POST",
        body: {
          ...values,
          resume_id: values.resume_id || null,
          job_id: values.job_id || null,
          mode: "mock",
        },
      }),
    onSuccess: (interview) => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      router.push(`/interview/${interview.id}`);
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Could not create interview.", "error"),
  });

  if (isLoading) return <PageSkeleton />;

  const completedResumes = resumes?.filter((r) => r.status === "completed") ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Mock Interviews</h1>
          <p className="text-sm text-slate-500">
            Questions grounded in your resume and target job — with structured
            feedback on every answer.
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>New interview</Button>
      </div>

      {!interviews || interviews.length === 0 ? (
        <EmptyState
          icon={MessageSquareText}
          title="No interviews yet"
          description="Start a mock interview. Linking a resume and a job makes the questions specific to your background."
          action={<Button onClick={() => setDialogOpen(true)}>Start your first interview</Button>}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {interviews.map((interview) => (
            <Card key={interview.id} className="flex flex-col p-5">
              <div className="flex items-start justify-between">
                <MessageSquareText className="h-8 w-8 text-brand-500" aria-hidden />
                <Badge variant={statusVariant[interview.status]}>
                  {titleCase(interview.status)}
                </Badge>
              </div>
              <h3 className="mt-3 font-semibold text-slate-900">{interview.target_role}</h3>
              <p className="text-xs text-slate-500">
                {titleCase(interview.difficulty)} · {formatDate(interview.created_at)}
              </p>
              <div className="mt-4 flex flex-1 items-end">
                <Link href={`/interview/${interview.id}`} className="w-full">
                  <Button variant="outline" size="sm" className="w-full">
                    {interview.status === "completed" ? "View report" : "Continue"}
                  </Button>
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} title="New mock interview">
        <form
          onSubmit={handleSubmit((values) => create.mutate(values))}
          className="space-y-4"
          noValidate
        >
          <div>
            <Label htmlFor="target_role">Target role</Label>
            <Input id="target_role" placeholder="e.g. Backend Engineer" {...register("target_role")} />
            <FieldError message={errors.target_role?.message} />
          </div>
          <div>
            <Label htmlFor="resume_id">Resume (recommended)</Label>
            <Select id="resume_id" {...register("resume_id")}>
              <option value="">None</option>
              {completedResumes.map((resume) => (
                <option key={resume.id} value={resume.id}>{resume.title}</option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="job_id">Target job (optional)</Label>
            <Select id="job_id" {...register("job_id")}>
              <option value="">None</option>
              {jobs?.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} {job.company ? `— ${job.company}` : ""}
                </option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="difficulty">Difficulty</Label>
              <Select id="difficulty" {...register("difficulty")}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </Select>
            </div>
            <div>
              <Label htmlFor="question_count">Questions</Label>
              <Input
                id="question_count"
                type="number"
                min={3}
                max={15}
                {...register("question_count")}
              />
              <FieldError message={errors.question_count?.message} />
            </div>
          </div>
          <Button type="submit" className="w-full" loading={create.isPending}>
            Generate questions & start
          </Button>
        </form>
      </Dialog>
    </div>
  );
}
