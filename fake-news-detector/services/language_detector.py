"""
Language detection and processing service for multi-language support
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class LanguageResult:
    """Result of language detection"""
    language: str
    confidence: float
    is_supported: bool
    fallback_used: bool

class LanguageDetector:
    """Service for detecting and processing multiple languages"""
    
    def __init__(self):
        """Initialize language detector"""
        # Supported languages (can be extended)
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish', 
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'hi': 'Hindi',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'ja': 'Japanese'
        }
        
        # Language patterns for basic detection
        self.language_patterns = {
            'en': {
                'common_words': ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with'],
                'patterns': [r'\b(the|and|is|are|was|were|have|has|will|would)\b']
            },
            'es': {
                'common_words': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no'],
                'patterns': [r'\b(el|la|de|que|y|en|un|una|es|son|se|no)\b']
            },
            'fr': {
                'common_words': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir'],
                'patterns': [r'\b(le|la|de|et|à|un|une|il|elle|être|avoir)\b']
            },
            'de': {
                'common_words': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich'],
                'patterns': [r'\b(der|die|das|und|in|den|von|zu|mit|sich)\b']
            },
            'hi': {
                'common_words': ['और', 'का', 'एक', 'में', 'की', 'है', 'से', 'को', 'पर', 'इस'],
                'patterns': [r'[\u0900-\u097F]+']  # Devanagari script
            },
            'ar': {
                'common_words': ['في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'التي', 'الذي', 'كان', 'كانت'],
                'patterns': [r'[\u0600-\u06FF]+']  # Arabic script
            },
            'zh': {
                'common_words': ['的', '是', '在', '有', '个', '人', '这', '中', '大', '为'],
                'patterns': [r'[\u4e00-\u9fff]+']  # Chinese characters
            }
        }
        
        # Fallback confidence reduction factor
        self.fallback_confidence_factor = 0.7
    
    def detect_language(self, text: str) -> LanguageResult:
        """
        Detect language of the given text
        
        Args:
            text: Text to analyze
            
        Returns:
            LanguageResult with detected language and confidence
        """
        if not text or len(text.strip()) < 10:
            return LanguageResult(
                language='en',
                confidence=0.3,
                is_supported=True,
                fallback_used=True
            )
        
        # Clean and normalize text
        clean_text = self._clean_text(text)
        
        # Try to detect language using patterns
        language_scores = {}
        
        for lang_code, lang_data in self.language_patterns.items():
            score = self._calculate_language_score(clean_text, lang_data)
            if score > 0:
                language_scores[lang_code] = score
        
        # Determine best match
        if language_scores:
            best_language = max(language_scores, key=language_scores.get)
            confidence = min(language_scores[best_language], 1.0)
            
            # Boost confidence if multiple indicators match
            if confidence > 0.3 and len([s for s in language_scores.values() if s > 0.1]) == 1:
                confidence = min(confidence * 1.2, 0.95)
        else:
            # Default to English if no clear match
            best_language = 'en'
            confidence = 0.4
        
        # Check if language is supported
        is_supported = best_language in self.supported_languages
        fallback_used = not is_supported or confidence < 0.5
        
        # If not supported or low confidence, fallback to English
        if fallback_used and best_language != 'en':
            best_language = 'en'
            confidence *= self.fallback_confidence_factor
        
        return LanguageResult(
            language=best_language,
            confidence=confidence,
            is_supported=is_supported,
            fallback_used=fallback_used
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for language detection"""
        # Convert to lowercase
        clean_text = text.lower()
        
        # Remove URLs
        clean_text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', clean_text)
        
        # Remove email addresses
        clean_text = re.sub(r'\S+@\S+', '', clean_text)
        
        # Remove excessive whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text
    
    def _calculate_language_score(self, text: str, lang_data: Dict) -> float:
        """Calculate language score based on patterns and common words"""
        score = 0.0
        text_length = len(text.split())
        
        if text_length == 0:
            return 0.0
        
        # Check common words
        common_words = lang_data.get('common_words', [])
        word_matches = 0
        
        for word in common_words:
            # Count occurrences of common words
            word_count = len(re.findall(r'\b' + re.escape(word.lower()) + r'\b', text))
            word_matches += word_count
        
        # Calculate word-based score
        word_score = min(word_matches / text_length, 0.8)
        score += word_score
        
        # Check patterns (for script-based languages)
        patterns = lang_data.get('patterns', [])
        for pattern in patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            if matches > 0:
                pattern_score = min(matches / max(text_length, 10), 0.6)
                score += pattern_score
        
        return min(score, 1.0)
    
    def process_multilingual_content(self, content: str, detected_language: str) -> Tuple[str, float]:
        """
        Process content based on detected language
        
        Args:
            content: Original content
            detected_language: Detected language code
            
        Returns:
            Tuple of (processed_content, confidence_adjustment)
        """
        # For now, we'll keep content as-is but adjust confidence
        confidence_adjustment = 1.0
        
        if detected_language != 'en':
            # Reduce confidence for non-English content
            confidence_adjustment = 0.8
            
            # Add language indicator to content for processing
            processed_content = f"[Language: {self.supported_languages.get(detected_language, detected_language)}] {content}"
        else:
            processed_content = content
        
        return processed_content, confidence_adjustment
    
    def get_language_info(self, language_code: str) -> Dict:
        """Get information about a language"""
        return {
            'code': language_code,
            'name': self.supported_languages.get(language_code, 'Unknown'),
            'supported': language_code in self.supported_languages,
            'fallback_factor': self.fallback_confidence_factor if language_code != 'en' else 1.0
        }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages"""
        return self.supported_languages.copy()
    
    def should_use_fallback(self, language_result: LanguageResult) -> bool:
        """Determine if fallback processing should be used"""
        return (language_result.fallback_used or 
                language_result.confidence < 0.5 or
                not language_result.is_supported)