"""
Module 3: Feature Extraction
Converts text into numerical features using TF-IDF, Word Embeddings, and Sentiment Analysis
"""

import numpy as np
from typing import Dict, List, Tuple
import logging
import pickle
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extracts numerical features from preprocessed text"""
    
    def __init__(self, vectorizer_path: str = None):
        self.vectorizer = None
        self.vectorizer_path = vectorizer_path
        
        if vectorizer_path and os.path.exists(vectorizer_path):
            self.load_vectorizer(vectorizer_path)
    
    def load_vectorizer(self, path: str):
        """Load pre-trained TF-IDF vectorizer"""
        try:
            with open(path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            logger.info(f"Vectorizer loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading vectorizer: {str(e)}")
    
    def extract_tfidf_features(self, text: str) -> np.ndarray:
        """
        Extract TF-IDF features from text
        
        Args:
            text: Preprocessed text
            
        Returns:
            TF-IDF feature vector
        """
        if self.vectorizer is None:
            logger.error("Vectorizer not loaded")
            return np.array([])
        
        try:
            features = self.vectorizer.transform([text])
            return features
        except Exception as e:
            logger.error(f"Error extracting TF-IDF features: {str(e)}")
            return np.array([])
    
    def extract_sentiment_features(self, text: str) -> Dict[str, float]:
        """
        Extract sentiment analysis features
        
        Returns:
            Dictionary with sentiment scores
        """
        # Simple sentiment analysis based on word lists
        positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
                         'positive', 'success', 'win', 'best', 'happy', 'love', 'perfect'}
        
        negative_words = {'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'fail',
                         'failure', 'negative', 'sad', 'angry', 'wrong', 'evil', 'disaster'}
        
        sensational_words = {'breaking', 'shocking', 'unbelievable', 'incredible', 'urgent',
                            'alert', 'warning', 'exclusive', 'revealed', 'exposed', 'scandal',
                            'crisis', 'bombshell', 'stunning'}
        
        emotional_words = {'outrage', 'fury', 'panic', 'fear', 'terror', 'rage', 'chaos',
                          'devastated', 'horrified', 'shocked', 'alarmed'}
        
        words = text.lower().split()
        total_words = len(words) if words else 1
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        sensational_count = sum(1 for word in words if word in sensational_words)
        emotional_count = sum(1 for word in words if word in emotional_words)
        
        return {
            'positive_ratio': positive_count / total_words,
            'negative_ratio': negative_count / total_words,
            'sensational_ratio': sensational_count / total_words,
            'emotional_ratio': emotional_count / total_words,
            'sentiment_polarity': (positive_count - negative_count) / total_words,
            'emotional_intensity': (sensational_count + emotional_count) / total_words
        }
    
    def extract_linguistic_features(self, text: str, original_text: str = "") -> Dict[str, float]:
        """
        Extract linguistic and stylistic features
        
        Args:
            text: Preprocessed text
            original_text: Original text before preprocessing
            
        Returns:
            Dictionary with linguistic features
        """
        words = text.split()
        total_words = len(words) if words else 1
        
        # Use original text for punctuation analysis
        analysis_text = original_text if original_text else text
        
        features = {
            'text_length': len(text),
            'word_count': total_words,
            'avg_word_length': sum(len(word) for word in words) / total_words,
            'exclamation_count': analysis_text.count('!'),
            'question_count': analysis_text.count('?'),
            'uppercase_ratio': sum(1 for c in analysis_text if c.isupper()) / len(analysis_text) if analysis_text else 0,
            'digit_ratio': sum(1 for c in analysis_text if c.isdigit()) / len(analysis_text) if analysis_text else 0,
        }
        
        # Unique word ratio (vocabulary richness)
        features['unique_word_ratio'] = len(set(words)) / total_words if total_words > 0 else 0
        
        return features
    
    def extract_all_features(self, article: Dict) -> Dict:
        """
        Extract all features from an article
        
        Args:
            article: Dictionary with 'processed_text' and optionally 'content'
            
        Returns:
            Article dictionary with added feature fields
        """
        processed_text = article.get('processed_text', '')
        original_text = article.get('content', '') + ' ' + article.get('title', '')
        
        # TF-IDF features (for model prediction)
        tfidf_features = self.extract_tfidf_features(processed_text)
        article['tfidf_features'] = tfidf_features
        
        # Sentiment features
        sentiment = self.extract_sentiment_features(original_text)
        article['sentiment_features'] = sentiment
        
        # Linguistic features
        linguistic = self.extract_linguistic_features(processed_text, original_text)
        article['linguistic_features'] = linguistic
        
        # Feature signals for explanation
        article['feature_signals'] = self._identify_signals(sentiment, linguistic, original_text)
        
        return article
    
    def _identify_signals(self, sentiment: Dict, linguistic: Dict, text: str) -> List[str]:
        """
        Identify suspicious signals in the text
        
        Returns:
            List of identified signals
        """
        signals = []
        
        # Check for sensational language
        if sentiment['sensational_ratio'] > 0.02:
            signals.append('sensational headline')
        
        # Check for emotional manipulation
        if sentiment['emotional_ratio'] > 0.015:
            signals.append('emotional tone')
        
        # Check for excessive punctuation
        if linguistic['exclamation_count'] > 3:
            signals.append('excessive punctuation')
        
        # Check for all caps usage
        if linguistic['uppercase_ratio'] > 0.15:
            signals.append('excessive capitalization')
        
        # Check for extreme sentiment
        if abs(sentiment['sentiment_polarity']) > 0.05:
            signals.append('extreme sentiment')
        
        # Check for grammatical anomalies (simple heuristic)
        if linguistic['avg_word_length'] < 3.5:
            signals.append('unusual word patterns')
        
        return signals
