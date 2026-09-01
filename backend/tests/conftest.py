"""
Pytest Fixtures and Mock Providers for News Verification Test Suite
"""

import pytest
from unittest.mock import MagicMock
from backend.services.article_extractor import ExtractedArticle
from backend.schemas.verification import ClaimInfo, EvidenceSource, StanceEnum


@pytest.fixture
def mock_extracted_article():
    return ExtractedArticle(
        url="https://reuters.com/world/example-news-story",
        title="India Announces Landmark Solar Energy Expansion",
        content="The government of India has officially announced a $5 billion solar energy expansion plan today in New Delhi.",
        publisher="reuters.com",
        published_date="2026-08-30T10:00:00Z"
    )


@pytest.fixture
def sample_claim_info():
    return ClaimInfo(
        primary_claim="India announced a $5 billion solar energy expansion plan.",
        secondary_claims=["The initiative was announced in New Delhi."],
        entities=["India", "New Delhi", "Solar Energy"],
        timeframe="2026-08-30"
    )


@pytest.fixture
def sample_evidence_sources():
    return [
        EvidenceSource(
            source_name="Reuters",
            domain="reuters.com",
            title="India Details $5B Solar Plan",
            url="https://reuters.com/solar-plan",
            published_at="2026-08-30T11:00:00Z",
            stance=StanceEnum.SUPPORT,
            relevance_score=0.94,
            evidence_snippet="The government announced $5B in solar funding.",
            credibility_tier="WIRE_AND_PRIMARY_AGENCY",
            search_provider="newsapi"
        ),
        EvidenceSource(
            source_name="The Hindu",
            domain="thehindu.com",
            title="Cabinet Approves Solar Mission Outlay",
            url="https://thehindu.com/solar-outlay",
            published_at="2026-08-30T12:00:00Z",
            stance=StanceEnum.SUPPORT,
            relevance_score=0.89,
            evidence_snippet="The cabinet cleared the multi-billion solar rollout.",
            credibility_tier="ESTABLISHED_NEWS_ORGANIZATION",
            search_provider="serpapi"
        )
    ]
