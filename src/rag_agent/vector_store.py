from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .embeddings import Embedder
from .models import Chunk, SearchResult


class ChromaVectorStore:
    def __init__(self, persist_dir: Path, collection_name: str, embedder: Embedder):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError("Install chromadb to use the vector database.") from exc

        self.embedder = embedder
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset(self) -> None:
        ids = self.collection.get(include=[])["ids"]
        if ids:
            self.collection.delete(ids=ids)

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        embeddings = self.embedder.embed([chunk.text for chunk in chunks])
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                {
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    **chunk.metadata,
                }
                for chunk in chunks
            ],
        )

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        query_embedding = self.embedder.embed([query])[0]
        response = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        results: list[SearchResult] = []
        for chunk_id, document, metadata, distance in zip(
            response["ids"][0],
            response["documents"][0],
            response["metadatas"][0],
            response["distances"][0],
        ):
            chunk = Chunk(
                id=chunk_id,
                text=document,
                source=str(metadata["source"]),
                chunk_index=int(metadata["chunk_index"]),
                metadata={key: str(value) for key, value in metadata.items()},
            )
            results.append(SearchResult(chunk=chunk, similarity=1.0 - float(distance)))
        return results


class JsonVectorStore:
    """Tiny fallback store useful for tests and locked-down environments."""

    def __init__(self, index_path: Path, embedder: Embedder):
        self.index_path = index_path
        self.embedder = embedder
        self.items: list[dict] = []
        if index_path.exists():
            self.items = json.loads(index_path.read_text(encoding="utf-8"))

    def reset(self) -> None:
        self.items = []
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text("[]", encoding="utf-8")

    def add(self, chunks: list[Chunk]) -> None:
        embeddings = self.embedder.embed([chunk.text for chunk in chunks])
        self.items.extend(
            {
                "chunk": {
                    "id": chunk.id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "metadata": chunk.metadata,
                },
                "embedding": embedding,
            }
            for chunk, embedding in zip(chunks, embeddings)
        )
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self.items, indent=2), encoding="utf-8")

    def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        if not self.items:
            return []
        query_embedding = np.array(self.embedder.embed([query])[0], dtype=np.float32)
        scored: list[SearchResult] = []
        for item in self.items:
            embedding = np.array(item["embedding"], dtype=np.float32)
            similarity = float(np.dot(query_embedding, embedding))
            chunk_data = item["chunk"]
            scored.append(
                SearchResult(
                    chunk=Chunk(
                        id=chunk_data["id"],
                        text=chunk_data["text"],
                        source=chunk_data["source"],
                        chunk_index=chunk_data["chunk_index"],
                        metadata=chunk_data["metadata"],
                    ),
                    similarity=similarity,
                )
            )
        return sorted(scored, key=lambda result: result.similarity, reverse=True)[:top_k]

