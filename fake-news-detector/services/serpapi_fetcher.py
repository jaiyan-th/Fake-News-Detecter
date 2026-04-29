"""
SerpAPI Google News fetcher for comprehensive news coverage
"""

from typing import List, Dict
import requests
import time
import re
from services.extractor import ArticleContent

class SerpAPIFetcher:
    """Service for fetching news articles from Google News via SerpAPI"""
    
    def __init__(self, api_key: str, limit: int = 15):
        if not api_key:
            raise ValueError("SerpAPI key is required")
        self.api_key = api_key
        self.limit = min(limit, 20)
        self.base_url = "https://serpapi.com/search"
    
    def fetch_google_news(self, query: str, keywords: List[str] = None) -> List[ArticleContent]:
        """
        Fetch news articles from Google News via SerpAPI
        
        Args:
            query: Search query
            keywords: Additional keywords
            
        Returns:
            List of ArticleContent objects
        """
        try:
            # Build search query
            search_query = self._build_search_query(query, keywords)
            
            # Make API request
            params = {
                'engine': 'google_news',
                'q': search_query,
                'api_key': self.api_key,
                'num': self.limit,
                'gl': 'us',  # Country
                'hl': 'en'   # Language
            }
            
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            articles = []
            news_results = data.get('news_results', [])
            
            for item in news_results[:self.limit]:
                article = self._convert_to_article_content(item)
                if article:
                    articles.append(article)
            
            print(f"SerpAPI: Found {len(articles)} articles")
            return articles
            
        except Exception as e:
            print(f"SerpAPI fetch failed: {str(e)}")
            return []
    
    def _build_search_query(self, query: str, keywords: List[str] = None) -> str:
        """
        Build optimized search query for Google News.
        Uses the full normalized claim (up to 10 words) for best results,
        supplemented by top keywords.
        """
        # Clean the query — remove filler but keep proper nouns and key terms
        clean = re.sub(r'\s+', ' ', query).strip()

        # If we have a rich query (sentence), extract the most important words
        words = clean.split()
        stop = {'the','a','an','and','or','but','in','on','at','to','for',
                'of','is','was','are','were','be','been','that','this',
                'with','from','by','as','it','its','will','has','have'}

        # Keep proper nouns and meaningful words, up to 8 terms
        key_words = [w for w in words if w.lower() not in stop and len(w) > 2][:8]

        if key_words:
            return ' '.join(key_words)

        # Fallback to provided keywords
        if keywords:
            return ' '.join(keywords[:6])

        return ' '.join(words[:6])
    
    def _convert_to_article_content(self, item: Dict) -> ArticleContent:
        """Convert SerpAPI result to ArticleContent."""
        try:
            title   = item.get('title', '').strip()
            link    = item.get('link', '').strip()
            source_info = item.get('source', {})
            source  = (source_info.get('name') or
                       source_info.get('title') or 'Unknown').strip()
            date    = item.get('date', '')

            if not title or not link:
                return None

            # Build content from all available text fields
            parts = []

            # snippet (sometimes present)
            snippet = item.get('snippet', '').strip()
            if snippet:
                parts.append(snippet)

            # description (alternate field)
            desc = item.get('description', '').strip()
            if desc and desc != snippet:
                parts.append(desc)

            # related stories snippets
            for story in item.get('stories', [])[:3]:
                s = story.get('snippet', '').strip()
                if s:
                    parts.append(s)
                t = story.get('title', '').strip()
                if t and t != title:
                    parts.append(t)

            # highlights
            for h in item.get('highlights', [])[:2]:
                if isinstance(h, str):
                    parts.append(h)

            # If still empty, use the title itself as content
            # (enough for keyword overlap and stance detection)
            content = ' '.join(parts).strip() if parts else title

            return ArticleContent(
                title=title,
                content=content,
                url=link,
                source=source,
                published_date=date,
            )
        except Exception as e:
            print(f"Error converting SerpAPI item: {e}")
            return None
