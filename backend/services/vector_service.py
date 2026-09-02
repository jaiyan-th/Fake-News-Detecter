"""
Semantic Vector Search Service
Performs in-memory vector indexing and semantic retrieval using FastEmbed and NumPy cosine similarity.
Provides lightning-fast, zero-dependency RAG evidence retrieval for news verification.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime, timezone
import numpy as np
from backend.services.embedding_service import EmbeddingService

logger = logging.getLogger("news_verification.vector_service")


class VectorSearchService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def is_available(self) -> bool:
        """Vector search engine is always available locally in-memory."""
        return True

    def index_evidence(self, verification_id: str, articles: List[Dict[str, Any]]) -> int:
        """
        Embed and index normalized articles in memory for semantic similarity retrieval.
        """
        if not articles:
            return 0

        texts_to_embed = [f"{a['title']}. {a.get('content', '')[:600]}" for a in articles]
        embeddings = self.embedding_service.embed_batch(texts_to_embed)
        now_iso = datetime.now(timezone.utc).isoformat()

        if verification_id not in self._store:
            self._store[verification_id] = []

        for art, emb in zip(articles, embeddings):
            self._store[verification_id].append({
                "vector": emb,
                "payload": {
                    "verification_id": verification_id,
                    "article_id": art.get("article_id"),
                    "source_name": art.get("source_name"),
                    "domain": art.get("domain"),
                    "title": art.get("title"),
                    "url": art.get("url"),
                    "published_at": art.get("published_at"),
                    "indexed_at": now_iso,
                    "content_snippet": art.get("content", "")[:600],
                    "credibility_tier": art.get("credibility_tier"),
                    "credibility_label": art.get("credibility_label"),
                    "search_provider": art.get("search_provider")
                }
            })

        logger.info(f"Indexed {len(articles)} evidence vectors for verification '{verification_id}'")
        return len(articles)

    def retrieve_relevant_evidence(
        self,
        query_text: str,
        verification_id: str,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic cosine similarity retrieval against indexed articles for a given claim.
        Filtered by the current verification_id.
        """
        query_vector = self.embedding_service.embed_text(query_text)
        stored_items = self._store.get(verification_id, [])

        if not stored_items:
            logger.warning(f"No indexed evidence found for verification '{verification_id}'")
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)

        scored = []
        for item in stored_items:
            doc_vec = np.array(item["vector"], dtype=np.float32)
            doc_norm = np.linalg.norm(doc_vec)
            norm = q_norm * doc_norm
            sim = float(np.dot(q_vec, doc_vec) / norm) if norm > 0 else 0.0
            scored.append((sim, item["payload"]))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, payload in scored[:top_k]:
            results.append({
                **payload,
                "relevance_score": round(max(0.0, min(1.0, sim)), 4)
            })

        top_score = results[0]["relevance_score"] if results else "N/A"
        logger.info(f"Retrieved {len(results)} evidence items via semantic search (top score: {top_score})")
        return results
