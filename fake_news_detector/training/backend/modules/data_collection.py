"""
Module 1: Data Collection Layer
Collects news data from various sources including APIs, social media, and web scraping
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    """Handles data collection from multiple sources"""
    
    def __init__(self, news_api_key: Optional[str] = None):
        self.news_api_key = news_api_key
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def collect_from_url(self, url: str) -> Dict:
        """
        Scrape news article from URL with improved error handling
        
        Args:
            url: Article URL
            
        Returns:
            Dictionary with article data
        """
        try:
            # Validate URL format
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Add more comprehensive headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Make request with better error handling
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title with multiple fallbacks
            title = ""
            title_selectors = [
                'h1',
                'title',
                '.headline',
                '.article-title',
                '[data-testid="headline"]',
                '.entry-title'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break
            
            # Extract article content with multiple strategies
            content = ""
            
            # Strategy 1: Look for article tags
            article_selectors = [
                'article',
                '.article-body',
                '.story-body',
                '.entry-content',
                '.post-content',
                '.article-content',
                '[data-testid="article-body"]',
                '.content'
            ]
            
            for selector in article_selectors:
                article_elem = soup.select_one(selector)
                if article_elem:
                    paragraphs = article_elem.find_all('p')
                    if paragraphs:
                        content = ' '.join([p.get_text().strip() for p in paragraphs])
                        break
            
            # Strategy 2: If no article content found, get all paragraphs
            if not content:
                paragraphs = soup.find_all('p')
                if paragraphs:
                    # Filter out short paragraphs (likely navigation/footer)
                    long_paragraphs = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 50]
                    content = ' '.join(long_paragraphs[:15])  # Take first 15 substantial paragraphs
            
            # Strategy 3: Fallback to any text content
            if not content:
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                content = soup.get_text()
                # Clean up whitespace
                lines = (line.strip() for line in content.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                content = ' '.join(chunk for chunk in chunks if chunk)[:2000]  # Limit length
            
            # Extract metadata with fallbacks
            author = "Unknown"
            author_selectors = [
                'meta[name="author"]',
                'meta[property="article:author"]',
                '.author',
                '.byline',
                '[data-testid="author"]'
            ]
            
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    if author_elem.name == 'meta':
                        author = author_elem.get('content', 'Unknown')
                    else:
                        author = author_elem.get_text().strip()
                    break
            
            # Extract publish date
            publish_date = ""
            date_selectors = [
                'meta[property="article:published_time"]',
                'meta[name="publish_date"]',
                'time[datetime]',
                '.publish-date',
                '.date'
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    if date_elem.name == 'meta':
                        publish_date = date_elem.get('content', '')
                    elif date_elem.name == 'time':
                        publish_date = date_elem.get('datetime', date_elem.get_text().strip())
                    else:
                        publish_date = date_elem.get_text().strip()
                    break
            
            # Validate extracted content
            if not title and not content:
                raise Exception("Could not extract meaningful content from the webpage")
            
            if len(content) < 100:
                logger.warning(f"Short content extracted from {url}: {len(content)} characters")
            
            return {
                'url': url,
                'title': title or "Untitled Article",
                'content': content,
                'author': author,
                'publish_date': publish_date,
                'source': self._extract_domain(url),
                'collection_method': 'web_scraping',
                'content_length': len(content),
                'success': True
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error accessing {url}: {str(e)}"
            logger.error(error_msg)
            return {
                'url': url,
                'error': error_msg,
                'collection_method': 'web_scraping',
                'success': False
            }
        except Exception as e:
            error_msg = f"Error processing {url}: {str(e)}"
            logger.error(error_msg)
            return {
                'url': url,
                'error': error_msg,
                'collection_method': 'web_scraping',
                'success': False
            }
    
    def collect_from_news_api(self, query: str, page_size: int = 10) -> List[Dict]:
        """
        Collect news from News API
        
        Args:
            query: Search query
            page_size: Number of articles to fetch
            
        Returns:
            List of article dictionaries
        """
        if not self.news_api_key:
            logger.warning("News API key not provided")
            return []
        
        try:
            url = f"https://newsapi.org/v2/everything"
            params = {
                'q': query,
                'apiKey': self.news_api_key,
                'pageSize': page_size,
                'language': 'en'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'content': article.get('content', '') or article.get('description', ''),
                    'author': article.get('author', 'Unknown'),
                    'publish_date': article.get('publishedAt', ''),
                    'source': article.get('source', {}).get('name', ''),
                    'url': article.get('url', ''),
                    'collection_method': 'news_api'
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error collecting from News API: {str(e)}")
            return []
    
    def collect_from_text(self, text: str, title: str = "") -> Dict:
        """
        Process user-provided text input
        
        Args:
            text: Article text
            title: Article title (optional)
            
        Returns:
            Dictionary with article data
        """
        return {
            'title': title,
            'content': text,
            'author': 'User Input',
            'publish_date': '',
            'source': 'manual_input',
            'collection_method': 'user_input'
        }
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
