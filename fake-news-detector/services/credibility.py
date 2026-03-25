"""
Credibility assessment service
"""

from typing import List, Dict
from services.similarity import SimilarityScore

class CredibilityAssessor:
    """Service for assessing source credibility and trustworthiness"""
    
    def __init__(self):
        self.trusted_sources = {
            # International Trusted Sources
            'bbc', 'reuters', 'associated press', 'ap news', 'cnn', 'npr',
            'pbs', 'the guardian', 'guardian', 'washington post', 'new york times', 'nyt',
            'wall street journal', 'wsj', 'abc news', 'cbs news', 'nbc news',
            'bloomberg', 'financial times', 'the economist', 'al jazeera', 'france 24', 'dw',
            
            # Major Indian News Sources (Most Popular & Trusted)
            'the hindu', 'hindu', 'indian express', 'times of india', 'toi',
            'hindustan times', 'ndtv', 'india today', 'news18', 'firstpost',
            'the quint', 'quint', 'scroll', 'the print', 'print', 'mint', 'livemint',
            'moneycontrol', 'money control',
            
            # Regional Indian News
            'deccan herald', 'telegraph india', 'tribune india', 'the week',
            'outlook india', 'business today', 'financial express', 'economic times',
            
            # News Agencies
            'pti', 'press trust of india', 'ani', 'asian news international', 'ians'
        }
        
        self.similarity_threshold = 0.7  # Threshold for high similarity
    
    def assess_credibility(self, similarity_scores: List[SimilarityScore]) -> Dict:
        """
        Assess overall credibility based on similarity scores and source trust
        
        Returns:
            Dict with credibility assessment metrics
        """
        if not similarity_scores:
            return {
                'trusted_matches': 0,
                'high_similarity_count': 0,
                'avg_similarity': 0.0,
                'trusted_ratio': 0.0,
                'support_ratio': 0.0,
                'credibility_score': 0.0
            }
        
        # Count trusted sources
        trusted_matches = sum(1 for score in similarity_scores if score.is_trusted)
        
        # Count high similarity matches
        high_similarity_count = sum(1 for score in similarity_scores if score.score > self.similarity_threshold)
        
        # Calculate average similarity
        avg_similarity = sum(score.score for score in similarity_scores) / len(similarity_scores)
        
        # Calculate ratios
        total_articles = len(similarity_scores)
        trusted_ratio = trusted_matches / total_articles if total_articles > 0 else 0.0
        support_ratio = high_similarity_count / total_articles if total_articles > 0 else 0.0
        
        # Calculate overall credibility score
        credibility_score = self._calculate_credibility_score(
            avg_similarity, trusted_ratio, support_ratio
        )
        
        return {
            'trusted_matches': trusted_matches,
            'high_similarity_count': high_similarity_count,
            'avg_similarity': avg_similarity,
            'trusted_ratio': trusted_ratio,
            'support_ratio': support_ratio,
            'credibility_score': credibility_score,
            'total_articles': total_articles
        }
    
    def is_trusted_source(self, source: str) -> bool:
        """Check if source is from a trusted news organization"""
        # Use the instance's trusted_sources set for consistency
        source_lower = source.lower()
        return any(trusted in source_lower for trusted in self.trusted_sources)
    
    def _calculate_credibility_score(self, avg_similarity: float, trusted_ratio: float, support_ratio: float) -> float:
        """
        Calculate overall credibility score using weighted formula
        Formula: 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        """
        credibility = 0.5 * avg_similarity + 0.3 * trusted_ratio + 0.2 * support_ratio
        
        # Clamp between 0.0 and 1.0
        return max(0.0, min(1.0, credibility))
    
    def get_trusted_sources(self) -> List[str]:
        """Get list of trusted sources"""
        return sorted(list(self.trusted_sources))
    
    def add_trusted_source(self, source: str):
        """Add a new trusted source"""
        if source:
            self.trusted_sources.add(source.lower())
    
    def remove_trusted_source(self, source: str):
        """Remove a trusted source"""
        if source:
            self.trusted_sources.discard(source.lower())