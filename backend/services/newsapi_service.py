"""
Async NewsAPI Search Service with Error Resilience and Rate Limit Protection
"""

import logging
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

    async def search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute searches across generated queries asynchronously.
        Returns a list of raw normalized article dictionaries.
        """
        if not self.is_configured():
            logger.warning("NewsAPI key not configured; skipping NewsAPI search.")
            return []

        all_articles = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries[:3]:  # query top 3 to conserve daily quota
                if not query.strip():
                    continue
                try:
                    params = {
                        "q": query,
                        "apiKey": self.api_key,
                        "pageSize": min(settings.NEWS_API_LIMIT, 10),
                        "language": "en",
                        "sortBy": "relevancy"
                    }
                    response = await client.get(self.base_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        articles = data.get("articles", [])
                        for art in articles:
                            url = art.get("url")
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                source_info = art.get("source", {})
                                all_articles.append({
                                    "title": art.get("title", ""),
                                    "url": url,
                                    "source_name": source_info.get("name", "Unknown"),
                                    "author": art.get("author"),
                                    "published_at": art.get("publishedAt"),
                                    "content": art.get("content") or art.get("description") or "",
                                    "description": art.get("description", ""),
                                    "search_provider": "newsapi",
                                    "matched_query": query
                                })
                    elif response.status_code == 429:
                        logger.warning("NewsAPI rate limit reached (429).")
                        break
                    else:
                        logger.warning(f"NewsAPI returned status {response.status_code} for query '{query}': {response.text}")
                except Exception as e:
                    logger.warning(f"NewsAPI request failed for query '{query}': {e}")

        logger.info(f"NewsAPI retrieved {len(all_articles)} unique articles across {len(queries)} queries.")
        return all_articles
