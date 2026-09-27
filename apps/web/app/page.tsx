import {
  ArrowRight,
  BarChart3,
  Bot,
  BrainCircuit,
  FileSearch,
  GitCompareArrows,
  KanbanSquare,
  Layers,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import Link from "next/link";

const features = [
  {
    icon: FileSearch,
    title: "AI Resume Analysis",
    description:
      "Upload a PDF or DOCX and get a transparent, weighted score: ATS-style checks, skills, experience quality, projects, keywords and structure — with an explanation for every number.",
  },
  {
    icon: GitCompareArrows,
    title: "Semantic Job Matching",
    description:
      "A hybrid engine blends vector-embedding similarity with skill coverage, experience and education fit. Every match shows strong, partial and missing skills with resume evidence.",
  },
  {
    icon: Target,
    title: "Skill Gap Analysis",
    description:
      "Gaps are categorized as critical, important or nice-to-have — derived only from skills you actually demonstrate, never guessed.",
  },
  {
    icon: BrainCircuit,
    title: "Learning Roadmaps",
    description:
      "Week-by-week plans for each gap, tailored to what you already know, with practice tasks and a portfolio project idea.",
  },
  {
    icon: MessageSquareText,
    title: "Mock Interviews",
    description:
      "Questions grounded in your real resume and target job. Answer in your own words and get structured feedback on relevance, clarity, completeness and structure.",
  },
  {
    icon: KanbanSquare,
    title: "Application Tracking",
    description:
      "Track every application from saved to offer, and see your funnel, match distribution and interview performance on one dashboard.",
  },
];

const steps = [
  { step: "1", title: "Upload your resume", text: "PDF or DOCX. Parsing combines deterministic extraction with schema-validated AI refinement." },
  { step: "2", title: "Add a job description", text: "Paste any posting. Required and preferred skills, keywords and requirements are extracted automatically." },
  { step: "3", title: "See explainable matches", text: "Hybrid semantic + skill scoring tells you exactly why a job fits — and what's missing." },
  { step: "4", title: "Close the gap", text: "Learning roadmaps, targeted resume improvements and grounded mock interviews get you ready." },
];

const faqs = [
  {
    q: "Is the ATS score a real ATS?",
    a: "No. It is an ATS-style heuristic analysis (sections, keywords, action verbs, quantified impact) built for guidance. We say so openly instead of pretending otherwise.",
  },
  {
    q: "Will the AI invent things on my resume?",
    a: "No. Extracted skills and experience are cross-checked against your resume text and anything unsupported is dropped. Improvement suggestions never add metrics or technologies you didn't state.",
  },
  {
    q: "Where is my data stored?",
    a: "In your own account, isolated per user. You can delete individual resumes or your whole account — deletion removes files, parsed data and embeddings.",
  },
  {
    q: "What powers the semantic search?",
    a: "Sentence-transformer embeddings stored in PostgreSQL with pgvector, retrieved with cosine distance and combined with deterministic skill matching.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
        <nav className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
            <Sparkles className="h-5 w-5 text-brand-600" aria-hidden />
            AI Career Copilot
          </Link>
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900"
            >
              Log in
            </Link>
            <Link
              href="/auth/register"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
            >
              Get started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-4 pb-20 pt-24 text-center">
        <p className="mx-auto mb-4 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
          <Bot className="h-3.5 w-3.5" aria-hidden />
          Your AI-powered personal career assistant
        </p>
        <h1 className="mx-auto max-w-3xl text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
          Your AI Career Copilot
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600">
          Analyze your resume, discover your skill gaps, match with opportunities, and
          prepare for interviews with AI.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/auth/register"
            className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 text-base font-medium text-white shadow-sm hover:bg-brand-700"
          >
            Analyze my resume <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
          <Link
            href="#how-it-works"
            className="rounded-lg border border-slate-300 px-6 py-3 text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            How it works
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="border-t border-slate-100 bg-slate-50 py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-3xl font-bold text-slate-900">How it works</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-4">
            {steps.map((item) => (
              <div key={item.step} className="relative rounded-xl border border-slate-200 bg-white p-6">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
                  {item.step}
                </span>
                <h3 className="mt-4 font-semibold text-slate-900">{item.title}</h3>
                <p className="mt-2 text-sm text-slate-600">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-3xl font-bold text-slate-900">
            One platform for the whole job search
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-slate-600">
            Resume analysis, ATS-style checks, job matching, skill gaps, resume
            improvement, interview prep and application tracking — unified.
          </p>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.title} className="rounded-xl border border-slate-200 p-6 transition-shadow hover:shadow-md">
                <feature.icon className="h-8 w-8 text-brand-600" aria-hidden />
                <h3 className="mt-4 font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technology */}
      <section className="border-t border-slate-100 bg-slate-900 py-20 text-white">
        <div className="mx-auto max-w-6xl px-4">
          <h2 className="text-center text-3xl font-bold">Built like a real AI product</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            <div className="rounded-xl border border-slate-800 bg-slate-800/50 p-6">
              <Layers className="h-7 w-7 text-brand-400" aria-hidden />
              <h3 className="mt-4 font-semibold">Genuine RAG pipeline</h3>
              <p className="mt-2 text-sm text-slate-300">
                Documents are chunked section-aware, embedded with sentence-transformers,
                stored in pgvector and retrieved semantically — not just dumped into a prompt.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-800/50 p-6">
              <BarChart3 className="h-7 w-7 text-brand-400" aria-hidden />
              <h3 className="mt-4 font-semibold">Explainable scoring</h3>
              <p className="mt-2 text-sm text-slate-300">
                Every score is a documented weighted formula. Every match lists its
                components, evidence and missing skills. No black boxes.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-800/50 p-6">
              <ShieldCheck className="h-7 w-7 text-brand-400" aria-hidden />
              <h3 className="mt-4 font-semibold">Hallucination controls</h3>
              <p className="mt-2 text-sm text-slate-300">
                All AI output is schema-validated and grounded against your actual resume
                text. Unsupported claims are dropped before they reach you.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20">
        <div className="mx-auto max-w-3xl px-4">
          <h2 className="text-center text-3xl font-bold text-slate-900">
            Frequently asked questions
          </h2>
          <div className="mt-10 space-y-4">
            {faqs.map((faq) => (
              <details key={faq.q} className="group rounded-xl border border-slate-200 p-5">
                <summary className="cursor-pointer list-none font-medium text-slate-900">
                  {faq.q}
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-100 bg-brand-600 py-16 text-center text-white">
        <div className="mx-auto max-w-2xl px-4">
          <h2 className="text-3xl font-bold">Ready to take control of your job search?</h2>
          <p className="mt-3 text-brand-100">
            Free to run locally. Your data stays in your own database.
          </p>
          <Link
            href="/auth/register"
            className="mt-8 inline-flex items-center gap-2 rounded-lg bg-white px-6 py-3 font-medium text-brand-700 hover:bg-brand-50"
          >
            Create your account <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-200 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 text-sm text-slate-500 sm:flex-row">
          <p>AI Career Copilot — open-source portfolio project (MIT license).</p>
          <p>FastAPI · PostgreSQL + pgvector · Next.js · Sentence-Transformers</p>
        </div>
      </footer>
    </div>
  );
}
