from __future__ import annotations

from pathlib import Path

from .chunking import chunk_documents
from .config import Settings, settings
from .embeddings import build_embedder
from .llm import GroundedAnswerer
from .loaders import load_documents
from .models import Answer, Chunk
from .vector_store import ChromaVectorStore, JsonVectorStore


class RagAgent:
    def __init__(self, config: Settings = settings, use_json_store: bool = False):
        self.settings = config
        self.embedder = build_embedder(config)
        if use_json_store:
            self.store = JsonVectorStore(config.resolve("data/index.json"), self.embedder)
        else:
            self.store = ChromaVectorStore(
                config.resolve(config.persist_dir),
                config.collection_name,
                self.embedder,
            )
        self.answerer = GroundedAnswerer(config)

    def ingest(self, docs_path: Path | str | None = None, reset: bool = True) -> list[Chunk]:
        path = self.settings.resolve(docs_path or self.settings.docs_dir)
        documents = load_documents(path)
        chunks = chunk_documents(
            documents,
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        if reset:
            self.store.reset()
        self.store.add(chunks)
        return chunks

    def ask(self, question: str) -> Answer:
        results = self.store.search(question, top_k=self.settings.top_k)
        grounded = [result for result in results if result.similarity >= self.settings.min_similarity]
        answer_text = self.answerer.answer(question, grounded)
        return Answer(
            question=question,
            answer=answer_text,
            sources=grounded,
            used_llm=self.answerer.uses_llm,
        )

