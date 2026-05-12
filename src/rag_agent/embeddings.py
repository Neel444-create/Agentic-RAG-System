from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

import numpy as np

from .config import Settings


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class OpenAIEmbedder(Embedder):
    def __init__(self, settings: Settings):
        from openai import OpenAI

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model, input=texts)
        return [item.embedding for item in response.data]


class HashingEmbedder(Embedder):
    """Offline fallback that keeps the app demonstrable without network credentials."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

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


def build_embedder(settings: Settings) -> Embedder:
    if settings.openai_api_key:
        return OpenAIEmbedder(settings)
    return HashingEmbedder()

