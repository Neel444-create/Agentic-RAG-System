from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

import numpy as np

from .config import Settings


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")

#Purpose: This file converts text into numerical vectors called embeddings, which allow the RAG system to compare a user's question with stored document chunks and find relevant information.

#Base class that defines the embedding interface.
class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        raise NotImplementedError

#Uses Google's Gemini embedding API to generate vectors.
class GeminiEmbedder(Embedder):
    def __init__(self, settings: Settings):
        from google import genai

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.embedding_model

    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        from google.genai import types

        response = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=768),
        )
        return [embedding.values for embedding in response.embeddings]

#Creates vectors locally without requiring an API key.
class HashingEmbedder(Embedder):
    """Offline fallback that keeps the app demonstrable without network credentials."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions
    #Converts a list of text strings into vectors.
    def embed(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        return [self._embed_one(text) for text in texts]
    #Converts one text into a vector using token hashing.
    def _embed_one(self, text: str) -> list[float]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = TOKEN_PATTERN.findall(text.lower())
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign * (1.0 + math.log1p(len(token)))
        norm = np.linalg.norm(vector)
        if norm:
            vector = vector / norm
        return vector.tolist()

#Selects Gemini or the local fallback based on API-key availability.
def build_embedder(settings: Settings) -> Embedder:
    if settings.gemini_api_key:
        return GeminiEmbedder(settings)
    return HashingEmbedder()

