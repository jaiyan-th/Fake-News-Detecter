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
    
    def extract_content(self, url: str) -> ArticleContent:
        """Extract article content from URL"""
        # Sanitize URL first
        url = self.sanitize_url(url)
        
        # Validate URL format
        if not self.validate_url(url):
            raise ValueError("Invalid URL format - only HTTP/HTTPS URLs are allowed")
        
        try:
            # Use newspaper3k for content extraction with a realistic user agent
            from newspaper import Config
            config = Config()
            config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            config.request_timeout = self.timeout
            
            article = Article(url, config=config)
            article.download()
            article.parse()
            
            # Check if we got meaningful content
            if not article.title or not article.text:
                raise ValueError("Unable to extract meaningful content from URL - page may not contain article content")
            
            # Validate content length
            content = article.text.strip()
            if len(content) < self.min_content_length:
                # Content too short - return UNCERTAIN verdict will be handled by decision engine
                pass  # Don't raise error, let the system handle short content
            
            # Extract source domain from URL
            parsed_url = urlparse(url)
            source = parsed_url.netloc.lower()
            # Remove www. prefix if present
            if source.startswith('www.'):
                source = source[4:]
            
            # Format published date if available
            published_date = None
            if article.publish_date:
                try:
                    published_date = article.publish_date.isoformat()
                except:
                    published_date = str(article.publish_date)
            
            # Format authors if available
            author = None
            if article.authors:
                author = ', '.join(article.authors)
            
            return ArticleContent(
                title=article.title.strip(),
                content=content,
                url=url,
                source=source,
                published_date=published_date,
                author=author
            )
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Network error accessing URL: {str(e)}")
        except Exception as e:
            if "Unable to extract" in str(e):
                raise  # Re-raise our custom errors
            raise ValueError(f"Content extraction failed: {str(e)}")
    
    def is_content_sufficient(self, content: str) -> bool:
        """Check if extracted content meets minimum length requirements"""
        return len(content.strip()) >= self.min_content_length