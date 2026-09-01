"""
Source Normalization and Multi-Factor Deduplication Service
Normalizes results from NewsAPI, SerpAPI, and scraped sources into a clean, canonical format.
Deduplicates identical links, syndicated wire copies (e.g. AP/Reuters reprinted), and near-duplicate headlines.
"""

import re
import hashlib
import logging
from typing import List, Dict, Any
from urllib.parse import urlparse
from backend.services.source_credibility import SourceCredibilityService

logger = logging.getLogger("news_verification.source_normalizer")


class SourceNormalizer:
    def __init__(self, credibility_service: SourceCredibilityService):
        self.credibility_service = credibility_service

    def _normalize_title(self, title: str) -> str:
        """Strip source name suffixes (e.g., ' - BBC News', ' | Reuters') and punctuation"""
        title = re.sub(r'\s*[-|–—:]\s*[A-Za-z0-9\s.]+$', '', title)
        title = re.sub(r'[^\w\s]', '', title).lower().strip()
        return title

    def _get_canonical_url(self, url: str) -> str:
        """Strip tracking parameters (utm_*, etc.) to find canonical URL"""
        if not url:
            return ""
        parsed = urlparse(url)
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        return clean_url.lower()

    def normalize_and_deduplicate(self, raw_articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge, clean, normalize, and deduplicate articles from all providers.
        """
        seen_canonical_urls = set()
        seen_title_hashes = set()
        normalized_list = []

        for item in raw_articles:
            raw_url = item.get("url", "").strip()
            title = item.get("title", "").strip()
            content = item.get("content", "").strip() or item.get("description", "").strip()
            source_name = item.get("source_name", "Unknown").strip()

            if not raw_url or not title or len(content) < 30:
                continue

            canonical_url = self._get_canonical_url(raw_url)
            if canonical_url in seen_canonical_urls:
                continue

            # Check normalized title duplicate (wire syndication)
            norm_title = self._normalize_title(title)
            title_hash = hashlib.md5(norm_title.encode("utf-8")).hexdigest()
            if title_hash in seen_title_hashes:
                logger.debug(f"Skipping syndicated wire duplicate: {title}")
                continue

            seen_canonical_urls.add(canonical_url)
            seen_title_hashes.add(title_hash)

            # Enrich with credibility tier
            cred_info = self.credibility_service.get_source_metadata(source_name, raw_url)

            # Generate unique stable article ID
            article_id = hashlib.sha256(canonical_url.encode("utf-8")).hexdigest()[:16]

            normalized_list.append({
                "article_id": article_id,
                "source_name": source_name,
                "domain": cred_info["domain"],
                "credibility_tier": cred_info["tier"],
                "credibility_label": cred_info["label"],
                "title": title,
                "url": raw_url,
                "canonical_url": canonical_url,
                "published_at": item.get("published_at"),
                "content": content,
                "search_provider": item.get("search_provider", "web"),
                "matched_query": item.get("matched_query", "")
            })

        logger.info(f"Normalized {len(raw_articles)} raw sources down to {len(normalized_list)} unique, deduplicated articles.")
        return normalized_list
