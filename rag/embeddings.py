"""Embedding helpers for local-first retrieval."""

import hashlib
import math
import re
from typing import Protocol

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class EmbeddingModel(Protocol):
    """Interface implemented by embedding providers."""

    def embed(self, text: str) -> list[float]:
        """Return a vector representation for text."""


class HashingEmbeddingModel:
    """Deterministic lightweight embedder used when no ML model is configured."""

    def __init__(self, dimensions: int = 128) -> None:
        self._dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        """Return a normalized hashed bag-of-words embedding."""

        vector = [0.0] * self._dimensions
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimensions
            vector[bucket] += 1.0

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
