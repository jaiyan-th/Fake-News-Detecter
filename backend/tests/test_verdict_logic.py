"""
Tests for Verdict Generation & Stance Aggregation Logic
"""

from unittest.mock import MagicMock
from backend.services.verdict_generator import VerdictGenerator
from backend.schemas.verification import (
    ClaimInfo, EvidenceSource, StanceEnum, VerdictEnum
)


def test_zero_sources_returns_unverified():
    """Verify that when 0 sources are found, the verdict is decisively UNVERIFIED"""
    mock_groq = MagicMock()
    generator = VerdictGenerator(mock_groq)

    claim = ClaimInfo(primary_claim="Unknown rumor without any news coverage")
    response = generator.synthesize_verdict(
        claim_info=claim,
        analyzed_sources=[],
        pipeline_stages=[],
        processing_time_ms=150.0
    )

    assert response.verdict == VerdictEnum.UNVERIFIED
    assert response.confidence <= 50
    assert response.evidence_summary.total_sources_evaluated == 0
    assert "Insufficient" in response.summary


def test_rule_based_fallback_supporting_sources():
    """Verify that fallback rule synthesis correctly returns REAL when multiple sources support"""
    mock_groq = MagicMock()
    mock_groq.generate_json.side_effect = Exception("Groq timeout")
    generator = VerdictGenerator(mock_groq)

    claim = ClaimInfo(primary_claim="Government launched highway project")
    sources = [
        EvidenceSource(
            source_name="Reuters",
            domain="reuters.com",
            title="Highway project inaugurated",
            url="https://reuters.com/highway",
            stance=StanceEnum.SUPPORT,
            relevance_score=0.9,
            evidence_snippet="Project launched today."
        ),
        EvidenceSource(
            source_name="The Hindu",
            domain="thehindu.com",
            title="Prime Minister opens highway",
            url="https://thehindu.com/highway",
            stance=StanceEnum.SUPPORT,
            relevance_score=0.88,
            evidence_snippet="The highway is now open."
        )
    ]

    response = generator.synthesize_verdict(
        claim_info=claim,
        analyzed_sources=sources,
        pipeline_stages=[],
        processing_time_ms=200.0
    )

    assert response.verdict == VerdictEnum.REAL
    assert response.confidence >= 75
    assert response.evidence_summary.supporting == 2
    assert response.evidence_summary.contradicting == 0
