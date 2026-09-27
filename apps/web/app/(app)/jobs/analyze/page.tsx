"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { FieldError, Input, Label, Textarea } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import type { JobDetail } from "@/types/api";

const schema = z.object({
  title: z.string().max(255).optional(),
  company: z.string().max(255).optional(),
  location: z.string().max(255).optional(),
  source_url: z.string().url("Must be a valid URL").max(1000).optional().or(z.literal("")),
  description: z
    .string()
    .min(100, "Please paste the full job description (at least 100 characters)")
    .max(50000),
});

type FormValues = z.infer<typeof schema>;

export default function JobAnalyzePage() {
  const router = useRouter();
  const { toast } = useToast();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = async (values: FormValues) => {
    try {
      const job = await api<JobDetail>("/api/jobs/analyze", {
        method: "POST",
        body: { ...values, source_url: values.source_url || undefined },
      });
      toast("Job analyzed.", "success");
      router.push(`/jobs/${job.id}`);
    } catch (error) {
      toast(error instanceof ApiError ? error.message : "Analysis failed.", "error");
    }
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Analyze a job description</h1>
        <p className="text-sm text-slate-500">
          Required/preferred skills, keywords and requirements are extracted with a
          hybrid rule-based + AI pipeline, then indexed for semantic matching.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job details</CardTitle>
          <CardDescription>Title and company are optional — they are also detected from the text.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="title">Job title</Label>
                <Input id="title" placeholder="Backend Engineer" {...register("title")} />
                <FieldError message={errors.title?.message} />
              </div>
              <div>
                <Label htmlFor="company">Company</Label>
                <Input id="company" placeholder="Acme Inc." {...register("company")} />
                <FieldError message={errors.company?.message} />
              </div>
              <div>
                <Label htmlFor="location">Location</Label>
                <Input id="location" placeholder="Remote / Berlin" {...register("location")} />
              </div>
              <div>
                <Label htmlFor="source_url">Job URL</Label>
                <Input id="source_url" placeholder="https://…" {...register("source_url")} />
                <FieldError message={errors.source_url?.message} />
              </div>
            </div>
            <div>
              <Label htmlFor="description">Job description</Label>
              <Textarea
                id="description"
                rows={12}
                placeholder="Paste the full job description here…"
                {...register("description")}
              />
              <FieldError message={errors.description?.message} />
            </div>
            <Button type="submit" className="w-full" loading={isSubmitting}>
              Analyze job
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
