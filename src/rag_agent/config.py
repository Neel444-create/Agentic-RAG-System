from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_root: Path = Path(__file__).resolve().parents[2]
    docs_dir: Path = Path("data/sample_docs")
    persist_dir: Path = Path("data/chroma")
    collection_name: str = "assignment_docs"
    chunk_size: int = 900
    chunk_overlap: int = 160
    top_k: int = int(os.getenv("RAG_TOP_K", "5"))
    min_similarity: float = float(os.getenv("RAG_MIN_SIMILARITY", "0.18"))
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
    embedding_model: str = os.getenv("RAG_EMBEDDING_MODEL", "text-embedding-3-small")
    chat_model: str = os.getenv("RAG_CHAT_MODEL", "gpt-4o-mini")

    def resolve(self, path: Path | str) -> Path:
        path = Path(path)
        return path if path.is_absolute() else self.project_root / path


settings = Settings()
