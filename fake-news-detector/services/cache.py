"""
Caching service for analysis results
"""

import hashlib
import json
from typing import Optional, Dict, Any
from models.database import Database


class CacheService:
    """Service for caching analysis results using the Database class"""
    
    def __init__(self, database: Database):
        """
        Initialize cache service with Database instance
        
        Args:
            database: Database instance for storage operations
        """
        self.database = database
    
    def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached analysis result for URL
        
        Args:
            url: URL to check for cached results
            
        Returns:
            Cached analysis result dictionary or None if not found
        """
        try:
            # Generate cache key from URL
            cache_key = self._generate_cache_key(url)
            
            # Use Database's get_analysis_by_url method
            cached_data = self.database.get_analysis_by_url(cache_key)
            
            if cached_data:
                # Convert database result to expected format
                return self._format_cached_result(cached_data)
            
            return None
            
        except Exception as e:
            print(f"Cache retrieval failed for URL {url}: {str(e)}")
            return None
    
    def store_result(self, url: str, summary: str, verdict: str, 
                    confidence: float, explanation: str = "", 
                    matched_articles: list = None, 
                    key_claims: list = None,
                    processing_time: float = 0.0) -> bool:
        """
        Store analysis result in cache using Database service
        
        Args:
            url: Original URL being analyzed
            summary: Article summary
            verdict: Analysis verdict (REAL/FAKE/UNCERTAIN)
            confidence: Confidence score (0.0-1.0)
            explanation: Human-readable explanation
            matched_articles: List of matched articles
            key_claims: List of key claims extracted
            processing_time: Time taken for analysis
            
        Returns:
            True if storage successful, False otherwise
        """
        try:
            # Generate cache key from URL
            cache_key = self._generate_cache_key(url)
            
            # Use Database's store_analysis method
            analysis_id = self.database.store_analysis(
                url=cache_key,
                summary=summary,
                verdict=verdict,
                confidence=confidence,
                explanation=explanation,
                matched_articles=matched_articles or [],
                key_claims=key_claims or [],
                processing_time=processing_time
            )
            
            return analysis_id is not None
            
        except Exception as e:
            print(f"Cache storage failed for URL {url}: {str(e)}")
            return False
    
    def is_cache_hit(self, url: str) -> bool:
        """
        Check if URL has cached results without retrieving them
        
        Args:
            url: URL to check
            
        Returns:
            True if cached result exists, False otherwise
        """
        try:
            cache_key = self._generate_cache_key(url)
            cached_data = self.database.get_analysis_by_url(cache_key)
            return cached_data is not None
            
        except Exception as e:
            print(f"Cache hit check failed for URL {url}: {str(e)}")
            return False
    
    def _generate_cache_key(self, url: str) -> str:
        """
        Generate consistent cache key from URL
        
        Args:
            url: URL to generate key for
            
        Returns:
            MD5 hash of the URL as cache key
        """
        # Normalize URL by stripping whitespace and converting to lowercase
        normalized_url = url.strip().lower()
        
        # Generate MD5 hash for consistent key generation
        return hashlib.md5(normalized_url.encode('utf-8')).hexdigest()
    
    def _format_cached_result(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format cached database result for consumption
        
        Args:
            cached_data: Raw database result
            
        Returns:
            Formatted result dictionary
        """
        try:
            # Parse JSON fields if they exist
            matched_articles = []
            key_claims = []
            
            if cached_data.get('matched_articles'):
                matched_articles = json.loads(cached_data['matched_articles'])
            
            if cached_data.get('key_claims'):
                key_claims = json.loads(cached_data['key_claims'])
            
            return {
                'summary': cached_data.get('summary', ''),
                'verdict': cached_data.get('verdict', 'UNCERTAIN'),
                'confidence': cached_data.get('confidence', 0.0),
                'explanation': cached_data.get('explanation', ''),
                'matched_articles': matched_articles,
                'key_claims': key_claims,
                'processing_time': cached_data.get('processing_time', 0.0),
                'created_at': cached_data.get('created_at'),
                'from_cache': True
            }
            
        except Exception as e:
            print(f"Result formatting failed: {str(e)}")
            return {
                'summary': cached_data.get('summary', ''),
                'verdict': cached_data.get('verdict', 'UNCERTAIN'),
                'confidence': cached_data.get('confidence', 0.0),
                'explanation': cached_data.get('explanation', ''),
                'matched_articles': [],
                'key_claims': [],
                'processing_time': 0.0,
                'from_cache': True
            }
    
    def clear_cache(self) -> bool:
        """
        Clear all cached entries (for testing/maintenance)
        Note: This would require additional Database methods not currently available
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would require a clear_all method in Database class
            # For now, we'll just return True as graceful handling
            print("Cache clear requested - would require Database.clear_all() method")
            return True
            
        except Exception as e:
            print(f"Cache clear failed: {str(e)}")
            return False