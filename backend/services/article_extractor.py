"""
Article Content Extraction Service
Extracts readable title, content, publisher, and publication date from a news URL.
Uses newspaper3k with BeautifulSoup4 fallback and realistic user agents.
"""

import logging
from typing import Optional
from dataclasses import dataclass
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from backend.core.exceptions import ArticleExtractionError

logger = logging.getLogger("news_verification.article_extractor")


@dataclass
class ExtractedArticle:
    url: str
    title: str
    content: str
    publisher: str
    published_date: Optional[str] = None
    author: Optional[str] = None


class ArticleExtractor:
    def __init__(self, timeout: int = 12, min_length: int = 100):
        self.timeout = timeout
        self.min_length = min_length
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"
        ]

    def _validate_url(self, url: str) -> bool:
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def extract(self, url: str) -> ExtractedArticle:
        url = url.strip()
        if not self._validate_url(url):
            raise ArticleExtractionError("Invalid URL format. Must begin with http:// or https://")

        # 1. Attempt newspaper3k extraction
        try:
            from newspaper import Article, Config as NConfig
            cfg = NConfig()
            cfg.browser_user_agent = self._user_agents[0]
            cfg.request_timeout = self.timeout
            cfg.fetch_images = False
            cfg.memoize_articles = False

            article = Article(url, config=cfg)
            article.download()
            article.parse()

            title = (article.title or "").strip()
            content = (article.text or "").strip()
            author = ", ".join(article.authors) if article.authors else None
            pub_date = str(article.publish_date) if article.publish_date else None
            publisher = urlparse(url).netloc.replace("www.", "")

            if title and len(content) >= self.min_length:
                logger.info(f"Successfully extracted article via newspaper3k: '{title[:50]}...' ({len(content)} chars)")
                return ExtractedArticle(
                    url=url,
                    title=title,
                    content=content,
                    publisher=publisher,
                    published_date=pub_date,
                    author=author
                )
        except Exception as e:
            logger.warning(f"newspaper3k extraction failed for {url}: {e}, trying BeautifulSoup fallback...")

        # 2. BeautifulSoup fallback
        try:
            headers = {"User-Agent": self._user_agents[1], "Accept": "text/html,application/xhtml+xml"}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove noise
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
                tag.decompose()

            # Extract title
            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Extract body paragraphs
            paragraphs = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 30]
            content = "\n\n".join(paragraphs)

            # Extract date if available
            pub_date = None
            date_meta = soup.find("meta", property="article:published_time") or soup.find("meta", {"name": "pubdate"})
            if date_meta and date_meta.get("content"):
                pub_date = date_meta["content"].strip()

            publisher = urlparse(url).netloc.replace("www.", "")

            if title and len(content) >= self.min_length:
                logger.info(f"Successfully extracted article via BeautifulSoup: '{title[:50]}...'")
                return ExtractedArticle(
                    url=url,
                    title=title,
                    content=content,
                    publisher=publisher,
                    published_date=pub_date
                )
        except Exception as e:
            logger.error(f"BeautifulSoup fallback also failed for {url}: {e}")

        raise ArticleExtractionError(
            message="Unable to reliably extract text from this URL (it may be behind a paywall, blocked, or heavily client-rendered). Please paste the news text directly into the verification box.",
            details={"url": url}
        )
