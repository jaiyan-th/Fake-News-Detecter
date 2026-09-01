"""
Qdrant Vector Database Service
Manages the stable collection 'news_evidence' with vector indexing,
payload storage, and session-filtered semantic retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from backend.core.config import settings
from backend.services.embedding_service import EmbeddingService

logger = logging.getLogger("news_verification.qdrant_service")


class QdrantService:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.collection_name = settings.QDRANT_COLLECTION
        self.client = None
        self._in_memory_fallback: Dict[str, List[Dict[str, Any]]] = {}
        self._init_client()

    def _init_client(self):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http.models import Distance, VectorParams

            if settings.QDRANT_URL.startswith("http"):
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=5.0
                )
            else:
                self.client = QdrantClient(location=":memory:")

            # Ensure stable collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created stable Qdrant collection: '{self.collection_name}'")
            else:
                logger.info(f"Connected to existing Qdrant collection: '{self.collection_name}'")
        except Exception as e:
            logger.warning(f"Qdrant connection unavailable ({e}). Using in-memory fallback store.")
            self.client = None

    def is_available(self) -> bool:
        return self.client is not None

    def index_evidence(self, verification_id: str, articles: List[Dict[str, Any]]) -> int:
        """
        Embed and upsert normalized articles into the stable Qdrant collection with payload metadata.
        """
        if not articles:
            return 0

        texts_to_embed = [f"{a['title']}. {a['content'][:600]}" for a in articles]
        embeddings = self.embedding_service.embed_batch(texts_to_embed)
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.client:
            try:
                from qdrant_client.http.models import PointStruct

                points = []
                for idx, (art, emb) in enumerate(zip(articles, embeddings)):
                    point_id = str(uuid.uuid4())
                    payload = {
                        "verification_id": verification_id,
                        "article_id": art.get("article_id"),
                        "source_name": art.get("source_name"),
                        "domain": art.get("domain"),
                        "title": art.get("title"),
                        "url": art.get("url"),
                        "published_at": art.get("published_at"),
                        "indexed_at": now_iso,
                        "content_snippet": art.get("content")[:600],
                        "credibility_tier": art.get("credibility_tier"),
                        "credibility_label": art.get("credibility_label"),
                        "search_provider": art.get("search_provider")
                    }
                    points.append(PointStruct(id=point_id, vector=emb, payload=payload))

                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Indexed {len(points)} evidence vectors into Qdrant collection '{self.collection_name}'")
                return len(points)
            except Exception as e:
                logger.error(f"Failed to upsert points to Qdrant: {e}")

        # In-memory fallback
        if verification_id not in self._in_memory_fallback:
            self._in_memory_fallback[verification_id] = []

        for art, emb in zip(articles, embeddings):
            self._in_memory_fallback[verification_id].append({
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
                    "content_snippet": art.get("content")[:600],
                    "credibility_tier": art.get("credibility_tier"),
                    "credibility_label": art.get("credibility_label"),
                    "search_provider": art.get("search_provider")
                }
            })
        return len(articles)

    def retrieve_relevant_evidence(
        self,
        query_text: str,
        verification_id: str,
        top_k: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity retrieval against Qdrant for a given claim.
        Filtered by the current verification_id payload.
        """
        query_vector = self.embedding_service.embed_text(query_text)
        results = []

        if self.client:
            try:
                from qdrant_client.http.models import Filter, FieldCondition, MatchValue

                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="verification_id",
                                match=MatchValue(value=verification_id)
                            )
                        ]
                    ),
                    limit=top_k
                )

                for hit in search_result:
                    payload = hit.payload or {}
                    results.append({
                        **payload,
                        "relevance_score": round(float(hit.score), 4)
                    })
                logger.info(f"Qdrant retrieved {len(results)} evidence items for query (top score: {results[0]['relevance_score'] if results else 'N/A'})")
                return results
            except Exception as e:
                logger.error(f"Qdrant search query failed: {e}")

        # In-memory cosine similarity fallback
        import numpy as np
        stored_items = self._in_memory_fallback.get(verification_id, [])
        q_vec = np.array(query_vector)

        scored = []
        for item in stored_items:
            doc_vec = np.array(item["vector"])
            norm = np.linalg.norm(q_vec) * np.linalg.norm(doc_vec)
            sim = float(np.dot(q_vec, doc_vec) / norm) if norm > 0 else 0.0
            scored.append((sim, item["payload"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        for sim, payload in scored[:top_k]:
            results.append({
                **payload,
                "relevance_score": round(max(0.0, min(1.0, sim)), 4)
            })

        return results
