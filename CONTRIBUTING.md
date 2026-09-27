# Contributing

## Setup

See the README's "Local development" section. TL;DR:

```bash
# backend
cd apps/api && python -m venv .venv && .venv/Scripts/activate
pip install -r requirements-dev.txt
pytest tests -q

# frontend
cd apps/web && npm install && npm test
```

## Ground rules

1. **Tests pass, lint passes.** `pytest` + `ruff check` for the API,
   `npm test` + `npm run typecheck` + `npm run lint` for the web app. CI
   enforces all of it.
2. **Layering.** Routers stay thin; business logic in services; SQL in
   repositories; AI calls only from services via the `app.ai` package.
3. **No unvalidated LLM output.** Anything a model returns goes through
   `guardrails.call_structured` with a Pydantic schema, and extraction-type
   outputs must be grounded against source text.
4. **No fake features.** Don't merge buttons or endpoints that pretend to work.
   Mark future work in the README instead.
5. **Schema changes need a migration.** Add an explicit Alembic revision (the
   metadata-based initial revision is the only exception).
6. **Secrets never enter the repo.** `.env` is gitignored; update
   `.env.example` when adding configuration.
7. **Privacy.** Never log resume content, tokens or passwords. New user data
   must be user-scoped in the repository layer and covered by account deletion.

## Commit style

Short imperative subject, context in the body when needed. Group related
changes; avoid drive-by reformatting.
