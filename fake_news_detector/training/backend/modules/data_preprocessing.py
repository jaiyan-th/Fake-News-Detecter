"""
Module 2: Data Preprocessing
Handles text cleaning, tokenization, stopword removal, and stemming/lemmatization
"""

import re
import string
from typing import List, Dict
import logging

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords', quiet=True)
    
    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', quiet=True)
    
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextPreprocessor:
    """Handles all text preprocessing operations"""
    
    def __init__(self, use_stemming: bool = True, use_lemmatization: bool = False):
        self.use_stemming = use_stemming
        self.use_lemmatization = use_lemmatization
        
        if NLTK_AVAILABLE:
            self.stop_words = set(stopwords.words('english'))
            self.stemmer = PorterStemmer()
            self.lemmatizer = WordNetLemmatizer()
        else:
            # Fallback stopwords
            self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                             'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
                             'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                             'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that',
                             'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
            logger.warning("NLTK not available, using basic preprocessing")
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing special characters and normalizing
        
        Example:
            Input: "Breaking: Government announces new policy today!!!"
            Output: "breaking government announces new policy today"
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove mentions and hashtags (social media)
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if NLTK_AVAILABLE:
            return word_tokenize(text)
        else:
            # Simple whitespace tokenization
            return text.split()
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords from token list
        
        Args:
            tokens: List of tokens
            
        Returns:
            Filtered token list
        """
        return [token for token in tokens if token not in self.stop_words and len(token) > 2]
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming to tokens
        
        Args:
            tokens: List of tokens
            
        Returns:
            Stemmed tokens
        """
        if NLTK_AVAILABLE and self.use_stemming:
            return [self.stemmer.stem(token) for token in tokens]
        return tokens
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply lemmatization to tokens
        
        Args:
            tokens: List of tokens
            
        Returns:
            Lemmatized tokens
        """
        if NLTK_AVAILABLE and self.use_lemmatization:
            return [self.lemmatizer.lemmatize(token) for token in tokens]
        return tokens
    
    def preprocess(self, text: str) -> str:
        """
        Complete preprocessing pipeline
        
        Steps:
        1. Clean text (remove punctuation, lowercase, etc.)
        2. Tokenize
        3. Remove stopwords
        4. Apply stemming/lemmatization
        
        Args:
            text: Raw input text
            
        Returns:
            Preprocessed text string
        """
        # Step 1: Clean
        cleaned = self.clean_text(text)
        
        # Step 2: Tokenize
        tokens = self.tokenize(cleaned)
        
        # Step 3: Remove stopwords
        tokens = self.remove_stopwords(tokens)
        
        # Step 4: Stemming or Lemmatization
        if self.use_lemmatization:
            tokens = self.lemmatize_tokens(tokens)
        elif self.use_stemming:
            tokens = self.stem_tokens(tokens)
        
        # Return as string
        return ' '.join(tokens)
    
    def preprocess_article(self, article: Dict) -> Dict:
        """
        Preprocess an entire article dictionary
        
        Args:
            article: Dictionary with 'title' and 'content' keys
            
        Returns:
            Article with added 'processed_text' field
        """
        title = article.get('title', '')
        content = article.get('content', '')
        
        # Combine title and content
        full_text = f"{title} {content}"
        
        # Preprocess
        processed = self.preprocess(full_text)
        
        article['processed_text'] = processed
        article['preprocessing_steps'] = {
            'cleaning': True,
            'tokenization': True,
            'stopword_removal': True,
            'stemming': self.use_stemming,
            'lemmatization': self.use_lemmatization
        }
        
        return article
