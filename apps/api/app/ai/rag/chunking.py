"""Section-aware chunking for career documents.

Resumes are split on detected sections first (a chunk should not mix
'skills' with 'education'), then long sections are windowed by words with
overlap so no context is lost at boundaries.
"""
from dataclasses import dataclass

from app.ai.parsing.resume_parser import split_sections

MAX_WORDS = 180
OVERLAP_WORDS = 30


@dataclass
class Chunk:
    content: str
    index: int
    meta: dict


def _window(text: str, max_words: int = MAX_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()] if text.strip() else []
    chunks = []
    start = 0
    while start < len(words):
        piece = words[start : start + max_words]
        chunks.append(" ".join(piece))
        if start + max_words >= len(words):
            break
        start += max_words - overlap
    return chunks


def chunk_resume(text: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    index = 0
    for section, content in split_sections(text).items():
        for piece in _window(content):
            chunks.append(Chunk(content=piece, index=index, meta={"section": section}))
            index += 1
    if not chunks:  # fallback if no sections detected
        for piece in _window(text):
            chunks.append(Chunk(content=piece, index=index, meta={"section": "document"}))
            index += 1
    return chunks


def chunk_job(text: str) -> list[Chunk]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    merged: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip()
        if len(candidate.split()) > MAX_WORDS and buffer:
            merged.append(buffer)
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        merged.append(buffer)

    chunks: list[Chunk] = []
    index = 0
    for block in merged:
        for piece in _window(block):
            chunks.append(Chunk(content=piece, index=index, meta={"section": "job"}))
            index += 1
    return chunks
