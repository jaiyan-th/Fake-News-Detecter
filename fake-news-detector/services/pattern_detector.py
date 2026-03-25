"""
Fake news pattern detection service
Detects common patterns and indicators associated with fake news
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

@dataclass
class PatternResult:
    """Result of pattern detection analysis"""
    overall_score: float
    patterns_detected: List[str]
    pattern_scores: Dict[str, float]
    emotional_indicators: List[str]
    suspicious_phrases: List[str]
    credibility_flags: List[str]

class PatternDetector:
    """Service for detecting fake news patterns and indicators"""
    
    def __init__(self):
        """Initialize pattern detector with predefined patterns"""
        
        # Emotional language patterns (high emotional charge)
        self.emotional_patterns = {
            'excessive_caps': {
                'pattern': r'[A-Z]{3,}',
                'weight': 0.3,
                'description': 'Excessive capitalization'
            },
            'multiple_exclamation': {
                'pattern': r'!{2,}',
                'weight': 0.2,
                'description': 'Multiple exclamation marks'
            },
            'emotional_words': {
                'words': [
                    'shocking', 'unbelievable', 'incredible', 'amazing', 'outrageous',
                    'devastating', 'terrifying', 'horrifying', 'scandalous', 'explosive',
                    'bombshell', 'exclusive', 'breaking', 'urgent', 'critical'
                ],
                'weight': 0.4,
                'description': 'High-emotion words'
            },
            'sensational_phrases': {
                'phrases': [
                    'you won\'t believe', 'doctors hate', 'this will shock you',
                    'they don\'t want you to know', 'secret revealed', 'hidden truth',
                    'mainstream media won\'t tell you', 'what they\'re hiding'
                ],
                'weight': 0.5,
                'description': 'Sensational phrases'
            }
        }
        
        # Suspicious content patterns
        self.suspicious_patterns = {
            'vague_sources': {
                'phrases': [
                    'sources say', 'experts claim', 'studies show', 'reports suggest',
                    'it is believed', 'according to sources', 'unnamed officials',
                    'insiders reveal', 'leaked documents'
                ],
                'weight': 0.3,
                'description': 'Vague source references'
            },
            'absolute_statements': {
                'words': [
                    'always', 'never', 'all', 'every', 'none', 'completely',
                    'totally', 'absolutely', 'definitely', 'certainly', 'guaranteed'
                ],
                'weight': 0.2,
                'description': 'Absolute statements'
            },
            'conspiracy_language': {
                'phrases': [
                    'cover up', 'conspiracy', 'they\'re hiding', 'secret agenda',
                    'wake up', 'open your eyes', 'the truth is', 'real story',
                    'what really happened', 'behind the scenes'
                ],
                'weight': 0.4,
                'description': 'Conspiracy-related language'
            }
        }
        
        # Credibility warning patterns
        self.credibility_patterns = {
            'poor_grammar': {
                'patterns': [
                    r'\b(there|their|they\'re)\b.*\b(there|their|they\'re)\b',  # Common mix-ups
                    r'\b(your|you\'re)\b.*\b(your|you\'re)\b',
                    r'[.!?]\s*[a-z]',  # Lowercase after punctuation
                    r'\s{2,}',  # Multiple spaces
                ],
                'weight': 0.2,
                'description': 'Poor grammar/spelling'
            },
            'clickbait_numbers': {
                'pattern': r'\b\d+\s+(reasons|ways|things|facts|secrets|tricks)\b',
                'weight': 0.3,
                'description': 'Clickbait number patterns'
            },
            'excessive_punctuation': {
                'pattern': r'[.!?]{3,}',
                'weight': 0.2,
                'description': 'Excessive punctuation'
            }
        }
        
        # Positive credibility indicators (reduce fake news score)
        self.credibility_indicators = {
            'specific_dates': {
                'pattern': r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                'weight': -0.1,
                'description': 'Specific dates mentioned'
            },
            'quotes_attribution': {
                'pattern': r'"[^"]*"\s*,?\s*(said|stated|explained|noted|commented|according to)\s+[A-Z][a-z]+',
                'weight': -0.2,
                'description': 'Properly attributed quotes'
            },
            'statistical_data': {
                'pattern': r'\b\d+(\.\d+)?%|\b\d+\s+(percent|million|billion|thousand)\b',
                'weight': -0.1,
                'description': 'Statistical data present'
            }
        }
    
    def detect_patterns(self, content: str, title: str = "") -> PatternResult:
        """
        Detect fake news patterns in content
        
        Args:
            content: Article content to analyze
            title: Article title (optional)
            
        Returns:
            PatternResult with detected patterns and scores
        """
        if not content:
            return PatternResult(
                overall_score=0.0,
                patterns_detected=[],
                pattern_scores={},
                emotional_indicators=[],
                suspicious_phrases=[],
                credibility_flags=[]
            )
        
        # Combine title and content for analysis
        full_text = f"{title} {content}".strip()
        
        # Initialize results
        pattern_scores = {}
        patterns_detected = []
        emotional_indicators = []
        suspicious_phrases = []
        credibility_flags = []
        
        # Analyze emotional patterns
        emotional_score = self._analyze_emotional_patterns(
            full_text, pattern_scores, emotional_indicators
        )
        
        # Analyze suspicious patterns
        suspicious_score = self._analyze_suspicious_patterns(
            full_text, pattern_scores, suspicious_phrases
        )
        
        # Analyze credibility patterns
        credibility_score = self._analyze_credibility_patterns(
            full_text, pattern_scores, credibility_flags
        )
        
        # Calculate overall pattern score
        overall_score = max(0.0, min(1.0, emotional_score + suspicious_score + credibility_score))
        
        # Collect all detected patterns
        patterns_detected = [desc for desc in pattern_scores.keys() if pattern_scores[desc] > 0]
        
        return PatternResult(
            overall_score=overall_score,
            patterns_detected=patterns_detected,
            pattern_scores=pattern_scores,
            emotional_indicators=emotional_indicators,
            suspicious_phrases=suspicious_phrases,
            credibility_flags=credibility_flags
        )
    
    def _analyze_emotional_patterns(self, text: str, pattern_scores: Dict, 
                                  emotional_indicators: List) -> float:
        """Analyze emotional language patterns"""
        total_score = 0.0
        text_lower = text.lower()
        
        # Check excessive capitalization
        caps_matches = re.findall(self.emotional_patterns['excessive_caps']['pattern'], text)
        if caps_matches:
            score = min(len(caps_matches) * 0.1, self.emotional_patterns['excessive_caps']['weight'])
            total_score += score
            pattern_scores['Excessive capitalization'] = score
            emotional_indicators.extend(caps_matches[:3])  # Limit to first 3
        
        # Check multiple exclamation marks
        excl_matches = re.findall(self.emotional_patterns['multiple_exclamation']['pattern'], text)
        if excl_matches:
            score = min(len(excl_matches) * 0.05, self.emotional_patterns['multiple_exclamation']['weight'])
            total_score += score
            pattern_scores['Multiple exclamation marks'] = score
            emotional_indicators.extend(excl_matches[:3])
        
        # Check emotional words
        emotional_words = self.emotional_patterns['emotional_words']['words']
        found_words = [word for word in emotional_words if word in text_lower]
        if found_words:
            score = min(len(found_words) * 0.05, self.emotional_patterns['emotional_words']['weight'])
            total_score += score
            pattern_scores['High-emotion words'] = score
            emotional_indicators.extend(found_words[:5])
        
        # Check sensational phrases
        sensational_phrases = self.emotional_patterns['sensational_phrases']['phrases']
        found_phrases = [phrase for phrase in sensational_phrases if phrase in text_lower]
        if found_phrases:
            score = min(len(found_phrases) * 0.1, self.emotional_patterns['sensational_phrases']['weight'])
            total_score += score
            pattern_scores['Sensational phrases'] = score
            emotional_indicators.extend(found_phrases[:3])
        
        return total_score
    
    def _analyze_suspicious_patterns(self, text: str, pattern_scores: Dict,
                                   suspicious_phrases: List) -> float:
        """Analyze suspicious content patterns"""
        total_score = 0.0
        text_lower = text.lower()
        
        # Check vague sources
        vague_phrases = self.suspicious_patterns['vague_sources']['phrases']
        found_vague = [phrase for phrase in vague_phrases if phrase in text_lower]
        if found_vague:
            score = min(len(found_vague) * 0.05, self.suspicious_patterns['vague_sources']['weight'])
            total_score += score
            pattern_scores['Vague source references'] = score
            suspicious_phrases.extend(found_vague[:3])
        
        # Check absolute statements
        absolute_words = self.suspicious_patterns['absolute_statements']['words']
        found_absolute = [word for word in absolute_words if f' {word} ' in f' {text_lower} ']
        if found_absolute:
            score = min(len(found_absolute) * 0.02, self.suspicious_patterns['absolute_statements']['weight'])
            total_score += score
            pattern_scores['Absolute statements'] = score
            suspicious_phrases.extend(found_absolute[:5])
        
        # Check conspiracy language
        conspiracy_phrases = self.suspicious_patterns['conspiracy_language']['phrases']
        found_conspiracy = [phrase for phrase in conspiracy_phrases if phrase in text_lower]
        if found_conspiracy:
            score = min(len(found_conspiracy) * 0.08, self.suspicious_patterns['conspiracy_language']['weight'])
            total_score += score
            pattern_scores['Conspiracy-related language'] = score
            suspicious_phrases.extend(found_conspiracy[:3])
        
        return total_score
    
    def _analyze_credibility_patterns(self, text: str, pattern_scores: Dict,
                                    credibility_flags: List) -> float:
        """Analyze credibility warning and positive patterns"""
        total_score = 0.0
        
        # Check poor grammar patterns
        grammar_issues = 0
        for pattern in self.credibility_patterns['poor_grammar']['patterns']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            grammar_issues += len(matches)
        
        if grammar_issues > 0:
            score = min(grammar_issues * 0.02, self.credibility_patterns['poor_grammar']['weight'])
            total_score += score
            pattern_scores['Poor grammar/spelling'] = score
            credibility_flags.append(f"Grammar issues: {grammar_issues}")
        
        # Check clickbait numbers
        clickbait_matches = re.findall(self.credibility_patterns['clickbait_numbers']['pattern'], text, re.IGNORECASE)
        if clickbait_matches:
            score = min(len(clickbait_matches) * 0.1, self.credibility_patterns['clickbait_numbers']['weight'])
            total_score += score
            pattern_scores['Clickbait number patterns'] = score
            credibility_flags.extend(clickbait_matches[:3])
        
        # Check excessive punctuation
        punct_matches = re.findall(self.credibility_patterns['excessive_punctuation']['pattern'], text)
        if punct_matches:
            score = min(len(punct_matches) * 0.05, self.credibility_patterns['excessive_punctuation']['weight'])
            total_score += score
            pattern_scores['Excessive punctuation'] = score
            credibility_flags.extend(punct_matches[:3])
        
        # Check positive credibility indicators (these reduce the fake news score)
        for indicator_name, indicator_data in self.credibility_indicators.items():
            matches = re.findall(indicator_data['pattern'], text, re.IGNORECASE)
            if matches:
                score = max(len(matches) * 0.02, indicator_data['weight'])  # Negative weight
                total_score += score
                pattern_scores[indicator_data['description']] = score
        
        return total_score
    
    def get_pattern_explanation(self, pattern_result: PatternResult) -> str:
        """Generate human-readable explanation of detected patterns"""
        if pattern_result.overall_score < 0.1:
            return "No significant fake news patterns detected."
        
        explanations = []
        
        if pattern_result.emotional_indicators:
            explanations.append(f"Emotional language detected: {', '.join(pattern_result.emotional_indicators[:3])}")
        
        if pattern_result.suspicious_phrases:
            explanations.append(f"Suspicious phrases found: {', '.join(pattern_result.suspicious_phrases[:3])}")
        
        if pattern_result.credibility_flags:
            explanations.append(f"Credibility concerns: {', '.join(pattern_result.credibility_flags[:3])}")
        
        if pattern_result.overall_score > 0.5:
            risk_level = "high"
        elif pattern_result.overall_score > 0.3:
            risk_level = "moderate"
        else:
            risk_level = "low"
        
        explanation = f"Pattern analysis shows {risk_level} risk of fake news characteristics. "
        if explanations:
            explanation += " ".join(explanations)
        
        return explanation
    
    def should_flag_content(self, pattern_result: PatternResult, threshold: float = 0.4) -> bool:
        """Determine if content should be flagged based on pattern analysis"""
        return pattern_result.overall_score >= threshold
    
    def get_pattern_summary(self, pattern_result: PatternResult) -> Dict:
        """Get summary of pattern analysis for logging/debugging"""
        return {
            'overall_score': round(pattern_result.overall_score, 3),
            'patterns_count': len(pattern_result.patterns_detected),
            'emotional_indicators_count': len(pattern_result.emotional_indicators),
            'suspicious_phrases_count': len(pattern_result.suspicious_phrases),
            'credibility_flags_count': len(pattern_result.credibility_flags),
            'top_patterns': list(pattern_result.pattern_scores.keys())[:5]
        }