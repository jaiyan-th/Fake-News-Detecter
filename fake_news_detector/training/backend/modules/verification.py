"""
Module 5: Fake News Verification Layer
Cross-checks with fact-checking websites and trusted sources
"""

import requests
from typing import Dict, List, Optional
import logging
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsVerifier:
    """Verifies news against fact-checking sources and trusted databases"""
    
    def __init__(self):
        self.trusted_sources = {
            # High credibility sources
            'reuters.com': 0.95,
            'apnews.com': 0.95,
            'bbc.com': 0.90,
            'npr.org': 0.90,
            'theguardian.com': 0.85,
            'nytimes.com': 0.85,
            'washingtonpost.com': 0.85,
            'wsj.com': 0.85,
            'economist.com': 0.85,
            'bloomberg.com': 0.85,
            
            # Medium credibility
            'cnn.com': 0.75,
            'foxnews.com': 0.70,
            'usatoday.com': 0.75,
            'time.com': 0.75,
            'newsweek.com': 0.70,
            
            # Fact-checking sites
            'snopes.com': 0.90,
            'factcheck.org': 0.90,
            'politifact.com': 0.90,
            'fullfact.org': 0.85,
        }
        
        self.known_fake_sources = {
            'theonion.com': 'satire',
            'clickhole.com': 'satire',
            'beforeitsnews.com': 'unreliable',
            'naturalnews.com': 'unreliable',
            'infowars.com': 'unreliable',
        }
    
    def verify_source_credibility(self, source: str) -> Dict:
        """
        Check source credibility
        
        Args:
            source: Domain name or source identifier
            
        Returns:
            Dictionary with credibility score and status
        """
        source_lower = source.lower()
        
        # Check if known fake/unreliable source
        for fake_source, reason in self.known_fake_sources.items():
            if fake_source in source_lower:
                return {
                    'credibility_score': 0.1,
                    'status': 'unreliable',
                    'reason': reason,
                    'verified': True
                }
        
        # Check if trusted source
        for trusted_source, score in self.trusted_sources.items():
            if trusted_source in source_lower:
                return {
                    'credibility_score': score,
                    'status': 'trusted',
                    'reason': 'established news organization',
                    'verified': True
                }
        
        # Unknown source
        return {
            'credibility_score': 0.5,
            'status': 'unknown',
            'reason': 'source not in database',
            'verified': False
        }
    
    def check_fact_checking_sites(self, title: str, content: str) -> Dict:
        """
        Search fact-checking websites for similar claims
        
        Args:
            title: Article title
            content: Article content
            
        Returns:
            Dictionary with fact-check results
        """
        # Extract key claims (simplified - first sentence or title)
        claim = title if title else content[:200]
        
        results = {
            'checked': False,
            'matches_found': 0,
            'fact_check_results': [],
            'overall_verdict': 'not_found'
        }
        
        # In a production system, this would query actual fact-checking APIs
        # For now, we'll use keyword matching as a demonstration
        
        fake_indicators = ['hoax', 'debunked', 'false', 'fake', 'misleading', 'unverified']
        claim_lower = claim.lower()
        
        # Simple heuristic check
        if any(indicator in claim_lower for indicator in fake_indicators):
            results['checked'] = True
            results['matches_found'] = 1
            results['fact_check_results'].append({
                'source': 'keyword_analysis',
                'verdict': 'suspicious',
                'confidence': 0.6
            })
            results['overall_verdict'] = 'suspicious'
        
        return results
    
    def cross_reference_trusted_sources(self, title: str, keywords: List[str]) -> Dict:
        """
        Check if similar stories exist in trusted sources
        
        Args:
            title: Article title
            keywords: List of keywords to search
            
        Returns:
            Dictionary with cross-reference results
        """
        results = {
            'similar_articles_found': 0,
            'trusted_sources_reporting': [],
            'coverage_score': 0.0
        }
        
        # In production, this would use news APIs to search trusted sources
        # For demonstration, we'll use a simplified approach
        
        # Simulate checking if major outlets are covering the story
        # This would be replaced with actual API calls
        
        return results
    
    def verify_article(self, article: Dict, prediction: str, confidence: float) -> Dict:
        """
        Complete verification process
        
        Args:
            article: Article dictionary
            prediction: ML model prediction
            confidence: Model confidence score
            
        Returns:
            Comprehensive verification results
        """
        source = article.get('source', 'unknown')
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Step 1: Source credibility check
        source_check = self.verify_source_credibility(source)
        
        # Step 2: Fact-checking sites
        fact_check = self.check_fact_checking_sites(title, content)
        
        # Step 3: Cross-reference with trusted sources
        cross_ref = self.cross_reference_trusted_sources(title, [])
        
        # Combine results
        verification_result = {
            'source_verification': source_check,
            'fact_check': fact_check,
            'cross_reference': cross_ref,
            'ml_prediction': prediction,
            'ml_confidence': confidence,
        }
        
        # Calculate final verdict
        verification_result['final_verdict'] = self._calculate_final_verdict(
            source_check, fact_check, prediction, confidence
        )
        
        return verification_result
    
    def _calculate_final_verdict(self, source_check: Dict, fact_check: Dict, 
                                 prediction: str, confidence: float) -> Dict:
        """
        Calculate final verdict combining all verification methods
        
        Returns:
            Dictionary with final verdict and reasoning
        """
        # Weight different factors
        source_weight = 0.3
        fact_check_weight = 0.2
        ml_weight = 0.5
        
        # Calculate composite score
        source_score = source_check['credibility_score']
        
        # Fact-check score
        if fact_check['overall_verdict'] == 'suspicious':
            fact_score = 0.2
        elif fact_check['overall_verdict'] == 'verified':
            fact_score = 0.9
        else:
            fact_score = 0.5
        
        # ML score (convert FAKE/REAL to numeric)
        ml_score = confidence if prediction == "REAL" else (1 - confidence)
        
        # Weighted average
        final_score = (source_score * source_weight + 
                      fact_score * fact_check_weight + 
                      ml_score * ml_weight)
        
        # Determine verdict
        if final_score > 0.7:
            verdict = "LIKELY REAL"
            confidence_level = "High"
        elif final_score > 0.5:
            verdict = "UNCERTAIN"
            confidence_level = "Medium"
        else:
            verdict = "LIKELY FAKE"
            confidence_level = "High" if final_score < 0.3 else "Medium"
        
        reasons = []
        if source_check['status'] == 'unreliable':
            reasons.append('unverified source')
        if fact_check['overall_verdict'] == 'suspicious':
            reasons.append('flagged by fact-checkers')
        if prediction == "FAKE" and confidence > 0.7:
            reasons.append('ML model high confidence fake detection')
        
        return {
            'verdict': verdict,
            'confidence_level': confidence_level,
            'composite_score': final_score,
            'reasons': reasons
        }
