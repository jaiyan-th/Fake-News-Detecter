"""
Complete Fake News Detection Pipeline
Integrates all 6 modules into a unified system
"""

from typing import Dict, Optional
import logging
import os

from .data_collection import DataCollector
from .data_preprocessing import TextPreprocessor
from .feature_extraction import FeatureExtractor
from .ml_model import FakeNewsClassifier
from .verification import NewsVerifier
from .dashboard import ResultDashboard

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeNewsDetectionPipeline:
    """
    Complete pipeline for fake news detection
    
    Pipeline Flow:
    1. Data Collection → 2. Preprocessing → 3. Feature Extraction →
    4. ML Classification → 5. Verification → 6. Dashboard Results
    """
    
    def __init__(self, model_path: str, vectorizer_path: str, news_api_key: Optional[str] = None):
        """
        Initialize the complete pipeline
        
        Args:
            model_path: Path to trained ML model
            vectorizer_path: Path to TF-IDF vectorizer
            news_api_key: Optional News API key for data collection
        """
        logger.info("Initializing Fake News Detection Pipeline...")
        
        # Module 1: Data Collection
        self.collector = DataCollector(news_api_key=news_api_key)
        logger.info("✓ Data Collection module loaded")
        
        # Module 2: Data Preprocessing
        self.preprocessor = TextPreprocessor(use_stemming=True, use_lemmatization=False)
        logger.info("✓ Data Preprocessing module loaded")
        
        # Module 3: Feature Extraction
        self.feature_extractor = FeatureExtractor(vectorizer_path=vectorizer_path)
        logger.info("✓ Feature Extraction module loaded")
        
        # Module 4: ML Model
        self.classifier = FakeNewsClassifier(model_path=model_path)
        logger.info("✓ ML Classifier module loaded")
        
        # Module 5: Verification Layer
        self.verifier = NewsVerifier()
        logger.info("✓ Verification module loaded")
        
        # Module 6: Dashboard
        self.dashboard = ResultDashboard()
        logger.info("✓ Dashboard module loaded")
        
        logger.info("Pipeline initialization complete!")
    
    def analyze_text(self, text: str, title: str = "") -> Dict:
        """
        Analyze user-provided text
        
        Args:
            text: Article text
            title: Article title (optional)
            
        Returns:
            Complete analysis results
        """
        logger.info("Starting text analysis...")
        
        # Step 1: Collect data (from user input)
        article = self.collector.collect_from_text(text, title)
        logger.info("✓ Step 1: Data collected")
        
        # Run through pipeline
        return self._run_pipeline(article)
    
    def analyze_url(self, url: str) -> Dict:
        """
        Analyze article from URL with improved error handling and test mode
        
        Args:
            url: Article URL or test keyword
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting URL analysis: {url}")
        
        try:
            # Handle test mode URLs
            if url.lower() in ['test', 'sample', 'demo', 'offline']:
                logger.info("Using test mode - creating sample article")
                
                sample_articles = {
                    'test': {
                        'url': 'test://sample',
                        'title': 'AI Breakthrough in Medical Diagnosis Announced by MIT',
                        'content': '''
                        Researchers at the Massachusetts Institute of Technology have announced a groundbreaking 
                        artificial intelligence system that can diagnose medical conditions with unprecedented accuracy. 
                        The new system, developed over three years by a team led by Dr. Sarah Chen, combines deep 
                        learning algorithms with traditional diagnostic methods to achieve 98% accuracy in clinical trials.
                        
                        The AI system, called MedAI, was tested at Massachusetts General Hospital on over 10,000 
                        patient cases across multiple medical specialties. Results published in the New England 
                        Journal of Medicine show the system correctly identified conditions ranging from cancer 
                        to rare genetic disorders.
                        
                        "This technology represents a significant step forward in medical diagnostics," said Dr. Chen 
                        during a press conference at MIT. "It could help doctors make faster, more accurate diagnoses, 
                        especially in underserved areas where specialist expertise may not be readily available."
                        
                        The research was funded by the National Institutes of Health and has undergone rigorous 
                        peer review. Clinical trials were conducted following FDA guidelines, and the team expects 
                        to submit for regulatory approval within the next 18 months.
                        
                        The system works by analyzing medical images, patient history, and laboratory results 
                        simultaneously. It cross-references findings with a database of over 100,000 verified 
                        medical cases to provide diagnostic recommendations with confidence scores.
                        ''',
                        'author': 'MIT Research Team',
                        'publish_date': '2024-01-15T10:00:00Z',
                        'source': 'MIT News',
                        'collection_method': 'test_mode',
                        'success': True
                    },
                    'sample': {
                        'url': 'sample://news',
                        'title': 'Local Community Garden Project Wins Environmental Award',
                        'content': '''
                        The Riverside Community Garden project has been awarded the 2024 Environmental Excellence 
                        Award by the State Environmental Protection Agency. The project, which began two years ago, 
                        has transformed a vacant lot into a thriving community space that produces fresh vegetables 
                        for local families.
                        
                        Project coordinator Maria Rodriguez said the garden now serves over 200 families in the 
                        neighborhood. "We started with just a few volunteers and some donated seeds," Rodriguez 
                        explained. "Now we have 50 garden plots, a composting system, and even a small greenhouse."
                        
                        The award recognizes the project's innovative approach to urban sustainability. The garden 
                        uses rainwater collection, solar-powered irrigation, and organic farming methods. Food 
                        produced is distributed through a local food bank and community market.
                        
                        Mayor Jennifer Thompson attended the award ceremony, praising the community's dedication. 
                        "This project shows what we can accomplish when neighbors work together for a common goal," 
                        she said. The garden has also become an educational site, hosting school field trips and 
                        workshops on sustainable agriculture.
                        
                        Plans are underway to expand the project to two additional sites in the city, with funding 
                        from the environmental award and local grants.
                        ''',
                        'author': 'Local News Reporter',
                        'publish_date': '2024-01-10T14:30:00Z',
                        'source': 'Community News',
                        'collection_method': 'test_mode',
                        'success': True
                    }
                }
                
                # Select article based on URL
                article_key = 'test' if url.lower() == 'test' else 'sample'
                article = sample_articles.get(article_key, sample_articles['test'])
                
                logger.info(f"✓ Test article loaded: {article['title']}")
                
                # Run through pipeline
                return self._run_pipeline(article)
            
            # Step 1: Collect data from URL
            article = self.collector.collect_from_url(url)
            
            # Check if collection was successful
            if not article.get('success', True) or 'error' in article:
                error_msg = article.get('error', 'Unknown error occurred while fetching the URL')
                logger.error(f"URL collection failed: {error_msg}")
                
                return {
                    'success': False,
                    'error': error_msg,
                    'message': 'Failed to collect article from URL. Try using "test" as URL for offline testing.',
                    'suggestions': [
                        'Use "test" or "sample" as URL for offline testing',
                        'Verify the URL is correct and accessible',
                        'Try a different news article URL',
                        'Use the text input option instead',
                        'Check your internet connection'
                    ]
                }
            
            # Validate content
            if not article.get('content') and not article.get('title'):
                return {
                    'success': False,
                    'error': 'No content found',
                    'message': 'The webpage does not contain readable article content.',
                    'suggestions': [
                        'Use "test" as URL for offline testing',
                        'Try a different article URL',
                        'Some websites block automated access',
                        'Copy and paste the article text manually'
                    ]
                }
            
            # Check content length
            content_length = len(article.get('content', ''))
            if content_length < 50:
                return {
                    'success': False,
                    'error': 'Insufficient content',
                    'message': f'Article content is too short ({content_length} characters). Need at least 50 characters for analysis.',
                    'suggestions': [
                        'Use "test" as URL for offline testing',
                        'Try a longer article',
                        'Check if the URL points to a full article',
                        'Some pages may require JavaScript to load content'
                    ]
                }
            
            logger.info(f"✓ Step 1: Data collected from URL ({content_length} characters)")
            
            # Run through pipeline
            return self._run_pipeline(article)
            
        except Exception as e:
            logger.error(f"Unexpected error in URL analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An unexpected error occurred while analyzing the URL.',
                'suggestions': [
                    'Use "test" as URL for offline testing',
                    'Try again in a few moments',
                    'Use a different URL',
                    'Contact support if the problem persists'
                ]
            }
    
    def analyze_news_query(self, query: str, article_index: int = 0) -> Dict:
        """
        Analyze news from News API query
        
        Args:
            query: Search query
            article_index: Which article to analyze from results
            
        Returns:
            Complete analysis results
        """
        logger.info(f"Starting News API query: {query}")
        
        # Step 1: Collect data from News API
        articles = self.collector.collect_from_news_api(query, page_size=5)
        
        if not articles:
            return {
                'success': False,
                'error': 'No articles found',
                'message': 'News API returned no results'
            }
        
        # Analyze the specified article
        article = articles[article_index] if article_index < len(articles) else articles[0]
        logger.info("✓ Step 1: Data collected from News API")
        
        # Run through pipeline
        return self._run_pipeline(article)
    
    def _run_pipeline(self, article: Dict) -> Dict:
        """
        Run the complete analysis pipeline
        
        Args:
            article: Article dictionary
            
        Returns:
            Complete analysis results
        """
        try:
            # Step 2: Preprocess
            article = self.preprocessor.preprocess_article(article)
            logger.info("✓ Step 2: Text preprocessed")
            
            # Step 3: Extract features
            article = self.feature_extractor.extract_all_features(article)
            logger.info("✓ Step 3: Features extracted")
            
            # Step 4: ML Classification
            prediction_result = self.classifier.predict_with_details(article)
            logger.info(f"✓ Step 4: Classification complete - {prediction_result['prediction']}")
            
            # Step 5: Verification
            verification_result = self.verifier.verify_article(
                article,
                prediction_result['prediction'],
                prediction_result['confidence']
            )
            logger.info("✓ Step 5: Verification complete")
            
            # Step 6: Format for dashboard
            dashboard_result = self.dashboard.format_analysis_result(
                article,
                prediction_result,
                verification_result
            )
            logger.info("✓ Step 6: Dashboard result formatted")
            
            # Return API-friendly response
            return self.dashboard.format_for_api_response(dashboard_result)
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred during analysis'
            }
    
    def batch_analyze(self, articles: list) -> Dict:
        """
        Analyze multiple articles in batch
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Batch analysis results with statistics
        """
        results = []
        
        for i, article in enumerate(articles):
            logger.info(f"Analyzing article {i+1}/{len(articles)}")
            result = self._run_pipeline(article)
            results.append(result)
        
        # Generate summary statistics
        summary = self.dashboard.format_summary_statistics(results)
        
        return {
            'success': True,
            'total_analyzed': len(articles),
            'results': results,
            'summary': summary
        }
    
    def get_pipeline_info(self) -> Dict:
        """Get information about the pipeline configuration"""
        return {
            'pipeline_version': '1.0.0',
            'modules': {
                'data_collection': 'Active',
                'preprocessing': 'Active',
                'feature_extraction': 'Active',
                'ml_model': f'Active ({self.classifier.model_type})',
                'verification': 'Active',
                'dashboard': 'Active'
            },
            'model_info': {
                'type': self.classifier.model_type,
                'loaded': self.classifier.model is not None
            },
            'vectorizer_loaded': self.feature_extractor.vectorizer is not None
        }
