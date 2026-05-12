from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Document:
    text: str
    source: Path
    metadata: dict[str, str]


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    chunk_index: int
    metadata: dict[str, str]


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    similarity: float


@dataclass(frozen=True)
class Answer:
    question: str
    answer: str
    sources: list[SearchResult]
    used_llm: bool

