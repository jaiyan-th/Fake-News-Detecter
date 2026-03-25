"""
Analysis route for fake news detection
"""

import time
import re
import threading
from urllib.parse import urlparse
from flask import Blueprint, request, jsonify
from config import Config
from functools import wraps

from functools import wraps

# Import all required services
from models.database import Database
from services.cache import CacheService
from services.extractor import ContentExtractor
from services.summarizer import ArticleSummarizer
from services.keyword_extractor import KeywordExtractor
from services.news_fetcher import NewsFetcher
from services.similarity import SimilarityEngine
from services.decision import DecisionEngine
from services.language_detector import LanguageDetector
from services.pattern_detector import PatternDetector
from services.logger import performance_logger
from services.security import security_validator
from services.error_handler import error_handler, ErrorType

# Import history saving function
from routes.history import save_user_analysis
from flask_login import current_user

analyze_bp = Blueprint('analyze', __name__)

# Initialize services (will be done once when blueprint is registered)
_services = {}

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def run_with_timeout(func, args=(), kwargs=None, timeout_seconds=10):
    """
    Run a function with timeout using threading (cross-platform)
    Preserves Flask application context for database operations
    
    Args:
        func: Function to execute
        args: Function arguments
        kwargs: Function keyword arguments
        timeout_seconds: Maximum time to wait
        
    Returns:
        Function result or raises TimeoutError
    """
    if kwargs is None:
        kwargs = {}
    
    from flask import current_app, has_app_context
    
    result = [None]
    exception = [None]
    
    # Capture the current app context if it exists
    app_context = current_app._get_current_object() if has_app_context() else None
    
    def target():
        try:
            # Push app context if available
            if app_context:
                with app_context.app_context():
                    result[0] = func(*args, **kwargs)
            else:
                result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running, timeout occurred
        raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
    
    if exception[0]:
        raise exception[0]
    
    return result[0]

def with_timeout_and_retry(timeout_seconds=10, max_retries=2):
    """
    Decorator to add timeout and retry logic to functions
    
    Args:
        timeout_seconds: Maximum time to wait for operation (default: 10)
        max_retries: Number of retry attempts (default: 2)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    # Run function with timeout
                    result = run_with_timeout(
                        func, args=args, kwargs=kwargs, 
                        timeout_seconds=timeout_seconds
                    )
                    return result
                    
                except (TimeoutError, Exception) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying...")
                        time.sleep(1)  # Brief delay before retry
                        continue
                    else:
                        print(f"All {max_retries + 1} attempts failed. Last error: {str(e)}")
                        break
            
            # Return fallback result if all attempts failed
            processing_time = time.time() - start_time
            response = jsonify({
                'verdict': 'UNCERTAIN',
                'confidence': '10%',
                'explanation': f"Analysis timed out after {max_retries + 1} attempts: {str(last_exception)}",
                'matched_articles': [],
                'processing_time': round(processing_time, 2)
            })
            return add_security_headers(response)
                
        return wrapper
    return decorator

def add_security_headers(response):
    """Add security headers to response"""
    headers = security_validator.get_security_headers()
    for header, value in headers.items():
        response.headers[header] = value
    return response

def secure_error_response(error_message: str, status_code: int, processing_time: float = None):
    """Create error response with security headers"""
    error_data = {'error': error_message}
    if processing_time is not None:
        error_data['processing_time'] = round(processing_time, 2)
    
    response = jsonify(error_data)
    return add_security_headers(response), status_code

def get_services():
    """Initialize and return services singleton with comprehensive error handling"""
    if not _services:
        try:
            # Validate configuration
            Config.validate_config()
            
            # Initialize database and cache with error handling
            try:
                database = Database(Config.DATABASE_PATH)
                cache_service = CacheService(database)
            except Exception as e:
                raise RuntimeError(f"Database initialization failed: {str(e)}")
            
            # Initialize content extraction with error handling
            try:
                content_extractor = ContentExtractor(timeout=Config.REQUEST_TIMEOUT)
            except Exception as e:
                raise RuntimeError(f"Content extractor initialization failed: {str(e)}")
            
            # Initialize LLM services with error handling
            try:
                article_summarizer = ArticleSummarizer(
                    api_key=Config.GROQ_API_KEY,
                    timeout=Config.REQUEST_TIMEOUT
                )
            except Exception as e:
                raise RuntimeError(f"Article summarizer initialization failed: {str(e)}")
            
            # Initialize keyword extractor with error handling
            try:
                keyword_extractor = KeywordExtractor(api_key=Config.GROQ_API_KEY)
            except Exception as e:
                raise RuntimeError(f"Keyword extractor initialization failed: {str(e)}")
            
            # Initialize news fetching with error handling
            try:
                news_fetcher = NewsFetcher(
                    api_key=Config.NEWS_API_KEY,
                    limit=Config.NEWS_API_LIMIT,
                    serpapi_key=Config.SERPAPI_KEY  # Add SerpAPI support
                )
            except Exception as e:
                raise RuntimeError(f"News fetcher initialization failed: {str(e)}")
            
            # Initialize similarity engine with error handling
            try:
                similarity_engine = SimilarityEngine(model_name=Config.EMBEDDING_MODEL)
            except Exception as e:
                raise RuntimeError(f"Similarity engine initialization failed: {str(e)}")
            
            # Initialize decision engine with error handling
            try:
                decision_engine = DecisionEngine(groq_api_key=Config.GROQ_API_KEY)
            except Exception as e:
                raise RuntimeError(f"Decision engine initialization failed: {str(e)}")
            
            # Initialize language detector with error handling
            try:
                language_detector = LanguageDetector()
            except Exception as e:
                raise RuntimeError(f"Language detector initialization failed: {str(e)}")
            
            # Initialize pattern detector with error handling
            try:
                pattern_detector = PatternDetector()
            except Exception as e:
                raise RuntimeError(f"Pattern detector initialization failed: {str(e)}")
            
            _services.update({
                'cache': cache_service,
                'extractor': content_extractor,
                'summarizer': article_summarizer,
                'keyword_extractor': keyword_extractor,
                'news_fetcher': news_fetcher,
                'similarity': similarity_engine,
                'decision': decision_engine,
                'language_detector': language_detector,
                'pattern_detector': pattern_detector
            })
            
        except Exception as e:
            # Log service initialization failure
            error_handler.logger.critical(f"Service initialization failed: {str(e)}")
            raise RuntimeError(f"Service initialization failed: {str(e)}")
    
    return _services

def save_to_user_history(input_type: str, input_content: str, verdict: str, 
                         confidence: float, explanation: str, matched_articles: list,
                         processing_time: float):
    """Save analysis to user's history if user is logged in"""
    try:
        if current_user.is_authenticated:
            save_user_analysis(
                user_id=current_user.id,
                input_type=input_type,
                input_content=input_content,
                verdict=verdict,
                confidence=confidence,
                explanation=explanation,
                matched_articles_count=len(matched_articles) if matched_articles else 0,
                processing_time=processing_time
            )
    except Exception as e:
        # Don't fail the request if history saving fails
        print(f"Failed to save to user history: {str(e)}")

@analyze_bp.route('/analyze-url', methods=['POST'])
def analyze_url():
    """
    Analyze a news article URL for authenticity
    
    Expected JSON payload:
    {
        "url": "https://example.com/news-article"
    }
    
    Returns:
    {
        "verdict": "REAL|FAKE|UNCERTAIN",
        "confidence": "85%",
        "explanation": "Analysis explanation...",
        "matched_articles": [...],
        "processing_time": 2.5
    }
    """
    start_time = time.time()
    
    # Start analysis tracking
    request_id = performance_logger.start_analysis(data.get('url', 'unknown') if 'data' in locals() else 'unknown')
    
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return error_handler.create_error_response(
                ValueError("Missing JSON payload"),
                ErrorType.VALIDATION_ERROR,
                request_id,
                processing_time=time.time() - start_time
            )
        
        # Comprehensive input validation and sanitization
        validation_result = security_validator.validate_json_input(data)
        
        if not validation_result['valid']:
            performance_logger.complete_analysis(
                request_id, "VALIDATION_ERROR", 0, time.time() - start_time, 
                f"Input validation failed: {'; '.join(validation_result['errors'])}"
            )
            return error_handler.create_error_response(
                ValueError('; '.join(validation_result['errors'])),
                ErrorType.VALIDATION_ERROR,
                request_id,
                {'validation_errors': validation_result['errors']},
                processing_time=time.time() - start_time
            )
        
        # Use sanitized data
        sanitized_data = validation_result['sanitized_data']
        url = sanitized_data['url']
        
        # Log security warnings if any
        if validation_result['warnings']:
            performance_logger.log_step(
                request_id, "security_validation", 
                details={'warnings': validation_result['warnings']}
            )
        
        # Update request ID with actual URL
        request_id = performance_logger.start_analysis(url)
        
        # Initialize services with error handling
        try:
            services = get_services()
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.INTERNAL_ERROR, request_id,
                {'step': 'service_initialization'},
                processing_time=time.time() - start_time
            )
        
        # Step 1: Check cache for existing results with error handling
        cache_start = time.time()
        try:
            cached_result = services['cache'].get_cached_result(url)
            cache_duration = time.time() - cache_start
            
            if cached_result:
                performance_logger.log_cache_hit(request_id, url)
                processing_time = time.time() - start_time
                cached_result['processing_time'] = round(processing_time, 2)
                
                # Complete analysis tracking
                performance_logger.complete_analysis(
                    request_id, cached_result['verdict'], 
                    cached_result['confidence'], processing_time
                )
                
                # Format response
                response = jsonify({
                    'verdict': cached_result['verdict'],
                    'confidence': f"{cached_result['confidence']:.0%}",
                    'explanation': cached_result['explanation'] + " (from cache)",
                    'matched_articles': cached_result['matched_articles'][:3],  # Top 3
                    'processing_time': cached_result['processing_time']
                })
                
                return add_security_headers(response)
            else:
                performance_logger.log_cache_miss(request_id, url)
                
        except Exception as e:
            # Cache failure shouldn't stop the analysis
            cache_duration = time.time() - cache_start
            performance_logger.log_step(request_id, "cache_check", cache_duration, error=str(e))
            performance_logger.log_cache_miss(request_id, url)
            print(f"Cache check failed: {str(e)}, continuing without cache")
        
        # Step 2: Extract content from URL
        extraction_start = time.time()
        try:
            article = run_with_timeout(
                services['extractor'].extract_content, 
                args=(url,), 
                timeout_seconds=8
            )
            extraction_duration = time.time() - extraction_start
            performance_logger.log_content_extraction(
                request_id, extraction_duration, len(article.content)
            )
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "content_extraction", 8)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'content_extraction', 'timeout_seconds': 8},
                "Content extraction timed out, please try again",
                processing_time=time.time() - start_time
            )
        except ValueError as e:
            extraction_duration = time.time() - extraction_start
            performance_logger.log_content_extraction(
                request_id, extraction_duration, 0, str(e)
            )
            
            # Handle specific content extraction errors
            if "Invalid URL" in str(e):
                return error_handler.create_error_response(
                    e, ErrorType.VALIDATION_ERROR, request_id,
                    {'step': 'content_extraction'},
                    processing_time=time.time() - start_time
                )
            elif "Unable to extract" in str(e):
                return error_handler.create_error_response(
                    e, ErrorType.PROCESSING_ERROR, request_id,
                    {'step': 'content_extraction'},
                    "Unable to extract content from the provided URL",
                    processing_time=time.time() - start_time
                )
            else:
                return error_handler.create_error_response(
                    e, ErrorType.PROCESSING_ERROR, request_id,
                    {'step': 'content_extraction'},
                    processing_time=time.time() - start_time
                )
        except Exception as e:
            extraction_duration = time.time() - extraction_start
            performance_logger.log_content_extraction(
                request_id, extraction_duration, 0, str(e)
            )
            return error_handler.handle_processing_error(e, "content_extraction", request_id)
        
        # Step 2.5: Detect language and process multilingual content
        language_start = time.time()
        try:
            # Detect language of the article content
            language_result = services['language_detector'].detect_language(article.content)
            
            # Process content based on detected language
            processed_content, confidence_adjustment = services['language_detector'].process_multilingual_content(
                article.content, language_result.language
            )
            
            # Update article content with processed version
            article.content = processed_content
            
            language_duration = time.time() - language_start
            performance_logger.log_step(
                request_id, "language_detection", language_duration,
                details={
                    'detected_language': language_result.language,
                    'confidence': language_result.confidence,
                    'is_supported': language_result.is_supported,
                    'fallback_used': language_result.fallback_used,
                    'confidence_adjustment': confidence_adjustment
                }
            )
            
            print(f"Language detected: {language_result.language} (confidence: {language_result.confidence:.2f})")
            
        except Exception as e:
            # Language detection failure shouldn't stop analysis
            language_duration = time.time() - language_start
            performance_logger.log_step(
                request_id, "language_detection", language_duration, error=str(e)
            )
            print(f"Language detection failed: {str(e)}, continuing with English fallback")
            language_result = None
            confidence_adjustment = 0.8  # Slight reduction for unknown language
        
        # Step 2.6: Detect fake news patterns
        pattern_start = time.time()
        try:
            # Detect patterns in article content and title
            pattern_result = services['pattern_detector'].detect_patterns(
                article.content, article.title
            )
            
            pattern_duration = time.time() - pattern_start
            performance_logger.log_step(
                request_id, "pattern_detection", pattern_duration,
                details={
                    'overall_score': pattern_result.overall_score,
                    'patterns_detected': len(pattern_result.patterns_detected),
                    'emotional_indicators': len(pattern_result.emotional_indicators),
                    'suspicious_phrases': len(pattern_result.suspicious_phrases),
                    'should_flag': services['pattern_detector'].should_flag_content(pattern_result)
                }
            )
            
            print(f"Pattern analysis: score={pattern_result.overall_score:.2f}, patterns={len(pattern_result.patterns_detected)}")
            
        except Exception as e:
            # Pattern detection failure shouldn't stop analysis
            pattern_duration = time.time() - pattern_start
            performance_logger.log_step(
                request_id, "pattern_detection", pattern_duration, error=str(e)
            )
            print(f"Pattern detection failed: {str(e)}, continuing without pattern analysis")
            pattern_result = None
        
        # Step 3: Summarize article and extract claims
        summarization_start = time.time()
        try:
            summary, key_claims = run_with_timeout(
                services['summarizer'].summarize_article,
                args=(article.content,),
                timeout_seconds=8
            )
            summarization_duration = time.time() - summarization_start
            performance_logger.log_summarization(
                request_id, summarization_duration, len(summary), len(key_claims)
            )
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "summarization", 8)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'summarization', 'timeout_seconds': 8},
                "Article summarization timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            summarization_duration = time.time() - summarization_start
            performance_logger.log_summarization(
                request_id, summarization_duration, 0, 0, str(e)
            )
            return error_handler.handle_api_error(e, "Groq API", request_id)
        
        # Step 4: Extract keywords for enhanced search
        keyword_start = time.time()
        try:
            keywords = run_with_timeout(
                services['keyword_extractor'].extract_keywords,
                args=(summary,),
                timeout_seconds=5
            )
            keyword_duration = time.time() - keyword_start
            performance_logger.log_keyword_extraction(
                request_id, keyword_duration, len(keywords)
            )
        except (TimeoutError, Exception) as e:
            # Continue without keywords if extraction fails
            keyword_duration = time.time() - keyword_start
            performance_logger.log_keyword_extraction(
                request_id, keyword_duration, 0, str(e)
            )
            print(f"Keyword extraction failed: {str(e)}")
            keywords = []
        
        # Step 5: Fetch related news articles using keywords
        news_fetch_start = time.time()
        try:
            related_articles = run_with_timeout(
                services['news_fetcher'].fetch_related_news,
                args=(summary, keywords),
                timeout_seconds=8
            )
            news_fetch_duration = time.time() - news_fetch_start
            performance_logger.log_news_fetch(
                request_id, news_fetch_duration, len(related_articles)
            )
            
            # Handle case where no related articles found
            if not related_articles:
                processing_time = time.time() - start_time
                
                # Store result in cache
                services['cache'].store_result(
                    url=url,
                    summary=summary,
                    verdict="UNCERTAIN",
                    confidence=0.3,
                    explanation="No related articles found for verification",
                    matched_articles=[],
                    key_claims=key_claims,
                    processing_time=processing_time
                )
                
                # Complete analysis tracking
                performance_logger.complete_analysis(
                    request_id, "UNCERTAIN", 0.3, processing_time
                )
                
                response = jsonify({
                    'verdict': 'UNCERTAIN',
                    'confidence': '30%',
                    'explanation': 'No related articles found for verification',
                    'matched_articles': [],
                    'processing_time': round(processing_time, 2)
                })
                
                return add_security_headers(response)
                
        except TimeoutError:
            # Continue with reduced functionality if news API times out
            news_fetch_duration = time.time() - news_fetch_start
            performance_logger.log_news_fetch(
                request_id, news_fetch_duration, 0, "Timeout"
            )
            performance_logger.log_timeout(request_id, "news_fetch", 8)
            print("News API fetch timed out, continuing with reduced functionality")
            related_articles = []
        except Exception as e:
            # Continue with reduced functionality if news API fails
            news_fetch_duration = time.time() - news_fetch_start
            performance_logger.log_news_fetch(
                request_id, news_fetch_duration, 0, str(e)
            )
            performance_logger.log_api_failure(request_id, "News API", str(e))
            related_articles = []
        
        # Step 6: Compute semantic similarities
        similarity_start = time.time()
        try:
            similarity_scores = run_with_timeout(
                services['similarity'].compute_similarities,
                args=(article, related_articles),
                timeout_seconds=15  # Increased from 6 to 15 seconds for more articles
            )
            similarity_duration = time.time() - similarity_start
            avg_similarity = sum(score.score for score in similarity_scores) / len(similarity_scores) if similarity_scores else 0
            performance_logger.log_similarity_analysis(
                request_id, similarity_duration, len(similarity_scores), avg_similarity
            )
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "similarity_analysis", 6)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'similarity_analysis', 'timeout_seconds': 6},
                "Similarity analysis timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            similarity_duration = time.time() - similarity_start
            performance_logger.log_similarity_analysis(
                request_id, similarity_duration, 0, 0, str(e)
            )
            return error_handler.handle_processing_error(e, "similarity_analysis", request_id)
        
        # Step 7: Make decision using enhanced rules with contradiction detection
        decision_start = time.time()
        try:
            # Pass the article source to the decision engine
            result = run_with_timeout(
                services['decision'].make_decision,
                args=(similarity_scores, summary, key_claims, related_articles, pattern_result, article.source),
                timeout_seconds=8
            )
            decision_duration = time.time() - decision_start
            performance_logger.log_decision_making(
                request_id, decision_duration, result.verdict.value, result.confidence
            )
            
            # Apply language confidence adjustment if language detection was performed
            if 'confidence_adjustment' in locals() and confidence_adjustment != 1.0:
                original_confidence = result.confidence
                result.confidence = max(0.1, min(1.0, result.confidence * confidence_adjustment))
                
                # Add language info to explanation if fallback was used
                if language_result and language_result.fallback_used:
                    language_info = f" [Language: {language_result.language}, fallback processing applied]"
                    result.explanation += language_info
                
                performance_logger.log_step(
                    request_id, "language_confidence_adjustment",
                    details={
                        'original_confidence': original_confidence,
                        'adjusted_confidence': result.confidence,
                        'adjustment_factor': confidence_adjustment
                    }
                )
        
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "decision_making", 8)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'decision_making', 'timeout_seconds': 8},
                "Decision making timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            decision_duration = time.time() - decision_start
            performance_logger.log_decision_making(
                request_id, decision_duration, "ERROR", 0, str(e)
            )
            return error_handler.handle_processing_error(e, "decision_making", request_id)
        
        # Step 8: Calculate processing time
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        
        # Step 9: Store result in cache with error handling
        try:
            services['cache'].store_result(
                url=url,
                summary=summary,
                verdict=result.verdict.value,
                confidence=result.confidence,
                explanation=result.explanation,
                matched_articles=result.matched_articles,
                key_claims=key_claims,
                processing_time=processing_time
            )
        except Exception as e:
            # Log error but don't fail the request - cache failure is not critical
            performance_logger.log_step(request_id, "cache_storage", error=str(e))
            error_handler.handle_database_error(e, "cache_storage", request_id)
            print(f"Cache storage failed: {str(e)}, continuing without caching")
        
        # Complete analysis tracking
        performance_logger.complete_analysis(
            request_id, result.verdict.value, result.confidence, processing_time
        )
        
        # Save to user history if logged in
        save_to_user_history(
            input_type='url',
            input_content=url,
            verdict=result.verdict.value,
            confidence=result.confidence,
            explanation=result.explanation,
            matched_articles=result.matched_articles,
            processing_time=processing_time
        )
        
        # Step 10: Return formatted response
        response = jsonify({
            'verdict': result.verdict.value,
            'confidence': f"{result.confidence:.0%}",
            'explanation': result.explanation,
            'matched_articles': result.matched_articles[:3],  # Top 3
            'processing_time': round(processing_time, 2)
        })
        
        return add_security_headers(response)
        
    except Exception as e:
        # Handle unexpected errors with comprehensive error handling
        processing_time = time.time() - start_time
        
        # Complete analysis tracking with error
        performance_logger.complete_analysis(
            request_id, "ERROR", 0, processing_time, str(e)
        )
        
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR, request_id,
            {'step': 'unexpected_error'},
            "An unexpected error occurred during analysis",
            processing_time
        )

def _is_valid_url(url: str) -> bool:
    """Validate URL format and protocol"""
    if not url or not isinstance(url, str):
        return False
    
    try:
        # Parse URL to validate structure
        parsed = urlparse(url.strip())
        
        # Check for valid HTTP/HTTPS protocol only
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Check for valid domain
        if not parsed.netloc:
            return False
        
        # Basic domain validation
        domain_pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        if not domain_pattern.match(parsed.netloc.split(':')[0]):
            return False
        
        return True
        
    except Exception:
        return False

def _detect_source_from_text(text: str) -> str:
    """
    Detect news source from text content by looking for source mentions
    This helps identify trusted sources even when analyzing raw text
    """
    if not text:
        return ""
    
    # Comprehensive list of trusted sources to detect
    trusted_sources_patterns = {
        # International sources
        'BBC': ['bbc', 'british broadcasting corporation'],
        'Reuters': ['reuters'],
        'Associated Press': ['associated press', 'ap news', 'the associated press'],
        'CNN': ['cnn', 'cable news network'],
        'The Guardian': ['the guardian', 'guardian'],
        'New York Times': ['new york times', 'nytimes', 'the new york times'],
        'Washington Post': ['washington post', 'washingtonpost'],
        'Wall Street Journal': ['wall street journal', 'wsj'],
        'NPR': ['npr', 'national public radio'],
        'PBS': ['pbs', 'public broadcasting service'],
        'Bloomberg': ['bloomberg'],
        'Financial Times': ['financial times', 'ft.com'],
        'Al Jazeera': ['al jazeera', 'aljazeera'],
        'France 24': ['france 24', 'france24'],
        'DW': ['deutsche welle', 'dw.com'],
        
        # Indian sources
        'The Hindu': ['the hindu', 'thehindu'],
        'Indian Express': ['indian express', 'indianexpress'],
        'Times of India': ['times of india', 'timesofindia'],
        'Hindustan Times': ['hindustan times', 'hindustantimes'],
        'NDTV': ['ndtv'],
        'India Today': ['india today', 'indiatoday'],
        'News18': ['news18'],
        'Firstpost': ['firstpost'],
        'The Quint': ['the quint', 'thequint'],
        'Scroll': ['scroll.in', 'scroll'],
        'The Print': ['the print', 'theprint'],
        'Mint': ['mint', 'livemint'],
        'Moneycontrol': ['moneycontrol'],
        'Economic Times': ['economic times', 'economictimes'],
        'Deccan Herald': ['deccan herald'],
        'Telegraph India': ['telegraph india', 'telegraphindia'],
        'Tribune India': ['tribune india', 'tribuneindia'],
        
        # News agencies
        'PTI': ['pti', 'press trust of india'],
        'ANI': ['ani', 'asian news international'],
        'IANS': ['ians', 'indo-asian news service']
    }
    
    text_lower = text.lower()
    
    # Check first 500 characters for source mentions (usually at top or bottom)
    text_start = text_lower[:500]
    text_end = text_lower[-500:] if len(text_lower) > 500 else text_lower
    search_text = text_start + " " + text_end
    
    # Look for source patterns
    for source_name, patterns in trusted_sources_patterns.items():
        for pattern in patterns:
            # Check for exact mentions
            if pattern in search_text:
                return source_name
            
            # Check for URL-like patterns (e.g., "from bbc.com")
            if f"{pattern}.com" in search_text or f"{pattern}.co.uk" in search_text:
                return source_name
            
            # Check for attribution patterns
            if f"by {pattern}" in search_text or f"from {pattern}" in search_text:
                return source_name
            
            # Check for copyright patterns
            if f"© {pattern}" in search_text or f"copyright {pattern}" in search_text:
                return source_name
    
    return ""

@analyze_bp.route('/analyze-text', methods=['POST'])
def analyze_text():
    """
    Analyze text content for authenticity
    
    Expected JSON payload:
    {
        "text": "News content to analyze..."
    }
    
    Returns:
    {
        "verdict": "REAL|FAKE|UNCERTAIN",
        "confidence": "85%",
        "explanation": "Analysis explanation...",
        "matched_articles": [...],
        "processing_time": 2.5
    }
    """
    start_time = time.time()
    
    # Start analysis tracking
    request_id = performance_logger.start_analysis('text_analysis')
    
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'text' not in data:
            return error_handler.create_error_response(
                ValueError("Missing 'text' field in JSON payload"),
                ErrorType.VALIDATION_ERROR,
                request_id,
                processing_time=time.time() - start_time
            )
        
        text_content = data['text'].strip()
        
        if not text_content:
            return error_handler.create_error_response(
                ValueError("Text content cannot be empty"),
                ErrorType.VALIDATION_ERROR,
                request_id,
                processing_time=time.time() - start_time
            )
        
        # Initialize services
        try:
            services = get_services()
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.INTERNAL_ERROR, request_id,
                {'step': 'service_initialization'},
                processing_time=time.time() - start_time
            )
        
        # Step 1: Detect language
        language_start = time.time()
        try:
            language_result = services['language_detector'].detect_language(text_content)
            processed_content, confidence_adjustment = services['language_detector'].process_multilingual_content(
                text_content, language_result.language
            )
            text_content = processed_content
            
            language_duration = time.time() - language_start
            performance_logger.log_step(
                request_id, "language_detection", language_duration,
                details={'detected_language': language_result.language}
            )
        except Exception as e:
            confidence_adjustment = 0.8
            print(f"Language detection failed: {str(e)}")
        
        # Step 2: Detect patterns
        pattern_start = time.time()
        try:
            pattern_result = services['pattern_detector'].detect_patterns(text_content, "")
            pattern_duration = time.time() - pattern_start
            performance_logger.log_step(request_id, "pattern_detection", pattern_duration)
        except Exception as e:
            pattern_result = None
            print(f"Pattern detection failed: {str(e)}")
        
        # Step 3: Summarize and extract claims
        summarization_start = time.time()
        try:
            summary, key_claims = run_with_timeout(
                services['summarizer'].summarize_article,
                args=(text_content,),
                timeout_seconds=20
            )
            summarization_duration = time.time() - summarization_start
            performance_logger.log_summarization(request_id, summarization_duration, len(summary), len(key_claims))
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'summarization'},
                processing_time=time.time() - start_time
            )
        
        # Step 4: Extract keywords
        keyword_start = time.time()
        try:
            keywords = run_with_timeout(
                services['keyword_extractor'].extract_keywords,
                args=(summary,),
                timeout_seconds=15
            )
            keyword_duration = time.time() - keyword_start
            performance_logger.log_keyword_extraction(request_id, keyword_duration, len(keywords))
        except Exception as e:
            keywords = []
            print(f"Keyword extraction failed: {str(e)}")
        
        # Step 5: Fetch related news
        news_fetch_start = time.time()
        try:
            related_articles = run_with_timeout(
                services['news_fetcher'].fetch_related_news,
                args=(summary, keywords),
                timeout_seconds=20  # Increased to 20 seconds for SerpAPI + fallback
            )
            news_fetch_duration = time.time() - news_fetch_start
            performance_logger.log_news_fetch(request_id, news_fetch_duration, len(related_articles))
            
            if not related_articles:
                processing_time = time.time() - start_time
                performance_logger.complete_analysis(request_id, "UNCERTAIN", 0.3, processing_time)
                
                response = jsonify({
                    'verdict': 'UNCERTAIN',
                    'confidence': '30%',
                    'explanation': 'No related articles found for verification. This could mean the news is very recent or not widely reported.',
                    'matched_articles': [],
                    'processing_time': round(processing_time, 2)
                })
                
                return add_security_headers(response)
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "news_fetch", 20)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'news_fetch', 'timeout_seconds': 20},
                "News fetching timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            news_fetch_duration = time.time() - news_fetch_start
            performance_logger.log_news_fetch(
                request_id, news_fetch_duration, 0, str(e)
            )
            print(f"News fetch failed: {str(e)}")
            related_articles = []
            
            # If news fetch completely fails, return uncertain verdict
            processing_time = time.time() - start_time
            performance_logger.complete_analysis(request_id, "UNCERTAIN", 0.2, processing_time)
            
            response = jsonify({
                'verdict': 'UNCERTAIN',
                'confidence': '20%',
                'explanation': 'Unable to fetch related articles for verification. Please try again later.',
                'matched_articles': [],
                'processing_time': round(processing_time, 2)
            })
            
            return add_security_headers(response)
        
        # Step 6: Compute similarities
        from services.extractor import ArticleContent
        
        # Try to detect source from text content (e.g., if user pasted from BBC)
        detected_source = _detect_source_from_text(text_content)
        text_article = ArticleContent(
            title="", 
            content=text_content, 
            url="", 
            source=detected_source
        )
        
        if detected_source:
            print(f"Detected source from text: {detected_source}")
        
        similarity_start = time.time()
        try:
            similarity_scores = run_with_timeout(
                services['similarity'].compute_similarities,
                args=(text_article, related_articles),
                timeout_seconds=15  # Increased from 60 to 15 seconds (was too high)
            )
            similarity_duration = time.time() - similarity_start
            avg_similarity = sum(score.score for score in similarity_scores) / len(similarity_scores) if similarity_scores else 0
            performance_logger.log_similarity_analysis(request_id, similarity_duration, len(similarity_scores), avg_similarity)
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "similarity_analysis", 15)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'similarity_analysis', 'timeout_seconds': 15},
                "Similarity analysis timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            similarity_duration = time.time() - similarity_start
            performance_logger.log_similarity_analysis(
                request_id, similarity_duration, 0, 0, str(e)
            )
            return error_handler.create_error_response(
                e, ErrorType.PROCESSING_ERROR, request_id,
                {'step': 'similarity_analysis'},
                "Failed to compute similarity scores",
                processing_time=time.time() - start_time
            )
        
        # Step 7: Make decision
        decision_start = time.time()
        try:
            result = run_with_timeout(
                services['decision'].make_decision,
                kwargs={
                    'similarity_scores': similarity_scores,
                    'summary': summary,
                    'claims': key_claims,
                    'related_articles': related_articles,
                    'pattern_result': pattern_result,
                    'input_source': detected_source
                },
                timeout_seconds=8
            )
            decision_duration = time.time() - decision_start
            performance_logger.log_decision_making(request_id, decision_duration, result.verdict.value, result.confidence)
            
            if 'confidence_adjustment' in locals():
                result.confidence = max(0.1, min(1.0, result.confidence * confidence_adjustment))
        except TimeoutError as e:
            performance_logger.log_timeout(request_id, "decision_making", 8)
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id,
                {'step': 'decision_making', 'timeout_seconds': 8},
                "Decision making timed out, please try again",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            decision_duration = time.time() - decision_start
            performance_logger.log_decision_making(
                request_id, decision_duration, "ERROR", 0, str(e)
            )
            return error_handler.create_error_response(
                e, ErrorType.PROCESSING_ERROR, request_id,
                {'step': 'decision_making'},
                "Failed to make verification decision",
                processing_time=time.time() - start_time
            )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        
        # Complete analysis tracking
        performance_logger.complete_analysis(request_id, result.verdict.value, result.confidence, processing_time)
        
        # Save to user history if logged in
        save_to_user_history(
            input_type='text',
            input_content=text_content[:500],  # Save first 500 chars as preview
            verdict=result.verdict.value,
            confidence=result.confidence,
            explanation=result.explanation,
            matched_articles=result.matched_articles,
            processing_time=processing_time
        )
        
        # Return formatted response
        response = jsonify({
            'verdict': result.verdict.value,
            'confidence': f"{result.confidence:.0%}",
            'explanation': result.explanation,
            'matched_articles': result.matched_articles[:3],
            'processing_time': round(processing_time, 2)
        })
        
        return add_security_headers(response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        performance_logger.complete_analysis(request_id, "ERROR", 0, processing_time, str(e))
        
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR, request_id,
            {'step': 'unexpected_error'},
            "An unexpected error occurred during text analysis",
            processing_time
        )

@analyze_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """
    Analyze image content using OCR and fake news detection
    """
    start_time = time.time()
    request_id = performance_logger.start_analysis('image_analysis')
    
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return error_handler.create_error_response(
                ValueError("No image file provided"),
                ErrorType.VALIDATION_ERROR, request_id,
                processing_time=time.time() - start_time
            )
        
        image_file = request.files['image']
        
        if image_file.filename == '':
            return error_handler.create_error_response(
                ValueError("Empty filename"),
                ErrorType.VALIDATION_ERROR, request_id,
                processing_time=time.time() - start_time
            )
            
        try:
            import pytesseract
            from PIL import Image
            import io
            
            image_bytes = image_file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            # Extract text using Tesseract
            extracted_text = pytesseract.image_to_string(image)
        except ImportError:
            return error_handler.create_error_response(
                RuntimeError("OCR libraries (pytesseract or Pillow) are not installed."),
                ErrorType.INTERNAL_ERROR, request_id,
                user_message="OCR libraries (pytesseract or Pillow) are not installed.",
                processing_time=time.time() - start_time
            )
        except Exception as e:
            if "tesseract is not installed" in str(e).lower():
                return error_handler.create_error_response(
                    RuntimeError("Tesseract OCR is not installed on the system. Please install it to use image analysis."),
                    ErrorType.INTERNAL_ERROR, request_id,
                    user_message="Tesseract OCR is not installed on the system. Please install it to use image analysis.",
                    processing_time=time.time() - start_time
                )
            return error_handler.create_error_response(
                ValueError(f"Failed to process image: {str(e)}"),
                ErrorType.PROCESSING_ERROR, request_id,
                processing_time=time.time() - start_time
            )
            
        if not extracted_text or not extracted_text.strip() or len(extracted_text.strip()) < 15:
            return error_handler.create_error_response(
                ValueError("Could not extract enough text from the image for analysis. Please ensure the image contains clear, readable text."),
                ErrorType.VALIDATION_ERROR, request_id,
                processing_time=time.time() - start_time
            )
            
        text_content = extracted_text.strip()
        
        # Now process the text exactly like analyze_text
        try:
            services = get_services()
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.INTERNAL_ERROR, request_id,
                {'step': 'service_initialization'},
                processing_time=time.time() - start_time
            )
            
        # Step 1: Detect language
        language_start = time.time()
        try:
            language_result = services['language_detector'].detect_language(text_content)
            processed_content, confidence_adjustment = services['language_detector'].process_multilingual_content(
                text_content, language_result.language
            )
            text_content = processed_content
            performance_logger.log_step(request_id, "language_detection", time.time() - language_start,
                details={'detected_language': language_result.language})
        except Exception as e:
            confidence_adjustment = 0.8
            print(f"Language detection failed: {str(e)}")
            
        # Step 2: Detect patterns
        pattern_start = time.time()
        try:
            pattern_result = services['pattern_detector'].detect_patterns(text_content, "")
            performance_logger.log_step(request_id, "pattern_detection", time.time() - pattern_start)
        except Exception as e:
            pattern_result = None
            print(f"Pattern detection failed: {str(e)}")
            
        # Step 3: Summarize and extract claims
        summarization_start = time.time()
        try:
            summary, key_claims = run_with_timeout(
                services['summarizer'].summarize_article,
                args=(text_content,), timeout_seconds=8
            )
            performance_logger.log_summarization(request_id, time.time() - summarization_start, len(summary), len(key_claims))
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id, {'step': 'summarization'},
                processing_time=time.time() - start_time
            )
            
        # Step 4: Extract keywords
        keyword_start = time.time()
        try:
            keywords = run_with_timeout(
                services['keyword_extractor'].extract_keywords,
                args=(summary,), timeout_seconds=5
            )
            performance_logger.log_keyword_extraction(request_id, time.time() - keyword_start, len(keywords))
        except Exception as e:
            keywords = []
            
        # Step 5: Fetch related news
        news_fetch_start = time.time()
        try:
            related_articles = run_with_timeout(
                services['news_fetcher'].fetch_related_news,
                args=(summary, keywords), timeout_seconds=8
            )
            performance_logger.log_news_fetch(request_id, time.time() - news_fetch_start, len(related_articles))
            
            if not related_articles:
                processing_time = time.time() - start_time
                performance_logger.complete_analysis(request_id, "UNCERTAIN", 0.3, processing_time)
                response = jsonify({
                    'verdict': 'UNCERTAIN', 'confidence': '30%',
                    'explanation': 'No related articles found for verification',
                    'matched_articles': [], 'extracted_text': extracted_text[:500] + '...',
                    'processing_time': round(processing_time, 2)
                })
                return add_security_headers(response)
        except Exception as e:
            related_articles = []
            
        # Step 6: Compute similarities
        from services.decision import Article
        text_article = Article(title="", content=text_content, url="", source="")
        similarity_start = time.time()
        try:
            similarity_scores = run_with_timeout(
                services['similarity'].compute_similarities,
                args=(text_article, related_articles), timeout_seconds=6
            )
            avg_similarity = sum(score.score for score in similarity_scores) / len(similarity_scores) if similarity_scores else 0
            performance_logger.log_similarity_analysis(request_id, time.time() - similarity_start, len(similarity_scores), avg_similarity)
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id, {'step': 'similarity_analysis'},
                processing_time=time.time() - start_time
            )
            
        # Step 7: Make decision
        decision_start = time.time()
        try:
            result = run_with_timeout(
                services['decision'].make_decision,
                args=(similarity_scores, summary, key_claims, related_articles, pattern_result),
                timeout_seconds=8
            )
            performance_logger.log_decision_making(request_id, time.time() - decision_start, result.verdict.value, result.confidence)
            if 'confidence_adjustment' in locals():
                result.confidence = max(0.1, min(1.0, result.confidence * confidence_adjustment))
        except Exception as e:
            return error_handler.create_error_response(
                e, ErrorType.TIMEOUT_ERROR, request_id, {'step': 'decision_making'},
                processing_time=time.time() - start_time
            )
            
        processing_time = time.time() - start_time
        result.processing_time = processing_time
        performance_logger.complete_analysis(request_id, result.verdict.value, result.confidence, processing_time)
        
        response = jsonify({
            'verdict': result.verdict.value,
            'confidence': f"{result.confidence:.0%}",
            'explanation': result.explanation,
            'matched_articles': result.matched_articles[:3],
            'extracted_text': extracted_text[:500] + ('...' if len(extracted_text) > 500 else ''),
            'processing_time': round(processing_time, 2)
        })
        return add_security_headers(response)
        
    except Exception as e:
        processing_time = time.time() - start_time
        performance_logger.complete_analysis(request_id, "ERROR", 0, processing_time, str(e))
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR, request_id, {'step': 'unexpected_error'},
            "An unexpected error occurred during image analysis", processing_time
        )

@analyze_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with comprehensive error handling"""
    try:
        # Test service initialization
        services = get_services()
        
        # Basic service health checks
        health_status = {
            'status': 'healthy',
            'service': 'fake-news-detector-backend',
            'timestamp': time.time(),
            'services': {
                'cache': 'ok',
                'extractor': 'ok',
                'summarizer': 'ok',
                'keyword_extractor': 'ok',
                'news_fetcher': 'ok',
                'similarity': 'ok',
                'decision': 'ok',
                'language_detector': 'ok',
                'pattern_detector': 'ok'
            }
        }
        
        # Test individual service health
        service_errors = []
        
        # Test LLM service availability
        try:
            if hasattr(services['summarizer'], 'is_service_available'):
                if not services['summarizer'].is_service_available():
                    health_status['services']['summarizer'] = 'unavailable'
                    health_status['status'] = 'degraded'
                    service_errors.append('Groq API unavailable')
        except Exception as e:
            health_status['services']['summarizer'] = 'error'
            health_status['status'] = 'degraded'
            service_errors.append(f'Groq API error: {str(e)}')
        
        # Test database connectivity
        try:
            services['cache'].get_cached_result('health-check-test')
            health_status['services']['cache'] = 'ok'
        except Exception as e:
            health_status['services']['cache'] = 'error'
            health_status['status'] = 'degraded'
            service_errors.append(f'Database error: {str(e)}')
        
        # Test similarity engine
        try:
            # Quick test of similarity engine
            test_embedding = services['similarity'].generate_embedding("test")
            if test_embedding is not None:
                health_status['services']['similarity'] = 'ok'
            else:
                health_status['services']['similarity'] = 'error'
                health_status['status'] = 'degraded'
                service_errors.append('Similarity engine error')
        except Exception as e:
            health_status['services']['similarity'] = 'error'
            health_status['status'] = 'degraded'
            service_errors.append(f'Similarity engine error: {str(e)}')
        
        # Test language detector
        try:
            # Quick test of language detector
            test_result = services['language_detector'].detect_language("This is a test sentence in English.")
            if test_result and test_result.language:
                health_status['services']['language_detector'] = 'ok'
            else:
                health_status['services']['language_detector'] = 'error'
                health_status['status'] = 'degraded'
                service_errors.append('Language detector error')
        except Exception as e:
            health_status['services']['language_detector'] = 'error'
            health_status['status'] = 'degraded'
            service_errors.append(f'Language detector error: {str(e)}')
        
        # Test pattern detector
        try:
            # Quick test of pattern detector
            test_result = services['pattern_detector'].detect_patterns("This is a test article with SHOCKING news!")
            if test_result and hasattr(test_result, 'overall_score'):
                health_status['services']['pattern_detector'] = 'ok'
            else:
                health_status['services']['pattern_detector'] = 'error'
                health_status['status'] = 'degraded'
                service_errors.append('Pattern detector error')
        except Exception as e:
            health_status['services']['pattern_detector'] = 'error'
            health_status['status'] = 'degraded'
            service_errors.append(f'Pattern detector error: {str(e)}')
        
        # Add error details if any
        if service_errors:
            health_status['errors'] = service_errors
        
        # Add system info
        health_status['system'] = {
            'error_handler': 'active',
            'rate_limiter': 'active',
            'security_validator': 'active',
            'performance_logger': 'active'
        }
        
        return add_security_headers(jsonify(health_status))
        
    except Exception as e:
        return error_handler.create_error_response(
            e, ErrorType.INTERNAL_ERROR,
            context={'endpoint': 'health_check'},
            user_message="Health check failed"
        )