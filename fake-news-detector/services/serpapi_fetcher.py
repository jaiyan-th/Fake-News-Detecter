"""
SerpAPI Google News fetcher for comprehensive news coverage
"""

from typing import List, Dict
import requests
import time
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
        """Build optimized search query"""
        if keywords and len(keywords) > 0:
            # Use top 3-4 keywords
            return " ".join(keywords[:4])
        
        # Extract key words from query
        words = query.split()[:5]
        return " ".join(words)
    
    def _convert_to_article_content(self, item: Dict) -> ArticleContent:
        """Convert SerpAPI result to ArticleContent"""
        try:
            title = item.get('title', '')
            snippet = item.get('snippet', '')
            link = item.get('link', '')
            source = item.get('source', {}).get('name', 'Unknown')
            date = item.get('date', '')
            
            if not title or not link:
                return None
            
            # Combine snippet and any additional text
            content = snippet
            if 'stories' in item:
                # Add related stories content
                for story in item['stories'][:2]:
                    story_snippet = story.get('snippet', '')
                    if story_snippet:
                        content += f" {story_snippet}"
            
            return ArticleContent(
                title=title,
                content=content,
                url=link,
                source=source,
                published_date=date
            )
            
        except Exception as e:
            print(f"Error converting SerpAPI item: {str(e)}")
            return None
