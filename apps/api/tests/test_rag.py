from app.ai.embeddings.hashing import HashingEmbeddingProvider
from app.ai.rag.chunking import chunk_job, chunk_resume
from app.ai.rag.context import build_context
from app.ai.rag.retriever import RetrievedChunk
from tests.conftest import SAMPLE_JOB_DESCRIPTION, SAMPLE_RESUME_LINES

SAMPLE_TEXT = "\n".join(SAMPLE_RESUME_LINES)


def test_resume_chunking_is_section_aware():
    chunks = chunk_resume(SAMPLE_TEXT)
    assert chunks
    sections = {c.meta["section"] for c in chunks}
    assert "skills" in sections
    assert "experience" in sections
    # indices are sequential
    assert [c.index for c in chunks] == list(range(len(chunks)))


def test_job_chunking_respects_word_limit():
    long_text = SAMPLE_JOB_DESCRIPTION * 5
    chunks = chunk_job(long_text)
    assert all(len(c.content.split()) <= 180 for c in chunks)


def test_hashing_embedder_properties():
    embedder = HashingEmbeddingProvider(dimension=64)
    a, b = embedder.embed(["python fastapi backend", "python fastapi backend"])
    assert a == b  # deterministic
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6  # unit norm

    c = embedder.embed_one("completely different gardening text")
    sim_ab = sum(x * y for x, y in zip(a, b, strict=True))
    sim_ac = sum(x * y for x, y in zip(a, c, strict=True))
    assert sim_ab > sim_ac  # similar text scores higher


def test_context_builder_budget_and_dedup():
    import uuid

    doc_id = uuid.uuid4()
    chunks = [
        RetrievedChunk(content="repeated chunk " * 10, similarity=0.9,
                       document_id=doc_id, document_type="resume",
                       chunk_index=0, meta={"section": "skills"}),
        RetrievedChunk(content="repeated chunk " * 10, similarity=0.8,
                       document_id=doc_id, document_type="resume",
                       chunk_index=1, meta={"section": "skills"}),
        RetrievedChunk(content="unique content here", similarity=0.7,
                       document_id=doc_id, document_type="resume",
                       chunk_index=2, meta={"section": "projects"}),
    ]
    context = build_context(chunks, word_budget=100)
    assert context.count("repeated chunk") == 10  # deduplicated
    assert "unique content here" in context
    assert "[resume/projects]" in context
