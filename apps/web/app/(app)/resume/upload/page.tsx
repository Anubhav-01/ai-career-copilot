"use client";

import { useMutation } from "@tanstack/react-query";
import { FileUp, UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Label } from "@/components/ui/input";
import { useToast } from "@/components/ui/toast";
import { ApiError, api } from "@/lib/api";
import type { Resume } from "@/types/api";

const MAX_SIZE_MB = 5;
const ALLOWED = [".pdf", ".docx"];

export default function ResumeUploadPage() {
  const router = useRouter();
  const { toast } = useToast();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [dragOver, setDragOver] = useState(false);

  const validate = (candidate: File): string | null => {
    const name = candidate.name.toLowerCase();
    if (!ALLOWED.some((ext) => name.endsWith(ext))) {
      return "Only PDF and DOCX files are supported.";
    }
    if (candidate.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large. Maximum is ${MAX_SIZE_MB} MB.`;
    }
    if (candidate.size === 0) return "This file is empty.";
    return null;
  };

  const selectFile = (candidate: File | null) => {
    if (!candidate) return;
    const error = validate(candidate);
    if (error) {
      toast(error, "error");
      return;
    }
    setFile(candidate);
    if (!title) setTitle(candidate.name.replace(/\.(pdf|docx)$/i, ""));
  };

  const upload = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error("No file selected");
      const formData = new FormData();
      formData.append("file", file);
      if (title) formData.append("title", title);
      return api<Resume>("/api/resumes/upload", { method: "POST", formData });
    },
    onSuccess: (resume) => {
      toast("Resume uploaded. Parsing has started.", "success");
      router.push(`/resume/${resume.id}`);
    },
    onError: (error) =>
      toast(error instanceof ApiError ? error.message : "Upload failed.", "error"),
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Upload resume</h1>
        <p className="text-sm text-slate-500">
          PDF or DOCX, up to {MAX_SIZE_MB} MB. Parsing extracts your skills,
          experience and projects, then indexes your resume for semantic matching.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Resume file</CardTitle>
          <CardDescription>
            Your file is stored privately in your account and can be deleted at any time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            role="button"
            tabIndex={0}
            aria-label="Choose a resume file"
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              selectFile(e.dataTransfer.files?.[0] ?? null);
            }}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 text-center transition-colors ${
              dragOver ? "border-brand-500 bg-brand-50" : "border-slate-300 hover:border-brand-400"
            }`}
          >
            {file ? (
              <>
                <FileUp className="h-8 w-8 text-brand-600" aria-hidden />
                <p className="mt-2 font-medium text-slate-900">{file.name}</p>
                <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(0)} KB — click to change</p>
              </>
            ) : (
              <>
                <UploadCloud className="h-8 w-8 text-slate-400" aria-hidden />
                <p className="mt-2 font-medium text-slate-700">
                  Drag & drop or click to choose a file
                </p>
                <p className="text-xs text-slate-500">PDF or DOCX, max {MAX_SIZE_MB} MB</p>
              </>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx"
              className="hidden"
              onChange={(e) => selectFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <div>
            <Label htmlFor="title">Title (optional)</Label>
            <Input
              id="title"
              value={title}
              placeholder="e.g. Backend Engineer Resume v3"
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <Button
            className="w-full"
            disabled={!file}
            loading={upload.isPending}
            onClick={() => upload.mutate()}
          >
            Upload and parse
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
