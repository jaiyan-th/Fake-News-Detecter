"""
News fetching service using News API with enhanced query optimization and retry logic
"""

from typing import List, Dict, Optional
import requests
import time
import random
import re
from services.extractor import ArticleContent

class NewsFetcher:
    """Service for fetching related news articles from multiple sources with fallback"""
    
    def __init__(self, api_key: str, limit: int = 15, serpapi_key: str = None):
        if not api_key:
            raise ValueError("News API key is required")
        self.api_key = api_key
        self.serpapi_key = serpapi_key
        self.limit = min(limit, 20)  # Cap at 20 for performance
        self.base_url = "https://newsapi.org/v2/everything"
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests
        self.max_retries = 3
        self.base_delay = 1  # Base delay for exponential backoff
        
        # Initialize SerpAPI if key is provided
        self.serpapi_fetcher = None
        if serpapi_key:
            try:
                from services.serpapi_fetcher import SerpAPIFetcher
                self.serpapi_fetcher = SerpAPIFetcher(serpapi_key, limit)
                print("✓ SerpAPI (Google News) initialized")
            except Exception as e:
                print(f"SerpAPI initialization failed: {str(e)}")
    
    def fetch_related_news(self, query: str, keywords: List[str] = None) -> List[ArticleContent]:
        """
        Fetch related news articles with intelligent fallback
        Tries SerpAPI (Google News) first, then falls back to NewsAPI
        
        Args:
            query: Main search query (usually article summary)
            keywords: Additional keywords to enhance search
            
        Returns:
            List of ArticleContent objects, sorted by relevance
        """
        articles = []
        
        # Try SerpAPI first (Google News - best coverage)
        if self.serpapi_fetcher:
            try:
                print(f"Trying SerpAPI (Google News) with query: {query[:100]}...")
                print(f"Keywords: {keywords}")
                articles = self.serpapi_fetcher.fetch_google_news(query, keywords)
                
                if articles and len(articles) > 0:
                    print(f"✓ SerpAPI returned {len(articles)} articles")
                    return articles
                else:
                    print("⚠ SerpAPI returned 0 articles, falling back to NewsAPI...")
            except Exception as e:
                print(f"✗ SerpAPI failed: {str(e)}, falling back to NewsAPI...")
        else:
            print("⚠ SerpAPI not initialized, using NewsAPI...")
        
        # Fallback to NewsAPI
        print("Using NewsAPI...")
        articles = self._fetch_from_newsapi(query, keywords)
        
        if articles:
            print(f"✓ NewsAPI returned {len(articles)} articles")
        else:
            print("✗ No articles found from any source")
        
        return articles
    
    def _fetch_from_newsapi(self, query: str, keywords: List[str] = None) -> List[ArticleContent]:
        """Fetch articles from NewsAPI with retry logic"""
        for attempt in range(self.max_retries + 1):
            try:
                # Build optimized search query
                search_query = self._build_optimized_search_query(query, keywords)
                
                # Rate limiting with exponential backoff
                self._enforce_rate_limit_with_backoff(attempt)
                
                # Make API request
                params = {
                    'q': search_query,
                    'apiKey': self.api_key,
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'pageSize': self.limit,
                    'excludeDomains': 'facebook.com,twitter.com,instagram.com,reddit.com',  # Exclude social media
                    'domains': self._get_trusted_domains()  # Focus on trusted sources
                }
                
                response = requests.get(self.base_url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('status') != 'ok':
                    error_msg = data.get('message', 'Unknown error')
                    if attempt < self.max_retries:
                        print(f"News API error (attempt {attempt + 1}): {error_msg}, retrying...")
                        continue
                    else:
                        raise ValueError(f"News API error: {error_msg}")
                
                articles = []
                for article_data in data.get('articles', []):
                    if self._is_valid_article(article_data):
                        article = self._convert_to_article_content(article_data)
                        articles.append(article)
                
                # Filter and rank by relevance
                filtered_articles = self._filter_and_rank_articles(articles, query, keywords)
                
                return filtered_articles[:self.limit]  # Return top results
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    print(f"Network error (attempt {attempt + 1}): {str(e)}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"News fetching failed after {self.max_retries + 1} attempts: {str(e)}")
                    return []
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self._calculate_backoff_delay(attempt)
                    print(f"Error (attempt {attempt + 1}): {str(e)}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"News fetching failed after {self.max_retries + 1} attempts: {str(e)}")
                    return []
        
        return []  # Return empty list if all attempts failed
    
    def _build_optimized_search_query(self, query: str, keywords: List[str] = None) -> str:
        """Build optimized search query focusing primarily on keywords for NewsAPI"""
        if keywords:
            # NewsAPI returns 0 results when given full sentences. 
            # We must exclusively use isolated keywords.
            relevant_keywords = self._select_relevant_keywords(keywords, "")
            # Join top 4 keywords
            keyword_str = " ".join(relevant_keywords[:4])
            return keyword_str.strip()
            
        if not query:
            return ""
            
        cleaned_query = self._extract_key_phrases(query)
        # Fallback: Just take the first few meaningful words from the summary
        words = [w for w in re.findall(r'\b[A-Za-z0-9]+\b', cleaned_query) if len(w) > 3]
        return " ".join(words[:4]).strip()
    
    def _extract_key_phrases(self, text: str) -> str:
        """Extract key phrases from text, removing filler words and focusing on important content"""
        # Remove common filler phrases
        filler_patterns = [
            r'\b(according to|reports suggest|it is believed|sources say|allegedly)\b',
            r'\b(in conclusion|furthermore|moreover|however|therefore)\b',
            r'\b(the article|this article|the report|this report)\b'
        ]
        
        cleaned_text = text
        for pattern in filler_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
        # Extract sentences with important keywords (who, what, where, when)
        important_sentences = []
        sentences = cleaned_text.split('.')
        
        for sentence in sentences[:3]:  # Focus on first 3 sentences
            sentence = sentence.strip()
            if len(sentence) > 20:  # Skip very short sentences
                # Prioritize sentences with proper nouns, numbers, or locations
                if re.search(r'[A-Z][a-z]+|[0-9]+|\b(in|at|from|to)\s+[A-Z]', sentence):
                    important_sentences.append(sentence)
        
        return '. '.join(important_sentences) if important_sentences else cleaned_text
    
    def _select_relevant_keywords(self, keywords: List[str], query: str) -> List[str]:
        """Select most relevant keywords based on context and importance"""
        if not keywords:
            return []
        
        # Score keywords based on various factors
        keyword_scores = []
        query_lower = query.lower()
        
        for keyword in keywords:
            score = 0
            keyword_lower = keyword.lower()
            
            # Higher score for keywords not already in query
            if keyword_lower not in query_lower:
                score += 3
            
            # Higher score for proper nouns (capitalized)
            if keyword[0].isupper():
                score += 2
            
            # Higher score for longer keywords (more specific)
            if len(keyword) > 5:
                score += 1
            
            # Higher score for keywords with numbers (dates, statistics)
            if re.search(r'[0-9]', keyword):
                score += 2
            
            keyword_scores.append((keyword, score))
        
        # Sort by score and return top keywords
        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in keyword_scores]
    
    def _get_trusted_domains(self) -> str:
        """Get comma-separated list of trusted news domains for better results"""
        trusted_domains = [
            # International Trusted Sources
            'bbc.com', 'bbc.co.uk', 'reuters.com', 'ap.org', 'apnews.com',
            'cnn.com', 'npr.org', 'theguardian.com', 'nytimes.com', 
            'washingtonpost.com', 'wsj.com', 'bloomberg.com',
            'aljazeera.com', 'france24.com', 'dw.com',
            
            # Major Indian News Sources (Most Popular & Trusted)
            'thehindu.com', 'indianexpress.com', 'timesofindia.indiatimes.com',
            'hindustantimes.com', 'ndtv.com', 'indiatoday.in',
            'news18.com', 'firstpost.com', 'thequint.com',
            'scroll.in', 'theprint.in', 'livemint.com', 'moneycontrol.com',
            
            # Regional Indian News
            'deccanherald.com', 'telegraphindia.com', 'tribuneindia.com',
            'theweek.in', 'outlookindia.com', 'businesstoday.in',
            'financialexpress.com', 'economictimes.indiatimes.com',
            
            # News Agencies
            'pti.org.in', 'ani.in', 'ians.in'
        ]
        return ','.join(trusted_domains)
    
    def _filter_and_rank_articles(self, articles: List[ArticleContent], query: str, keywords: List[str] = None) -> List[ArticleContent]:
        """Filter and rank articles by relevance to the original query"""
        if not articles:
            return []
        
        query_lower = query.lower() if query else ""
        keyword_set = set(kw.lower() for kw in (keywords or []))
        
        scored_articles = []
        
        for article in articles:
            score = 0
            title_lower = article.title.lower()
            content_lower = article.content.lower()
            
            # Score based on query terms in title (higher weight)
            query_words = query_lower.split()[:5]  # Top 5 words from query
            for word in query_words:
                if len(word) > 3:  # Skip short words
                    if word in title_lower:
                        score += 3
                    elif word in content_lower:
                        score += 1
            
            # Score based on keyword matches
            for keyword in keyword_set:
                if keyword in title_lower:
                    score += 2
                elif keyword in content_lower:
                    score += 1
            
            # Bonus for trusted sources
            if self._is_trusted_source(article.source):
                score += 2
            
            # Penalty for very short content
            if len(article.content) < 100:
                score -= 1
            
            scored_articles.append((article, score))
        
        # Sort by score (descending) and return articles
        scored_articles.sort(key=lambda x: x[1], reverse=True)
        return [article for article, score in scored_articles]
    
    def _is_trusted_source(self, source: str) -> bool:
        """Check if source is from a trusted news organization"""
        trusted_sources = {
            # International Trusted Sources
            'bbc', 'reuters', 'associated press', 'ap news', 'cnn', 'npr',
            'the guardian', 'guardian', 'new york times', 'nyt', 'washington post',
            'wall street journal', 'wsj', 'bloomberg', 'al jazeera', 'france 24', 'dw',
            
            # Major Indian News Sources (Most Popular & Trusted)
            'the hindu', 'hindu', 'indian express', 'times of india', 'toi',
            'hindustan times', 'ndtv', 'india today', 'news18', 'firstpost',
            'the quint', 'quint', 'scroll', 'the print', 'print', 'mint', 'livemint',
            'moneycontrol', 'money control',
            
            # Regional Indian News
            'deccan herald', 'telegraph', 'tribune', 'the week', 'outlook',
            'business today', 'financial express', 'economic times',
            
            # News Agencies
            'pti', 'press trust of india', 'ani', 'asian news international', 'ians'
        }
        
        source_lower = source.lower()
        return any(trusted in source_lower for trusted in trusted_sources)
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        # Exponential backoff: base_delay * (2 ^ attempt) + random jitter
        delay = self.base_delay * (2 ** attempt)
        # Add random jitter (±25% of delay)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.1, delay + jitter)  # Minimum 0.1 second delay
    
    def _enforce_rate_limit_with_backoff(self, attempt: int):
        """Enforce rate limiting with exponential backoff for retries"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Base rate limiting
        min_interval = self.min_request_interval
        
        # Increase interval for retries
        if attempt > 0:
            min_interval *= (2 ** attempt)
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def _is_valid_article(self, article_data: Dict) -> bool:
        """Check if article data is valid and useful with enhanced validation"""
        # Basic required fields
        if not all([
            article_data.get('title'),
            article_data.get('description'),
            article_data.get('url'),
            article_data.get('source', {}).get('name')
        ]):
            return False
        
        # Content quality checks
        description = article_data.get('description', '')
        title = article_data.get('title', '')
        
        # Minimum content length
        if len(description) < 50:
            return False
        
        # Filter out low-quality content
        low_quality_indicators = [
            '[removed]', '[deleted]', 'subscribe to read',
            'sign up to continue', 'paywall', 'premium content'
        ]
        
        content_lower = (title + ' ' + description).lower()
        if any(indicator in content_lower for indicator in low_quality_indicators):
            return False
        
        # Filter out non-news content
        non_news_indicators = [
            'advertisement', 'sponsored', 'promoted', 'ad:',
            'buy now', 'shop', 'sale', 'discount'
        ]
        
        if any(indicator in content_lower for indicator in non_news_indicators):
            return False
        
        return True
    
    def _convert_to_article_content(self, article_data: Dict) -> ArticleContent:
        """Convert News API response to ArticleContent object with enhanced content handling"""
        # Combine description and content, prioritizing description for quality
        description = article_data.get('description', '').strip()
        content = article_data.get('content', '').strip()
        
        # Use description as primary content, append content if it adds value
        if content and content != description and len(content) > len(description):
            # Remove common truncation indicators from content
            content = re.sub(r'\s*\[\+\d+\s+chars\]$', '', content)
            content = re.sub(r'\s*\.\.\.$', '', content)
            combined_content = f"{description} {content}".strip()
        else:
            combined_content = description
        
        # Clean up source name
        source_name = article_data['source']['name']
        # Remove common suffixes like ".com", "News", etc.
        source_name = re.sub(r'\.(com|org|net)$', '', source_name, flags=re.IGNORECASE)
        source_name = re.sub(r'\s+(News|Media|Press)$', '', source_name, flags=re.IGNORECASE)
        
        return ArticleContent(
            title=article_data['title'].strip(),
            content=combined_content,
            url=article_data['url'],
            source=source_name.strip(),
            published_date=article_data.get('publishedAt'),
            author=article_data.get('author')
        )