"""
Content extraction service for news articles
"""

from typing import Optional
from dataclasses import dataclass
import requests
from newspaper import Article
import re
from urllib.parse import urlparse

@dataclass
class ArticleContent:
    title: str
    content: str
    url: str
    source: str
    published_date: Optional[str] = None
    author: Optional[str] = None

class ContentExtractor:
    """Service for extracting article content from URLs"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.min_content_length = 200  # Minimum content length for valid articles
    
    def validate_url(self, url: str) -> bool:
        """Validate URL format and protocol"""
        if not url or not isinstance(url, str):
            return False
        
        try:
            # Parse URL to validate structure
            parsed = urlparse(url)
            
            # Check for valid HTTP/HTTPS protocol only
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for valid domain
            if not parsed.netloc:
                return False
            
            return True
            
        except Exception:
            return False
    
    def sanitize_url(self, url: str) -> str:
        """Sanitize URL by removing potentially dangerous elements"""
        # Remove any whitespace
        url = url.strip()
        
        # Basic URL sanitization - ensure it starts with http/https
        if not url.startswith(('http://', 'https://')):
            # Don't auto-add protocol, let validation catch this
            pass
        
        return url
    
    # Rotate through several realistic user-agents to avoid blocks
    _USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
        '(KHTML, like Gecko) Version/17.4 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0',
    ]

    def extract_content(self, url: str) -> ArticleContent:
        """
        Extract article content from URL.
        Strategy:
          1. newspaper3k (fast, handles most sites)
          2. requests + BeautifulSoup fallback (handles paywalled/JS-lite pages)
          3. Meta-tag only fallback (title + description when body is blocked)
        """
        url = self.sanitize_url(url)
        if not self.validate_url(url):
            raise ValueError("Invalid URL format - only HTTP/HTTPS URLs are allowed")

        # --- Attempt 1: newspaper3k ---
        try:
            from newspaper import Config as NConfig
            cfg = NConfig()
            cfg.browser_user_agent = self._USER_AGENTS[0]
            cfg.request_timeout = self.timeout
            cfg.fetch_images = False
            cfg.memoize_articles = False

            art = Article(url, config=cfg)
            art.download()
            art.parse()

            title   = (art.title or "").strip()
            content = (art.text  or "").strip()

            if title and len(content) >= self.min_content_length:
                return self._build_result(url, title, content,
                                          art.publish_date, art.authors)
        except Exception:
            pass

        # --- Attempt 2: requests + BeautifulSoup ---
        try:
            from bs4 import BeautifulSoup
            import random

            headers = {
                'User-Agent': random.choice(self._USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            resp = requests.get(url, headers=headers,
                                timeout=self.timeout, allow_redirects=True)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove noise
            for tag in soup(['script', 'style', 'nav', 'footer',
                             'header', 'aside', 'form', 'noscript']):
                tag.decompose()

            # Title
            title = ""
            if soup.title:
                title = soup.title.get_text(strip=True)
            if not title:
                og = soup.find('meta', property='og:title')
                if og:
                    title = og.get('content', '').strip()

            # Body text — try article/main first, then paragraphs
            body_text = ""
            for selector in ['article', 'main', '[role="main"]',
                              '.article-body', '.story-body',
                              '.article__body', '.post-content',
                              '#article-body', '.entry-content']:
                node = soup.select_one(selector)
                if node:
                    body_text = node.get_text(separator=' ', strip=True)
                    if len(body_text) >= self.min_content_length:
                        break

            # Fallback: all <p> tags
            if len(body_text) < self.min_content_length:
                paras = soup.find_all('p')
                body_text = ' '.join(p.get_text(strip=True) for p in paras
                                     if len(p.get_text(strip=True)) > 40)

            # Meta description as last resort for content
            if len(body_text) < 100:
                for attr in [('name', 'description'),
                              ('property', 'og:description'),
                              ('name', 'twitter:description')]:
                    meta = soup.find('meta', {attr[0]: attr[1]})
                    if meta and meta.get('content'):
                        body_text = meta['content'].strip()
                        break

            content = body_text.strip()

            if title and len(content) >= 50:
                return self._build_result(url, title, content, None, [])

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error accessing URL: {str(e)}")
        except Exception:
            pass

        # --- Attempt 3: meta-only (title + og:description) ---
        try:
            from bs4 import BeautifulSoup
            headers = {'User-Agent': self._USER_AGENTS[0]}
            resp = requests.get(url, headers=headers,
                                timeout=self.timeout, allow_redirects=True)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = ""
            if soup.title:
                title = soup.title.get_text(strip=True)

            description = ""
            for attr in [('property', 'og:description'),
                          ('name', 'description'),
                          ('name', 'twitter:description')]:
                meta = soup.find('meta', {attr[0]: attr[1]})
                if meta and meta.get('content'):
                    description = meta['content'].strip()
                    break

            if title:
                content = description if description else title
                return self._build_result(url, title, content, None, [])
        except Exception:
            pass

        raise ValueError(
            "Unable to extract meaningful content from URL — "
            "the page may be paywalled, JavaScript-rendered, or blocking scrapers."
        )

    def _build_result(self, url: str, title: str, content: str,
                      publish_date, authors) -> ArticleContent:
        """Build ArticleContent from extracted parts."""
        parsed_url = urlparse(url)
        source = parsed_url.netloc.lower()
        if source.startswith('www.'):
            source = source[4:]

        published_date = None
        if publish_date:
            try:
                published_date = publish_date.isoformat()
            except Exception:
                published_date = str(publish_date)

        author = None
        if authors:
            author = ', '.join(authors)

        return ArticleContent(
            title=title,
            content=content,
            url=url,
            source=source,
            published_date=published_date,
            author=author,
        )
    
    def is_content_sufficient(self, content: str) -> bool:
        """Check if extracted content meets minimum length requirements"""
        return len(content.strip()) >= self.min_content_length