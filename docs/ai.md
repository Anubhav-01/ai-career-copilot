# AI Architecture

## Design principles

1. **Deterministic first.** LLMs are used only where language understanding or
   generation is genuinely required. File validation, skill matching, cosine
   similarity, scoring math — all plain code.
2. **Never trust model output.** Every LLM response passes through
   `guardrails.call_structured`: JSON extraction → Pydantic validation →
   bounded retries (validation error fed back) → typed result or a clean
   `AIServiceError`.
3. **Ground everything.** Extraction output is filtered against the source
   text (word-boundary matching); skills exist only with verbatim evidence;
   improvement prompts forbid new facts; roadmaps forbid URLs.
4. **Explain everything.** Scores are decomposed, weighted and narrated;
   matches list strong/partial/missing skills with evidence; interview
   questions carry their grounding.

## Provider abstraction

```
LLMProvider (abstract, single generate() method)
 ├── OpenAIProvider   — chat completions via httpx, JSON mode, timeouts,
 │                      429/4xx/5xx normalization; key from env only
 └── MockProvider     — deterministic, derives output from the structured
                        context embedded in each prompt (no fabrication);
                        lets the app run and be tested with zero API keys

EmbeddingProvider (abstract)
 ├── SentenceTransformerProvider — all-MiniLM-L6-v2 (384d), unit-normalized,
 │                                 loaded once per process
 └── HashingEmbeddingProvider    — dependency-free lexical fallback
                                   (feature-hashed word uni/bigrams);
                                   NOT semantic — used for tests and
                                   ML-less environments, reported by /health
```

Prompts embed a machine-readable `CONTEXT_JSON` block plus explicit
anti-hallucination rules. This gives real LLMs clean structured context and
lets the mock provider produce grounded output from the same interface.

## Resume parsing pipeline (hybrid)

```
raw text
  → regex contact extraction (email, phone, URLs) + optional spaCy PERSON NER
  → section segmentation (header lexicon: summary/experience/education/…)
  → taxonomy skill extraction (word-boundary regex over ~150 canonical
    skills + aliases; each hit records its evidence line)
  → draft ResumeExtraction (fully deterministic)
  → LLM refinement (draft + raw text; fills experience/education/projects)
  → grounding filter: any skill, employer, bullet, certification or project
    not literally present in the resume text is DROPPED
  → deterministic fields win on conflict (regex email > LLM email)
```

If the LLM is unavailable, the deterministic draft is used — the product
degrades, it does not break.

## Resume score (documented formula)

```
Overall = 25% ATS + 20% Skills + 20% Experience + 15% Projects
        + 10% Keyword coverage + 10% Structure
```

Weights come from `ScoreWeights` (env-overridable via
`RESUME_SCORE_WEIGHT_*`). Each component returns a 0–100 score **plus a
human-readable explanation** of how it was computed, e.g. skills =
`min(count/12)·70 + min(categories/4)·30`. The ATS component aggregates
heuristic findings (missing sections −10, no email −10, low action-verb ratio
−6, <30% quantified bullets −8, keyword stuffing −8, …), each finding shipping
a concrete recommendation.

> The ATS analysis is explicitly labeled an **ATS-style simulation**. It does
> not claim to reproduce any proprietary ATS.

## Hybrid job matching

```
Final = 40% semantic + 25% required skills + 15% preferred skills
      + 10% experience fit + 5% education fit + 5% keyword overlap
```

- **Semantic**: mean of each resume chunk's best cosine matches in the job's
  chunks (pgvector `<=>` in production, in-Python for tests). Raw cosine is
  calibrated to 0–100 over the empirically useful band [0.15, 0.75].
- **Skills**: canonical-name comparison via the taxonomy. Exact = strong match;
  same-category neighbor (job wants Kubernetes, resume shows Docker) = partial
  (40% credit); otherwise missing.
- **Evidence**: every strong match carries the resume line that proves it.
- **Experience**: profile value wins; otherwise estimated conservatively from
  resume date ranges; unknown → 50 with an explanation telling the user how to
  fix it.

## Skill gaps & roadmaps

Gap priorities are rule-based and transparent:

| Priority | Rule |
|---|---|
| critical | required by the job, no same-category resume skill |
| important | required, but user has a same-category skill |
| nice_to_have | preferred-only |

Roadmaps are LLM-generated within a strict schema (stages with
period/focus/practice task, project idea, estimated weeks) and grounded in the
user's known related skills. Course names/URLs are forbidden in the prompt and
absent from the schema, eliminating fabricated links.

## Interview system

- **Generation** is RAG-grounded: the target role is used as a semantic query
  over the user's resume chunks; retrieved evidence + extracted skills/projects
  + the job's required skills form the context. Each question stores a
  `grounding` string shown in the UI ("Why this question").
- **Evaluation** scores relevance, technical correctness, clarity,
  completeness and structure (0–100 each) with strengths/weaknesses/tips —
  judging only the answer text; the schema and prompt explicitly exclude
  personality or psychological claims.
- **Report** aggregates per-category averages and deduplicated takeaways.

## Cost control

| Mechanism | Where |
|---|---|
| Deterministic paths for validation/matching/scoring | whole AI layer |
| Content-hash cache for job analyses (1h TTL) | `JobService` |
| Embedding model loaded once, batch encoding | embedding provider |
| Re-index replaces chunks idempotently (no orphan vectors) | RAG indexer |
| Token budgets: word-bounded contexts, per-task `max_tokens` | prompts/guardrails |
| Retries capped (`LLM_MAX_RETRIES`, default 2) | guardrails |
| Mock provider for dev/tests/CI | provider factory |

Approximate real-provider cost per full user journey (gpt-4o-mini class model):
resume refinement ~3–4k tokens, job refinement ~2–3k, explanations ~0.5k each,
6 interview questions + 6 evaluations ~6–8k — well under $0.01–0.02 per
complete session at current small-model prices. (Order-of-magnitude estimate,
not a measured benchmark.)

## Hallucination controls (summary)

- Schema validation on every structured output
- Grounding filters on extraction (word-boundary text matching)
- Bullet improvement requires the bullet to exist verbatim in the resume (422 otherwise)
- Tailoring only cites skills the resume actually contains; missing skills are
  surfaced as "add only if truthful"
- Metrics are never invented — missing ones produce a suggestion field
- Roadmaps cannot emit URLs; evidence strings are verbatim resume lines
