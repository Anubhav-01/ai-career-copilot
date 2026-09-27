# Resume Positioning

Truthful, verifiable bullets for this project. Everything below is implemented
in this repository — no invented metrics or usage claims.

## Project title

**AI Career Copilot** — full-stack AI job-search platform (FastAPI, Next.js,
PostgreSQL + pgvector, sentence-transformers)

## Bullets (pick 3–5 per application)

- Built a full-stack AI career platform (FastAPI, Next.js/TypeScript,
  PostgreSQL) covering resume analysis, semantic job matching, skill-gap
  analysis, learning roadmaps, mock interviews and application tracking.
- Implemented a RAG pipeline with section-aware chunking, sentence-transformer
  embeddings (all-MiniLM-L6-v2) and pgvector storage with HNSW cosine indexing
  and metadata-filtered retrieval.
- Designed a hybrid job-matching engine blending embedding similarity (40%)
  with taxonomy-based skill coverage, experience and education fit — fully
  explainable, returning strong/partial/missing skills with verbatim resume
  evidence.
- Engineered a hallucination-controlled LLM integration: provider abstraction
  (OpenAI/mock), Pydantic-validated structured outputs with bounded retries,
  and grounding filters that drop any extracted fact not present in the source
  document.
- Built a hybrid resume parser (PDF/DOCX) combining deterministic extraction
  (regex, section heuristics, a ~150-skill alias taxonomy with evidence
  capture) with schema-validated LLM refinement.
- Implemented JWT authentication with hashed, rotating refresh tokens,
  repository-level user isolation, upload validation (magic bytes, size,
  type), rate limiting and structured JSON logging with request IDs.
- Created an AI evaluation harness measuring skill-extraction precision/recall/
  F1 and parsing field accuracy on labeled sets, wired as a regression gate.
- Shipped 67 automated tests (pytest + Vitest/Testing Library), GitHub Actions
  CI (lint, tests, pgvector migration check, Docker builds) and a one-command
  `docker compose up` deployment.

## Do NOT claim (unless you later measure them)

- User counts, production traffic, uptime
- Accuracy percentages beyond the documented synthetic-set harness results
- Cost savings or latency numbers that were not benchmarked
