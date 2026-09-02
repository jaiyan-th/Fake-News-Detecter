"""
Async Google News & SerpAPI Search Service
Queries Google News directly via real-time RSS feeds (0 API keys needed, zero rate limits)
as well as SerpAPI when an optional API key is configured.
"""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from backend.core.config import settings

logger = logging.getLogger("news_verification.serpapi_service")


class SerpAPIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_KEY
        self.serpapi_base_url = "https://serpapi.com/search"
        self.google_news_rss_url = "https://news.google.com/rss/search"
        self.timeout = settings.REQUEST_TIMEOUT_SECONDS

    def is_configured(self) -> bool:
        """Google News RSS is always available (0 keys needed); SerpAPI is optional."""
        return True

    async def search_google_news(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Search Google News across queries using direct Google News RSS + SerpAPI (if configured).
        Returns deduplicated, normalized article dictionaries.
        """
        all_articles = []
        seen_urls = set()
        seen_titles = set()

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            # 1. Direct Google News RSS Search (High accuracy, live real-time, no API key required)
            for query in queries[:3]:
                if not query or len(query.strip()) < 3:
                    continue
                clean_q = query.strip()
                try:
                    # Query both global English and regional editions for maximum coverage
                    rss_params = [
                        {"q": clean_q, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
                        {"q": clean_q, "hl": "en", "gl": "US", "ceid": "US:en"}
                    ]
                    for param in rss_params:
                        encoded = urllib.parse.urlencode(param)
                        rss_url = f"{self.google_news_rss_url}?{encoded}"
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                        }
                        res = await client.get(rss_url, headers=headers)
                        if res.status_code == 200:
                            root = ET.fromstring(res.content)
                            items = root.findall(".//item")
                            for item in items[:settings.SERPAPI_LIMIT]:
                                title_elem = item.find("title")
                                raw_title = title_elem.text if title_elem is not None else ""
                                if not raw_title:
                                    continue

                                # Extract source name and clean title
                                source_elem = item.find("source")
                                if source_elem is not None and source_elem.text:
                                    source_name = source_elem.text.strip()
                                    source_domain = source_elem.attrib.get("url", "")
                                else:
                                    if " - " in raw_title:
                                        parts = raw_title.rsplit(" - ", 1)
                                        clean_title = parts[0].strip()
                                        source_name = parts[1].strip()
                                    else:
                                        clean_title = raw_title
                                        source_name = "Google News"
                                    source_domain = ""

                                clean_title = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title

                                link_elem = item.find("link")
                                link = link_elem.text if link_elem is not None else ""
                                if not link or link in seen_urls:
                                    continue

                                # Normalized title check to avoid duplicate stories
                                title_key = clean_title.lower()[:60]
                                if title_key in seen_titles:
                                    continue

                                seen_urls.add(link)
                                seen_titles.add(title_key)

                                pubdate_elem = item.find("pubDate")
                                pub_date = pubdate_elem.text if pubdate_elem is not None else None

                                all_articles.append({
                                    "title": clean_title,
                                    "url": link,
                                    "source_name": source_name,
                                    "domain": source_domain,
                                    "author": None,
                                    "published_at": pub_date,
                                    "content": f"{clean_title}. Reported by {source_name}.",
                                    "description": clean_title,
                                    "search_provider": "google_news",
                                    "matched_query": clean_q
                                })
                except Exception as e:
                    logger.warning(f"Google News RSS query failed for '{clean_q}': {e}")

            # 2. SerpAPI Search (if API key is provided)
            if self.api_key and self.api_key.strip():
                for query in queries[:2]:
                    clean_q = query.strip()
                    try:
                        params = {
                            "engine": "google_news",
                            "q": clean_q,
                            "api_key": self.api_key,
                            "num": min(settings.SERPAPI_LIMIT, 10),
                            "gl": "us",
                            "hl": "en"
                        }
                        response = await client.get(self.serpapi_base_url, params=params)
                        if response.status_code == 200:
                            data = response.json()
                            news_results = data.get("news_results", [])
                            for item in news_results:
                                link = item.get("link")
                                if link and link not in seen_urls:
                                    seen_urls.add(link)
                                    source_info = item.get("source", {})
                                    source_name = source_info.get("name") or source_info.get("title") or "Unknown"

                                    parts = []
                                    if item.get("snippet"):
                                        parts.append(item["snippet"])
                                    if item.get("description") and item["description"] != item.get("snippet"):
                                        parts.append(item["description"])

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
                                        "matched_query": clean_q
                                    })
                    except Exception as e:
                        logger.warning(f"SerpAPI request error on '{clean_q}': {e}")

        logger.info(f"Google News / SerpAPI retrieved {len(all_articles)} unique articles across queries.")
        return all_articles
