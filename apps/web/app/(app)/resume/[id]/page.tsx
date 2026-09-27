"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, Loader2 } from "lucide-react";
import { useParams } from "next/navigation";

import { AnalysisPanel } from "@/components/resume/analysis-panel";
import { ImprovePanel } from "@/components/resume/improve-panel";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type { ResumeDetail } from "@/types/api";

export default function ResumeDetailPage() {
  const params = useParams<{ id: string }>();
  const resumeId = params.id;

  const { data: resume, isLoading, isError } = useQuery({
    queryKey: ["resume", resumeId],
    queryFn: () => api<ResumeDetail>(`/api/resumes/${resumeId}`),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "pending" || status === "processing" ? 2000 : false;
    },
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !resume) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Resume not found"
        description="It may have been deleted, or you may not have access to it."
      />
    );
  }

  if (resume.status === "pending" || resume.status === "processing") {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <Loader2 className="h-8 w-8 animate-spin text-brand-500" aria-hidden />
        <h1 className="mt-4 text-lg font-semibold text-slate-900">
          Parsing your resume…
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Extracting text, detecting skills and indexing for semantic search. This
          usually takes a few seconds.
        </p>
      </div>
    );
  }

  if (resume.status === "failed") {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Processing failed"
        description={resume.error_message ?? "We could not process this file. Try a different export."}
      />
    );
  }

  const parsed = resume.parsed;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{resume.title}</h1>
        <p className="text-sm text-slate-500">
          {resume.original_filename} · {resume.skills.length} skills detected
        </p>
      </div>

      <Tabs defaultValue="analysis">
        <TabsList>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="content">Parsed content</TabsTrigger>
          <TabsTrigger value="skills">Skills & evidence</TabsTrigger>
          <TabsTrigger value="improve">Improve</TabsTrigger>
        </TabsList>

        <TabsContent value="analysis">
          <AnalysisPanel resumeId={resumeId} />
        </TabsContent>

        <TabsContent value="content">
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Contact & summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p><span className="text-slate-500">Name:</span> {parsed?.name ?? "—"}</p>
                <p><span className="text-slate-500">Email:</span> {parsed?.email ?? "—"}</p>
                <p><span className="text-slate-500">Phone:</span> {parsed?.phone ?? "—"}</p>
                <p><span className="text-slate-500">Location:</span> {parsed?.location ?? "—"}</p>
                {parsed?.links && parsed.links.length > 0 && (
                  <p className="break-all">
                    <span className="text-slate-500">Links:</span> {parsed.links.join(", ")}
                  </p>
                )}
                {parsed?.summary && (
                  <p className="rounded-lg bg-slate-50 p-3 text-slate-600">{parsed.summary}</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Education & certifications</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {parsed?.education.length ? (
                  parsed.education.map((item, index) => (
                    <div key={index}>
                      <p className="font-medium text-slate-900">{item.degree || "Degree"}</p>
                      <p className="text-slate-500">
                        {item.institution}
                        {item.end_year ? ` · ${item.start_year ?? "?"}–${item.end_year}` : ""}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-500">No education entries detected.</p>
                )}
                {parsed?.certifications.length ? (
                  <div className="flex flex-wrap gap-1.5 pt-2">
                    {parsed.certifications.map((cert) => (
                      <Badge key={cert} variant="neutral">{cert}</Badge>
                    ))}
                  </div>
                ) : null}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Experience</CardTitle>
              </CardHeader>
              <CardContent className="space-y-5">
                {parsed?.experience.length ? (
                  parsed.experience.map((item, index) => (
                    <div key={index} className="border-l-2 border-brand-200 pl-4">
                      <p className="font-medium text-slate-900">
                        {item.title || "Role"}{item.company ? ` · ${item.company}` : ""}
                      </p>
                      <p className="text-xs text-slate-500">
                        {item.start_date ?? "?"} – {item.end_date ?? "present"}
                      </p>
                      <ul className="mt-2 list-inside list-disc space-y-1 text-sm text-slate-600">
                        {item.bullets.map((bullet, i) => (
                          <li key={i}>{bullet}</li>
                        ))}
                      </ul>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No structured experience detected.</p>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Projects</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                {parsed?.projects.length ? (
                  parsed.projects.map((project, index) => (
                    <div key={index} className="rounded-lg border border-slate-200 p-4">
                      <p className="font-medium text-slate-900">{project.name}</p>
                      <p className="mt-1 text-sm text-slate-600">{project.description}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {project.technologies.map((tech) => (
                          <Badge key={tech} variant="neutral">{tech}</Badge>
                        ))}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500">No projects detected.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="skills">
          <Card>
            <CardHeader>
              <CardTitle>Detected skills with evidence</CardTitle>
            </CardHeader>
            <CardContent>
              {resume.skills.length === 0 ? (
                <p className="text-sm text-slate-500">No recognizable skills detected.</p>
              ) : (
                <div className="divide-y divide-slate-100">
                  {resume.skills.map((skill) => (
                    <div key={skill.normalized} className="flex flex-col gap-1 py-3 sm:flex-row sm:items-start sm:gap-4">
                      <div className="flex w-48 shrink-0 items-center gap-2">
                        <Badge>{skill.normalized}</Badge>
                        {skill.category && (
                          <span className="text-xs text-slate-400">{titleCase(skill.category)}</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-600">
                        {skill.evidence ? `“${skill.evidence}”` : "—"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="improve">
          <ImprovePanel resumeId={resumeId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
