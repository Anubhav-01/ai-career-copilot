"""Context builder: assemble retrieved chunks into a token-bounded context
block for LLM prompts (instead of dumping whole documents)."""
from app.ai.rag.retriever import RetrievedChunk

DEFAULT_WORD_BUDGET = 900  # ~1200 tokens


def build_context(chunks: list[RetrievedChunk], word_budget: int = DEFAULT_WORD_BUDGET) -> str:
    """Deduplicate, order by relevance, and pack chunks under the budget."""
    seen: set[str] = set()
    parts: list[str] = []
    used = 0
    for chunk in sorted(chunks, key=lambda c: c.similarity, reverse=True):
        key = chunk.content[:120]
        if key in seen:
            continue
        words = len(chunk.content.split())
        if used + words > word_budget:
            continue
        seen.add(key)
        used += words
        section = (chunk.meta or {}).get("section", chunk.document_type)
        parts.append(f"[{chunk.document_type}/{section}] {chunk.content}")
    return "\n\n".join(parts)
