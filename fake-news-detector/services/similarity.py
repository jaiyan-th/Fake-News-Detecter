"""
Semantic similarity engine using sentence transformers
"""

from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from dataclasses import dataclass
from services.extractor import ArticleContent
@dataclass
class SimilarityScore:
    article_url: str
    score: float
    source: str
    is_trusted: bool
    article_title: str = ""

class SimilarityEngine:
    """Service for computing semantic similarity between articles"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = None
        self.embedding_cache = {}
        self.trusted_sources = {
            'bbc', 'reuters', 'the hindu', 'ndtv', 'cnn', 'associated press',
            'npr', 'pbs', 'the guardian', 'washington post', 'new york times',
            'wall street journal', 'abc news', 'cbs news', 'nbc news'
        }
    
    def _load_model(self):
        """Lazy load the sentence transformer model"""
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding with caching"""
        # Use first 500 characters as cache key to avoid memory issues
        cache_key = text[:500]
        
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        self._load_model()
        
        # Generate embedding
        embedding = self.model.encode(text, convert_to_tensor=False)
        
        # Cache the embedding
        self.embedding_cache[cache_key] = embedding
        
        return embedding
    
    def compute_similarities(self, target_article: ArticleContent, articles: List[ArticleContent]) -> List[SimilarityScore]:
        """
        Compute semantic similarities between target article and list of articles
        
        Returns:
            List of SimilarityScore objects sorted by similarity (highest first)
        """
        if not articles:
            return []
        
        try:
            # Generate embedding for target article
            target_text = f"{target_article.title} {target_article.content}"
            target_embedding = self.generate_embedding(target_text)
            
            similarity_scores = []
            
            for article in articles:
                try:
                    # Generate embedding for comparison article
                    article_text = f"{article.title} {article.content}"
                    article_embedding = self.generate_embedding(article_text)
                    
                    # Compute cosine similarity
                    similarity = self._cosine_similarity(target_embedding, article_embedding)
                    
                    # Ensure similarity is between 0 and 1
                    similarity = max(0.0, min(1.0, similarity))
                    
                    # Check if source is trusted
                    is_trusted = self._is_trusted_source(article.source)
                    
                    score = SimilarityScore(
                        article_url=article.url,
                        score=similarity,
                        source=article.source,
                        is_trusted=is_trusted,
                        article_title=article.title
                    )
                    
                    similarity_scores.append(score)
                    
                except Exception as e:
                    print(f"Error computing similarity for {article.url}: {str(e)}")
                    continue
            
            # Sort by similarity score (highest first)
            similarity_scores.sort(key=lambda x: x.score, reverse=True)
            
            return similarity_scores
            
        except Exception as e:
            print(f"Similarity computation failed: {str(e)}")
            return []
    
    def _cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings"""
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Compute cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        
        return float(similarity)
    
    def _is_trusted_source(self, source: str) -> bool:
        """Check if source is from a trusted news organization"""
        trusted_sources = {
            'bbc', 'reuters', 'associated press', 'cnn', 'npr',
            'the guardian', 'new york times', 'washington post',
            'wall street journal', 'bloomberg', 'the hindu', 'ndtv',
            'times of india', 'indian express', 'hindustan times',
            'the print', 'scroll', 'the quint', 'moneycontrol',
            'india today', 'news18', 'firstpost', 'deccan herald',
            'telegraph', 'tribune', 'mint', 'livemint', 'economic times'
        }
        
        source_lower = source.lower()
        return any(trusted in source_lower for trusted in trusted_sources)
    
    def clear_cache(self):
        """Clear embedding cache to free memory"""
        self.embedding_cache.clear()