"""
Async NewsAPI Search Service with Precision Query Optimization & Fallbacks
"""

import logging
import re
from typing import List, Dict, Any, Optional
import httpx
from backend.core.config import settings

logger = logging.getLogger("news_verification.newsapi_service")


class NewsAPIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.NEWS_API_KEY
        self.base_url = "https://newsapi.org/v2/everything"
        self.top_headlines_url = "https://newsapi.org/v2/top-headlines"
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _clean_query(self, query: str) -> str:
        """Strip punctuation and invalid characters that disrupt NewsAPI query syntax."""
        cleaned = re.sub(r'["\'\(\)\[\]\{\}\+\-]', ' ', query)
        words = cleaned.split()
        return " ".join(words[:6])

    async def search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute precision searches across generated queries asynchronously.
        Returns a deduplicated list of raw article dictionaries.
        """
        if not self.is_configured():
            logger.info("NewsAPI key not configured; skipping NewsAPI search.")
            return []

        all_articles = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries[:3]:  # Top 3 queries to conserve quota
                clean_q = self._clean_query(query)
                if not clean_q or len(clean_q) < 3:
                    continue
                try:
                    params = {
                        "q": clean_q,
                        "apiKey": self.api_key,
                        "pageSize": min(settings.NEWS_API_LIMIT, 10),
                        "language": "en",
                        "sortBy": "relevancy"
                    }
                    response = await client.get(self.base_url, params=params)
                    articles = []

                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get("articles", [])
                    elif response.status_code == 429:
                        logger.warning("NewsAPI rate limit reached (429).")
                        break
                    else:
                        logger.warning(f"NewsAPI status {response.status_code} for query '{clean_q}'")

                    # If everything returned 0, try top-headlines fallback
                    if not articles and len(clean_q.split()) >= 1:
                        keyword = clean_q.split()[0]
                        hl_params = {
                            "q": keyword,
                            "apiKey": self.api_key,
                            "pageSize": 5,
                            "language": "en"
                        }
                        hl_resp = await client.get(self.top_headlines_url, params=hl_params)
                        if hl_resp.status_code == 200:
                            articles = hl_resp.json().get("articles", [])

                    for art in articles:
                        url = art.get("url")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            source_info = art.get("source", {})

                            content_parts = []
                            if art.get("description"):
                                content_parts.append(art["description"].strip())
                            if art.get("content"):
                                raw_c = re.sub(r'\[\+\d+ chars\]$', '', art["content"]).strip()
                                if raw_c and raw_c not in content_parts:
                                    content_parts.append(raw_c)

                            full_content = " ".join(content_parts) or art.get("title", "")

                            all_articles.append({
                                "title": art.get("title", "").strip(),
                                "url": url,
                                "source_name": source_info.get("name", "Unknown"),
                                "author": art.get("author"),
                                "published_at": art.get("publishedAt"),
                                "content": full_content,
                                "description": art.get("description", ""),
                                "search_provider": "newsapi",
                                "matched_query": clean_q
                            })
                except Exception as e:
                    logger.warning(f"NewsAPI request failed for query '{clean_q}': {e}")

        logger.info(f"NewsAPI retrieved {len(all_articles)} unique articles across {len(queries)} queries.")
        return all_articles
