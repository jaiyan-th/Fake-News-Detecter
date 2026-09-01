"""
Tests for Source Normalization & Wire Deduplication
"""

from backend.services.source_credibility import SourceCredibilityService
from backend.services.source_normalizer import SourceNormalizer


def test_canonical_url_deduplication():
    cred_service = SourceCredibilityService()
    normalizer = SourceNormalizer(cred_service)

    raw_articles = [
        {
            "title": "Government Approves New Policy",
            "url": "https://reuters.com/world/india/policy?utm_source=twitter&utm_medium=social",
            "content": "Official announcement made on Monday regarding new policy.",
            "source_name": "Reuters"
        },
        {
            "title": "Government Approves New Policy",
            "url": "https://reuters.com/world/india/policy",  # Exact same canonical URL
            "content": "Official announcement made on Monday regarding new policy.",
            "source_name": "Reuters"
        }
    ]

    result = normalizer.normalize_and_deduplicate(raw_articles)
    assert len(result) == 1
    assert result[0]["source_name"] == "Reuters"
    assert result[0]["credibility_tier"] == "WIRE_AND_PRIMARY_AGENCY"


def test_wire_syndication_deduplication():
    """Verify that identical syndicated wire stories from different publishers are deduplicated"""
    cred_service = SourceCredibilityService()
    normalizer = SourceNormalizer(cred_service)

    raw_articles = [
        {
            "title": "Supreme Court Rules on Electoral Bonds - Reuters",
            "url": "https://reuters.com/article/1",
            "content": "The supreme court struck down the electoral bonds scheme as unconstitutional.",
            "source_name": "Reuters"
        },
        {
            "title": "Supreme Court Rules on Electoral Bonds - The Tribune",
            "url": "https://tribuneindia.com/article/2",
            "content": "The supreme court struck down the electoral bonds scheme as unconstitutional.",
            "source_name": "The Tribune"
        }
    ]

    result = normalizer.normalize_and_deduplicate(raw_articles)
    assert len(result) == 1
    assert result[0]["source_name"] == "Reuters"
