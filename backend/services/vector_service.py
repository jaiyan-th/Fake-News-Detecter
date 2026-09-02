"""
Enhanced Semantic Vector Search Service
Implements sentence-level semantic indexing, FastEmbed dense vector embeddings,
cosine similarity scoring with credibility-tier weighting, and high-density evidence extraction.
"""

import logging
import re
from typing import List, Dict, Any
from datetime import datetime, timezone
import numpy as np
from backend.services.embedding_service import EmbeddingService

logger = logging.getLogger("news_verification.vector_service")

# Tier credibility weighting bonuses for evidence ranking
CREDIBILITY_BOOSTS = {
    "WIRE_AND_PRIMARY_AGENCY": 0.06,
    "MAJOR_INTERNATIONAL_BROADCASTER": 0.05,
    "NATIONAL_REPUTABLE_BROADCASTER": 0.04,
    "ESTABLISHED_NEWS_ORGANIZATION": 0.03,
    "REGIONAL_ESTABLISHED": 0.02,
    "STANDARD_NEWS": 0.0,
    "UNKNOWN_OR_UNTIERED": -0.02,
    "USER_GENERATED_OR_SOCIAL": -0.05,
}


class VectorSearchService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self._store: Dict[str, List[Dict[str, Any]]] = {}

    def is_available(self) -> bool:
        """In-memory vector search engine is always available."""
        return True

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split article text into clean sentence-level semantic chunks."""
        if not text:
            return []
        # Split on sentence boundaries
        raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        chunks = []
        for s in raw_sentences:
            s_clean = s.strip()
            if len(s_clean) >= 25:  # meaningful sentence
                chunks.append(s_clean[:300])
        return chunks[:8]  # top 8 sentences per article to preserve memory and speed

    def index_evidence(self, verification_id: str, articles: List[Dict[str, Any]]) -> int:
        """
        Embed and index normalized articles with multi-chunk sentence embeddings for fine-grained retrieval.
        """
        if not articles:
            return 0

        now_iso = datetime.now(timezone.utc).isoformat()
        if verification_id not in self._store:
            self._store[verification_id] = []

        # Prepare all chunks to embed in a single batch
        all_texts_to_embed = []
        chunk_map = []  # tracks which article each chunk belongs to

        for art_idx, art in enumerate(articles):
            title = art.get("title", "").strip()
            content = art.get("content", "").strip()
            chunks = [title] + self._split_into_chunks(content)

            for chunk in chunks:
                all_texts_to_embed.append(chunk)
                chunk_map.append((art_idx, chunk))

        # Batch embed all chunks
        embeddings = self.embedding_service.embed_batch(all_texts_to_embed)

        # Organize by article
        article_chunks: Dict[int, List[Dict[str, Any]]] = {}
        for (art_idx, chunk_text), emb in zip(chunk_map, embeddings):
            if art_idx not in article_chunks:
                article_chunks[art_idx] = []
            article_chunks[art_idx].append({
                "text": chunk_text,
                "vector": emb
            })

        # Store in verification session
        for art_idx, art in enumerate(articles):
            chunks = article_chunks.get(art_idx, [])
            if not chunks:
                continue

            self._store[verification_id].append({
                "chunks": chunks,
                "payload": {
                    "verification_id": verification_id,
                    "article_id": art.get("article_id"),
                    "source_name": art.get("source_name"),
                    "domain": art.get("domain"),
                    "title": art.get("title"),
                    "url": art.get("url"),
                    "published_at": art.get("published_at"),
                    "indexed_at": now_iso,
                    "credibility_tier": art.get("credibility_tier", "STANDARD_NEWS"),
                    "credibility_label": art.get("credibility_label", "Standard News"),
                    "search_provider": art.get("search_provider", "web")
                }
            })

        logger.info(f"Indexed {len(articles)} articles ({len(all_texts_to_embed)} sentence chunks) for session '{verification_id}'")
        return len(articles)

    def retrieve_relevant_evidence(
        self,
        query_text: str,
        verification_id: str,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Perform high-precision semantic cosine similarity retrieval.
        Finds the exact most relevant sentence from each article, applies credibility weighting,
        and returns the top-K highest quality evidence items.
        """
        query_vector = self.embedding_service.embed_text(query_text)
        stored_articles = self._store.get(verification_id, [])

        if not stored_articles:
            logger.warning(f"No indexed evidence found for verification '{verification_id}'")
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        scored_articles = []

        for item in stored_articles:
            payload = item["payload"]
            tier = payload.get("credibility_tier", "STANDARD_NEWS")
            credibility_boost = CREDIBILITY_BOOSTS.get(tier, 0.0)

            # Find maximum similarity across all sentence chunks in this article
            best_chunk_text = payload.get("title", "")
            best_sim = 0.0

            for chunk in item["chunks"]:
                c_vec = np.array(chunk["vector"], dtype=np.float32)
                c_norm = np.linalg.norm(c_vec)
                if c_norm > 0:
                    sim = float(np.dot(q_vec, c_vec) / (q_norm * c_norm))
                    if sim > best_sim:
                        best_sim = sim
                        best_chunk_text = chunk["text"]

            # Combined score: raw semantic similarity + subtle credibility weighting
            weighted_score = max(0.0, min(1.0, best_sim + credibility_boost))

            scored_articles.append({
                **payload,
                "evidence_snippet": best_chunk_text,
                "content_snippet": best_chunk_text,
                "raw_similarity": round(best_sim, 4),
                "relevance_score": round(weighted_score, 4)
            })

        # Sort by relevance score descending
        scored_articles.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Filter out completely irrelevant noise (similarity threshold < 0.20)
        filtered = [a for a in scored_articles if a["raw_similarity"] >= 0.20]
        results = filtered[:top_k] if filtered else scored_articles[:top_k]

        top_score = results[0]["relevance_score"] if results else "N/A"
        logger.info(f"Retrieved {len(results)} high-precision evidence items (top score: {top_score})")
        return results
