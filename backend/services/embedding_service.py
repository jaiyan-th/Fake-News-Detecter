"""
Embedding Service using FastEmbed (ONNX Runtime)
Provides lightweight, high-speed 384-dimensional dense vector embeddings.
Strictly used for semantic retrieval in RAG (NO ML classification).
"""

import logging
from typing import List
import numpy as np
from backend.core.config import settings

logger = logging.getLogger("news_verification.embedding_service")


class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._initialized = False

    def _lazy_init(self):
        if not self._initialized:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name)
                self._initialized = True
                logger.info(f"FastEmbed embedding model initialized: {self.model_name}")
            except Exception as e:
                logger.warning(f"FastEmbed initialization failed: {e}. Fallback vector mode enabled.")
                self._initialized = True
                self._model = None

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single string"""
        self._lazy_init()
        if not text or not text.strip():
            return [0.0] * settings.EMBEDDING_DIM

        if self._model:
            try:
                embeddings = list(self._model.embed([text]))
                return embeddings[0].tolist()
            except Exception as e:
                logger.error(f"Embedding generation error: {e}")

        # Deterministic fallback vector when fastembed is not installed
        np.random.seed(abs(hash(text[:50])) % (2**32))
        vec = np.random.randn(settings.EMBEDDING_DIM).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of strings efficiently"""
        self._lazy_init()
        if not texts:
            return []

        if self._model:
            try:
                embeddings = list(self._model.embed(texts))
                return [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.error(f"Batch embedding generation error: {e}")

        return [self.embed_text(t) for t in texts]
