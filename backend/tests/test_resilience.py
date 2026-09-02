"""
Tests for Error Resilience & Fallback Handling
"""

import pytest
from backend.services.article_extractor import ArticleExtractor
from backend.core.exceptions import ArticleExtractionError
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_service import VectorSearchService


def test_article_extractor_invalid_url():
    """Verify that an invalid or non-http URL raises clean ArticleExtractionError"""
    extractor = ArticleExtractor(timeout=2)
    with pytest.raises(ArticleExtractionError) as exc_info:
        extractor.extract("not_a_valid_url")
    assert "Invalid URL format" in str(exc_info.value)


def test_embedding_and_vector_search():
    """Verify that FastEmbed embedding and vector search work seamlessly in memory"""
    emb_service = EmbeddingService()
    vector = emb_service.embed_text("India launches new space mission")
    assert len(vector) == 384

    vector_service = VectorSearchService(emb_service)
    session_id = "test-session-123"

    articles = [
        {
            "article_id": "art1",
            "title": "ISRO Launches New Satellite",
            "content": "Indian Space Research Organisation successfully launched satellite from Sriharikota.",
            "source_name": "The Hindu",
            "domain": "thehindu.com",
            "url": "https://thehindu.com/isro-launch",
            "published_at": "2026-08-30",
            "credibility_tier": "ESTABLISHED_NEWS_ORGANIZATION",
            "credibility_label": "Established News Organization",
            "search_provider": "newsapi"
        }
    ]

    indexed_count = vector_service.index_evidence(session_id, articles)
    assert indexed_count == 1

    retrieved = vector_service.retrieve_relevant_evidence("ISRO satellite launch", session_id, top_k=2)
    assert len(retrieved) == 1
    assert retrieved[0]["source_name"] == "The Hindu"
    assert retrieved[0]["relevance_score"] > 0.0
