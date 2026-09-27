"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KanbanSquare, Trash2 } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { FieldError, Input, Label, Select, Textarea } from "@/components/ui/input";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { formatDate, titleCase } from "@/lib/utils";
import type { Application, ApplicationStatus } from "@/types/api";

const STATUSES: ApplicationStatus[] = [
  "saved", "applied", "screening", "interview", "offer", "rejected", "withdrawn",
];

const statusColor: Record<ApplicationStatus, string> = {
  saved: "bg-slate-100 text-slate-700",
  applied: "bg-brand-50 text-brand-700",
  screening: "bg-amber-50 text-amber-700",
  interview: "bg-violet-50 text-violet-700",
  offer: "bg-emerald-50 text-emerald-700",
  rejected: "bg-rose-50 text-rose-700",
  withdrawn: "bg-slate-100 text-slate-500",
};

const schema = z.object({
  company: z.string().min(1, "Company is required").max(255),
  job_title: z.string().min(1, "Job title is required").max(255),
  job_url: z.string().url("Must be a valid URL").optional().or(z.literal("")),
  location: z.string().max(255).optional(),
  salary: z.string().max(100).optional(),
  status: z.enum(["saved", "applied", "screening", "interview", "offer", "rejected", "withdrawn"]),
  notes: z.string().max(10000).optional(),
});

type FormValues = z.infer<typeof schema>;

export default function ApplicationsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data: applications, isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: () => api<Application[]>("/api/applications"),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { status: "saved" },
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["applications"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const create = useMutation({
    mutationFn: (values: FormValues) =>
      api<Application>("/api/applications", {
        method: "POST",
        body: { ...values, job_url: values.job_url || null },
      }),
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      reset({ status: "saved" });
      toast("Application added.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Could not add application.", "error"),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: string; status: ApplicationStatus }) =>
      api<Application>(`/api/applications/${id}`, { method: "PUT", body: { status } }),
    onSuccess: invalidate,
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Update failed.", "error"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api(`/api/applications/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      invalidate();
      toast("Application deleted.", "success");
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Delete failed.", "error"),
  });

  if (isLoading) return <PageSkeleton />;

  const counts = STATUSES.map((status) => ({
    status,
    count: applications?.filter((a) => a.status === status).length ?? 0,
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Applications</h1>
          <p className="text-sm text-slate-500">Track every application from saved to offer.</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>Add application</Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {counts.map(({ status, count }) => (
          <span
            key={status}
            className={`rounded-full px-3 py-1 text-xs font-medium ${statusColor[status]}`}
          >
            {titleCase(status)}: {count}
          </span>
        ))}
      </div>

      {!applications || applications.length === 0 ? (
        <EmptyState
          icon={KanbanSquare}
          title="No applications tracked yet"
          description="Add the jobs you have saved or applied to, and keep your entire pipeline in one place."
          action={<Button onClick={() => setDialogOpen(true)}>Add your first application</Button>}
        />
      ) : (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-400">
                <th className="px-4 py-3 font-medium">Company</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Location</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Added</th>
                <th className="px-4 py-3 font-medium sr-only">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {applications.map((application) => (
                <tr key={application.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">
                    {application.job_url ? (
                      <a
                        href={application.job_url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-brand-600 hover:underline"
                      >
                        {application.company}
                      </a>
                    ) : (
                      application.company
                    )}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{application.job_title}</td>
                  <td className="px-4 py-3 text-slate-500">{application.location ?? "—"}</td>
                  <td className="px-4 py-3">
                    <select
                      aria-label={`Status for ${application.company}`}
                      className={`rounded-full border-0 px-2.5 py-1 text-xs font-medium ${statusColor[application.status]}`}
                      value={application.status}
                      onChange={(e) =>
                        updateStatus.mutate({
                          id: application.id,
                          status: e.target.value as ApplicationStatus,
                        })
                      }
                    >
                      {STATUSES.map((status) => (
                        <option key={status} value={status}>{titleCase(status)}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-slate-500">{formatDate(application.created_at)}</td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={`Delete application at ${application.company}`}
                      onClick={() => {
                        if (window.confirm("Delete this application?")) {
                          remove.mutate(application.id);
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4 text-slate-400" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} title="Add application">
        <form onSubmit={handleSubmit((values) => create.mutate(values))} className="space-y-4" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="company">Company</Label>
              <Input id="company" {...register("company")} />
              <FieldError message={errors.company?.message} />
            </div>
            <div>
              <Label htmlFor="job_title">Job title</Label>
              <Input id="job_title" {...register("job_title")} />
              <FieldError message={errors.job_title?.message} />
            </div>
            <div>
              <Label htmlFor="location">Location</Label>
              <Input id="location" {...register("location")} />
            </div>
            <div>
              <Label htmlFor="salary">Salary (optional)</Label>
              <Input id="salary" placeholder="e.g. $90k–110k" {...register("salary")} />
            </div>
            <div className="col-span-2">
              <Label htmlFor="job_url">Job URL</Label>
              <Input id="job_url" placeholder="https://…" {...register("job_url")} />
              <FieldError message={errors.job_url?.message} />
            </div>
            <div className="col-span-2">
              <Label htmlFor="status">Status</Label>
              <Select id="status" {...register("status")}>
                {STATUSES.map((status) => (
                  <option key={status} value={status}>{titleCase(status)}</option>
                ))}
              </Select>
            </div>
            <div className="col-span-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" rows={3} {...register("notes")} />
            </div>
          </div>
          <Button type="submit" className="w-full" loading={create.isPending}>
            Add application
          </Button>
        </form>
      </Dialog>
    </div>
  );
}
