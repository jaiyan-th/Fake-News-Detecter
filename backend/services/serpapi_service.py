"""
Async SerpAPI Google News Search Service
Provides broad Google News real-time retrieval as a complement and fallback to NewsAPI.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx
from backend.core.config import settings

logger = logging.getLogger("news_verification.serpapi_service")


class SerpAPIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_KEY
        self.base_url = "https://serpapi.com/search"
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    async def search_google_news(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute Google News search via SerpAPI asynchronously.
        """
        if not self.is_configured():
            logger.info("SerpAPI key not configured; skipping SerpAPI search.")
            return []

        all_articles = []
        seen_urls = set()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for query in queries[:2]:  # Query top 2 to preserve quota
                if not query.strip():
                    continue
                try:
                    params = {
                        "engine": "google_news",
                        "q": query,
                        "api_key": self.api_key,
                        "num": min(settings.SERPAPI_LIMIT, 10),
                        "gl": "us",
                        "hl": "en"
                    }
                    response = await client.get(self.base_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        news_results = data.get("news_results", [])
                        for item in news_results:
                            link = item.get("link")
                            if link and link not in seen_urls:
                                seen_urls.add(link)
                                source_info = item.get("source", {})
                                source_name = source_info.get("name") or source_info.get("title") or "Unknown"

                                # Aggregate snippet content
                                parts = []
                                if item.get("snippet"):
                                    parts.append(item["snippet"])
                                if item.get("description") and item["description"] != item.get("snippet"):
                                    parts.append(item["description"])
                                for story in item.get("stories", [])[:2]:
                                    if story.get("snippet"):
                                        parts.append(story["snippet"])
                                    elif story.get("title"):
                                        parts.append(story["title"])

                                content = " ".join(parts).strip() or item.get("title", "")

                                all_articles.append({
                                    "title": item.get("title", ""),
                                    "url": link,
                                    "source_name": source_name,
                                    "author": None,
                                    "published_at": item.get("date"),
                                    "content": content,
                                    "description": item.get("snippet", ""),
                                    "search_provider": "serpapi",
                                    "matched_query": query
                                })
                    else:
                        logger.warning(f"SerpAPI returned status {response.status_code} for '{query}'")
                except Exception as e:
                    logger.warning(f"SerpAPI request error on '{query}': {e}")

        logger.info(f"SerpAPI retrieved {len(all_articles)} unique articles across {len(queries)} queries.")
        return all_articles
