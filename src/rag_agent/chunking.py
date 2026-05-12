from __future__ import annotations

import hashlib

from .models import Chunk, Document


def chunk_documents(
    documents: list[Document],
    chunk_size: int = 900,
    chunk_overlap: int = 160,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for document in documents:
        parts = split_text(document.text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for index, text in enumerate(parts):
            digest = hashlib.sha1(f"{document.source}:{index}:{text}".encode("utf-8")).hexdigest()[:16]
            chunks.append(
                Chunk(
                    id=digest,
                    text=text,
                    source=str(document.source),
                    chunk_index=index,
                    metadata=document.metadata | {"source_name": document.source.name},
                )
            )
    return chunks


def split_text(text: str, chunk_size: int = 900, chunk_overlap: int = 160) -> list[str]:
    if not text.strip():
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_long_text(paragraph, chunk_size, chunk_overlap))
            continue

        candidate = f"{current}\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            chunks.append(current.strip())
            overlap = current[-chunk_overlap:].strip()
            current = f"{overlap}\n{paragraph}".strip() if overlap else paragraph

    if current:
        chunks.append(current.strip())
    return chunks


def _split_long_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - chunk_overlap
    return chunks

