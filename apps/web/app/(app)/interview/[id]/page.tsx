"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ChevronRight, Info } from "lucide-react";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Textarea } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { PageSkeleton } from "@/components/ui/skeleton";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import { titleCase } from "@/lib/utils";
import type {
  AnswerResult,
  InterviewDetail,
  InterviewFeedback,
  InterviewQuestion,
  InterviewReport,
} from "@/types/api";

const categoryVariant: Record<string, "default" | "success" | "warning" | "danger" | "neutral"> = {
  technical: "default",
  system_design: "danger",
  behavioral: "success",
  situational: "warning",
  project: "default",
  resume: "default",
  hr: "neutral",
};

function FeedbackCard({ feedback }: { feedback: InterviewFeedback }) {
  const dimensions: [string, number][] = [
    ["Relevance", feedback.relevance],
    ["Technical", feedback.technical_correctness],
    ["Clarity", feedback.clarity],
    ["Completeness", feedback.completeness],
    ["Structure", feedback.structure],
  ];
  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <h4 className="font-semibold text-slate-900">Feedback</h4>
        <span className="text-2xl font-bold text-slate-900">
          {Math.round(feedback.score)}
          <span className="text-sm font-normal text-slate-400">/100</span>
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {dimensions.map(([label, value]) => (
          <div key={label}>
            <div className="flex justify-between text-xs text-slate-500">
              <span>{label}</span>
              <span>{Math.round(value)}</span>
            </div>
            <Progress value={value} colorByScore className="mt-1 h-1.5" />
          </div>
        ))}
      </div>
      {feedback.strengths.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Strengths</p>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-600">
            {feedback.strengths.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
      {feedback.weaknesses.length > 0 && (
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-rose-600">To improve</p>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-600">
            {feedback.weaknesses.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      )}
      {feedback.suggested_structure && (
        <p className="rounded-lg bg-white p-3 text-xs text-slate-600">
          <strong>Suggested structure:</strong> {feedback.suggested_structure}
        </p>
      )}
      {feedback.improvement_tips.length > 0 && (
        <ul className="space-y-1">
          {feedback.improvement_tips.map((tip) => (
            <li key={tip} className="flex gap-2 text-xs text-slate-600">
              <Info className="h-3.5 w-3.5 shrink-0 text-brand-500" aria-hidden />
              {tip}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ReportView({ interviewId }: { interviewId: string }) {
  const { data: report, isLoading } = useQuery({
    queryKey: ["interview-report", interviewId],
    queryFn: () => api<InterviewReport>(`/api/interviews/${interviewId}/report`),
  });

  if (isLoading || !report) return <PageSkeleton />;

  return (
    <div className="space-y-6">
      <Card className="p-6 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" aria-hidden />
        <h2 className="mt-3 text-xl font-semibold text-slate-900">Interview complete</h2>
        <p className="text-sm text-slate-500">
          You answered {report.answered} of {report.total_questions} questions.
        </p>
        <p className="mt-4 text-5xl font-bold text-slate-900">
          {Math.round(report.overall_score)}
          <span className="text-xl font-normal text-slate-400">/100</span>
        </p>
        <Progress value={report.overall_score} colorByScore className="mx-auto mt-4 h-3 max-w-md" />
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Scores by category</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(report.category_scores).map(([category, score]) => (
              <div key={category}>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">{titleCase(category)}</span>
                  <span className="font-medium">{Math.round(score)}</span>
                </div>
                <Progress value={score} colorByScore className="mt-1" />
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Takeaways</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {report.strengths.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">Strengths</p>
                <ul className="mt-1 list-inside list-disc text-slate-600">
                  {report.strengths.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            )}
            {report.weaknesses.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-600">Weaknesses</p>
                <ul className="mt-1 list-inside list-disc text-slate-600">
                  {report.weaknesses.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            )}
            {report.improvement_tips.length > 0 && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Next steps</p>
                <ul className="mt-1 list-inside list-disc text-slate-600">
                  {report.improvement_tips.map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function InterviewSessionPage() {
  const params = useParams<{ id: string }>();
  const interviewId = params.id;
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [answer, setAnswer] = useState("");
  const [lastFeedback, setLastFeedback] = useState<InterviewFeedback | null>(null);
  const [activeQuestion, setActiveQuestion] = useState<InterviewQuestion | null>(null);
  const [finished, setFinished] = useState(false);

  const { data: interview, isLoading, isError } = useQuery({
    queryKey: ["interview", interviewId],
    queryFn: () => api<InterviewDetail>(`/api/interviews/${interviewId}`),
  });

  const submit = useMutation({
    mutationFn: (questionId: string) =>
      api<AnswerResult>(`/api/interviews/${interviewId}/answer`, {
        method: "POST",
        body: { question_id: questionId, answer },
      }),
    onSuccess: (result) => {
      setLastFeedback(result.feedback);
      setAnswer("");
      setActiveQuestion(result.next_question);
      if (result.interview_completed) {
        setFinished(true);
        queryClient.invalidateQueries({ queryKey: ["interview", interviewId] });
        queryClient.invalidateQueries({ queryKey: ["interviews"] });
        queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      }
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Could not submit answer.", "error"),
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !interview) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Interview not found"
        description="It may have been deleted, or you may not have access to it."
      />
    );
  }

  if (interview.status === "completed" || finished) {
    return (
      <div className="space-y-6">
        {lastFeedback && !interview.completed_at && <FeedbackCard feedback={lastFeedback} />}
        <ReportView interviewId={interviewId} />
      </div>
    );
  }

  // Current question: follow the answer flow once started, otherwise resume
  // at the first unanswered question from the server.
  const current =
    activeQuestion ?? interview.questions.find((q) => !q.answered) ?? null;
  const currentIndex = current
    ? interview.questions.findIndex((q) => q.id === current.id)
    : 0;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">
          Mock interview — {interview.target_role}
        </h1>
        <p className="text-sm text-slate-500">
          Question {Math.max(1, currentIndex + 1)} of {interview.questions.length} ·{" "}
          {titleCase(interview.difficulty)} difficulty
        </p>
        <Progress
          value={((currentIndex) / interview.questions.length) * 100}
          className="mt-3"
        />
      </div>

      {lastFeedback && <FeedbackCard feedback={lastFeedback} />}

      {current && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Badge variant={categoryVariant[current.category] ?? "neutral"}>
                {titleCase(current.category)}
              </Badge>
              <Badge variant="neutral">{titleCase(current.difficulty)}</Badge>
            </div>
            <CardTitle className="mt-2 text-lg leading-relaxed">{current.question}</CardTitle>
            {current.grounding && (
              <CardDescription className="flex items-start gap-1.5">
                <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                Why this question: {current.grounding}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              aria-label="Your answer"
              rows={7}
              placeholder="Type your answer as you would say it out loud…"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
            />
            <div className="flex justify-end">
              <Button
                disabled={answer.trim().length === 0}
                loading={submit.isPending}
                onClick={() => submit.mutate(current.id)}
              >
                Submit answer <ChevronRight className="h-4 w-4" aria-hidden />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
