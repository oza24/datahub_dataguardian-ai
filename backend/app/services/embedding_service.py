"""
Embedding + cosine similarity primitives used by the semantic matcher. This
is the mechanism that replaces field/table alias tables: candidates are
compared to the user's raw phrase in vector space instead of by string
equality against a maintained list.
"""
import logging
import math
from typing import Sequence

from google import genai

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else None
        self._model = settings.GEMINI_EMBEDDING_MODEL
        self._cache: dict[str, list[float]] = {}

    def embed(self, text: str) -> list[float]:
        key = text.strip().lower()
        if key in self._cache:
            return self._cache[key]
        if self._client is None:
            raise RuntimeError("GEMINI_API_KEY is not configured; cannot compute embeddings.")
        result = self._client.models.embed_content(model=self._model, contents=text)
        vector = result.embeddings[0].values
        self._cache[key] = vector
        return vector

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    @staticmethod
    def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)


embedding_service = EmbeddingService()
