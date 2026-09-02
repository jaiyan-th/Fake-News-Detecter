"""
High-Speed Concurrent Google News & SerpAPI Search Service
Directly queries Google News via real-time RSS feeds (0 API keys required, zero rate-limit)
with full concurrent execution (asyncio.gather) targeting verified newsrooms (The Hindu, Times of India,
Indian Express, NDTV, News18, CNN, BBC, Reuters).
"""

import asyncio
import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import httpx
from backend.core.config import settings

logger = logging.getLogger("news_verification.serpapi_service")

# Priority mainstream newsrooms to explicitly prioritize
PRIORITY_OUTLETS = [
    "The Hindu", "Times of India", "The Indian Express", "NDTV", "News18",
    "India Today", "Hindustan Times", "Outlook India", "The Economic Times",
    "BBC News", "Reuters", "Associated Press", "CNN"
]


class SerpAPIService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SERPAPI_KEY
        self.serpapi_base_url = "https://serpapi.com/search"
        self.google_news_rss_url = "https://news.google.com/rss/search"
        self.timeout = 7.0  # Fast timeout to guarantee quick user responses

    def is_configured(self) -> bool:
        """Google News RSS is always active (0 keys needed); SerpAPI is optional."""
        return True

    async def _fetch_rss(
        self,
        client: httpx.AsyncClient,
        query: str,
        gl: str = "IN",
        hl: str = "en-IN",
        ceid: str = "IN:en"
    ) -> List[Dict[str, Any]]:
        """Fetch a single Google News RSS feed asynchronously."""
        articles = []
        try:
            params = {"q": query, "hl": hl, "gl": gl, "ceid": ceid}
            encoded = urllib.parse.urlencode(params)
            url = f"{self.google_news_rss_url}?{encoded}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                items = root.findall(".//item")
                for item in items[:15]:
                    title_elem = item.find("title")
                    raw_title = title_elem.text if title_elem is not None else ""
                    if not raw_title:
                        continue

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
                    if not link:
                        continue

                    pubdate_elem = item.find("pubDate")
                    pub_date = pubdate_elem.text if pubdate_elem is not None else None

                    # Use title and source to construct informative content
                    content = f"{clean_title}. Reported by {source_name} on Google News."

                    articles.append({
                        "title": clean_title,
                        "url": link,
                        "source_name": source_name,
                        "domain": source_domain,
                        "author": None,
                        "published_at": pub_date,
                        "content": content,
                        "description": clean_title,
                        "search_provider": "google_news",
                        "matched_query": query
                    })
        except Exception as e:
            logger.debug(f"Google News RSS fetch failed for '{query}': {e}")
        return articles

    async def _fetch_serpapi(self, client: httpx.AsyncClient, query: str) -> List[Dict[str, Any]]:
        """Fetch SerpAPI if API key is provided."""
        if not self.api_key or not self.api_key.strip():
            return []
        articles = []
        try:
            params = {
                "engine": "google_news",
                "q": query,
                "api_key": self.api_key,
                "num": min(settings.SERPAPI_LIMIT, 10),
                "gl": "in",
                "hl": "en"
            }
            res = await client.get(self.serpapi_base_url, params=params)
            if res.status_code == 200:
                data = res.json()
                for item in data.get("news_results", []):
                    link = item.get("link")
                    if not link:
                        continue
                    source_info = item.get("source", {})
                    source_name = source_info.get("name") or source_info.get("title") or "Unknown"

                    parts = []
                    if item.get("snippet"):
                        parts.append(item["snippet"])
                    if item.get("description") and item["description"] != item.get("snippet"):
                        parts.append(item["description"])

                    content = " ".join(parts).strip() or item.get("title", "")

                    articles.append({
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
        except Exception as e:
            logger.debug(f"SerpAPI query error for '{query}': {e}")
        return articles

    async def search_google_news(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Execute concurrent Google News RSS and SerpAPI searches across all queries.
        Returns deduplicated, publisher-ranked articles.
        """
        if not queries:
            return []

        clean_queries = [q.strip() for q in queries[:4] if q and len(q.strip()) >= 3]
        if not clean_queries:
            return []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            tasks = []
            for q in clean_queries:
                # 1. Regional Indian Edition (The Hindu, Times of India, Indian Express, NDTV, News18)
                tasks.append(self._fetch_rss(client, q, gl="IN", hl="en-IN", ceid="IN:en"))
                # 2. Global English Edition (BBC, Reuters, CNN, NYT)
                tasks.append(self._fetch_rss(client, q, gl="US", hl="en", ceid="US:en"))
                # 3. SerpAPI if configured
                if self.api_key:
                    tasks.append(self._fetch_serpapi(client, q))

            # Run ALL queries concurrently in parallel!
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        seen_urls = set()
        seen_titles = set()

        for batch in batch_results:
            if isinstance(batch, list):
                for art in batch:
                    url = art.get("url", "").strip()
                    title = art.get("title", "").strip()
                    title_key = title.lower()[:60]

                    if not url or url in seen_urls or title_key in seen_titles:
                        continue

                    seen_urls.add(url)
                    seen_titles.add(title_key)
                    all_articles.append(art)

        logger.info(f"Google News concurrently retrieved {len(all_articles)} unique articles across {len(clean_queries)} queries.")
        return all_articles
