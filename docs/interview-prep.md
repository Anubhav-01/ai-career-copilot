# Interview Preparation — defending this project

Questions you should be able to answer about AI Career Copilot, with the
project-specific answers.

## Architecture

**Why this architecture (API → services → repositories)?**
Separation of concerns and testability. Routers stay thin (validation +
delegation), services own workflows and are unit-testable without HTTP,
repositories own SQL so authorization (user scoping) lives in exactly one
place. The AI layer is isolated so providers can be swapped (OpenAI ↔ mock)
without touching business logic.

**Why FastAPI?**
Native Pydantic integration (the same schemas validate requests *and* LLM
outputs), automatic OpenAPI docs, dependency injection for DB sessions/auth,
async-capable, and background tasks for the parsing pipeline.

**Why PostgreSQL?**
Relational integrity for a domain full of relationships (users → resumes →
analyses → matches), JSON columns for validated AI artifacts, and — decisively —
pgvector, which keeps vectors next to the relational data they describe.

**Why pgvector instead of a dedicated vector DB?**
One less system: transactional consistency (deleting a resume deletes its
embeddings in the same transaction), metadata filtering with plain SQL `WHERE`
before ANN ranking, HNSW indexing for cosine distance. At this scale a separate
vector DB adds ops cost with no benefit; the repository abstraction makes a
later swap contained.

**Why RAG rather than sending whole documents to the LLM?**
Cost (token budgets), quality (the model sees only relevant, deduplicated
chunks), and control (retrieved chunks carry metadata so outputs can cite
evidence). Interview generation retrieves resume chunks relevant to the target
role instead of dumping the resume.

## AI

**How do embeddings work here?**
Sentence-transformers (`all-MiniLM-L6-v2`) map text to 384-d unit vectors such
that semantically similar text is close in cosine terms. Documents are chunked
(section-aware, 180 words, 30 overlap), embedded in batch, stored with
metadata.

**Why cosine similarity?**
Vectors are unit-normalized, so cosine is the natural metric (equivalent to dot
product here) and pgvector has a native `<=>` operator with HNSW support. It
measures direction (meaning) not magnitude (length of text).

**How do you reduce hallucinations?**
Layered: (1) schema validation with retries; (2) grounding filters — extracted
facts must exist in the source text (word-boundary matched); (3) task design —
bullet improvement requires the exact bullet to exist, tailoring separates
"emphasize" (evidenced) from "missing" (add only if truthful); (4) prompts
embed explicit anti-fabrication rules; (5) deterministic evidence: every skill
carries the resume line it came from.

**How do you evaluate the AI system?**
A harness (`evals/run.py`) measures skill-extraction P/R/F1 and extraction
field accuracy on labeled sets, plus a ranking sanity check. Its limitations
are documented honestly (small synthetic sets, taxonomy-bounded recall).
LLM-quality paths are schema/grounding-tested with a mock; real-quality
assessment would need human-reviewed samples.

**Hybrid matching — why not pure cosine?**
Cosine captures topical similarity but misses hard requirements. A resume can
be "about" backend work yet lack the required Kubernetes. The blend (40%
semantic + explicit skill/experience/education/keyword components) keeps both
signal types, stays explainable, and its weights are configurable.

## Backend

**How does authentication work?**
PBKDF2-SHA256 password hashing (pure-Python, NIST-recommended KDF). JWT access
tokens (30 min) + refresh tokens (7 days) stored server-side as SHA-256 hashes
with rotation on use and revocation on password change/logout/account deletion.

**How are files processed safely?**
Allowlisted extensions, 5MB cap, magic-byte checks (PDF `%PDF`, DOCX zip
header), random storage filenames under a per-user directory, parsing in a
background task with failure states — and files/rows/embeddings are removed on
delete.

**How are background jobs handled?**
FastAPI background tasks with a status state machine polled by the UI. The
pipeline is a plain service method with its own session, deliberately framework-
independent so it can move to Celery + Redis unchanged when horizontal scale is
needed.

## Database

**What indexes exist?**
PK indexes (UUID), unique email + token-hash indexes, FK-side indexes on all
`user_id`/`resume_id`/`job_id` columns, composite `(document_id, document_type)`
and `(user_id, document_type)` on embeddings, application status index, and an
HNSW cosine index on the vector column.

**Soft vs hard deletion?**
User-facing artifacts (resumes, jobs, applications) soft-delete (`deleted_at`)
to preserve referential history; account deletion is a hard cascade for
privacy. The base repository filters soft-deleted rows automatically.

## System design follow-ups

**A million users?** Stateless API replicas behind LB; Redis-backed rate
limiting + cache; Celery workers for parse/embed; read replicas; object storage
for uploads; partition embeddings or move ANN out only when pgvector limits are
actually reached.

**Cut LLM costs 10×?** Cache by content hash (done), route tasks to the
smallest capable model, batch, truncate contexts by retrieval score (done),
pre-compute explanations only on demand, and fall back to deterministic
explanation templates for low-value calls.

**Large resume files?** Streamed upload with size cap (done at read), page
limits, OCR pipeline for scanned PDFs as an async job, chunked text extraction.
