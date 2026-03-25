"""
Comprehensive logging system for fake news detection backend
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class PerformanceLogger:
    """Service for tracking processing steps, timing, and performance metrics"""
    
    def __init__(self, log_level: str = "INFO", log_file: str = "fake_news_detector.log"):
        """Initialize logging system"""
        self.log_file = log_file
        self.setup_logging(log_level)
        self.performance_metrics = {}
        
    def setup_logging(self, log_level: str):
        """Set up logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Set up file handler
        file_handler = logging.FileHandler(log_dir / self.log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(log_format))
        
        # Configure logger
        self.logger = logging.getLogger('fake_news_detector')
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def start_analysis(self, url: str, request_id: str = None) -> str:
        """Start analysis tracking"""
        if not request_id:
            request_id = f"req_{int(time.time() * 1000)}"
        
        self.performance_metrics[request_id] = {
            'url': url,
            'start_time': time.time(),
            'steps': {},
            'errors': [],
            'status': 'started'
        }
        
        self.logger.info(f"[{request_id}] Analysis started for URL: {url}")
        return request_id
    
    def log_step(self, request_id: str, step_name: str, duration: float = None, 
                 details: Dict[str, Any] = None, error: str = None):
        """Log processing step with timing and details"""
        if request_id not in self.performance_metrics:
            self.logger.warning(f"Request ID {request_id} not found in metrics")
            return
        
        step_data = {
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'details': details or {},
            'error': error
        }
        
        self.performance_metrics[request_id]['steps'][step_name] = step_data
        
        if error:
            self.performance_metrics[request_id]['errors'].append({
                'step': step_name,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
            self.logger.error(f"[{request_id}] {step_name} failed: {error}")
        else:
            duration_str = f" ({duration:.2f}s)" if duration else ""
            details_str = f" - {details}" if details else ""
            self.logger.info(f"[{request_id}] {step_name} completed{duration_str}{details_str}")
    
    def log_cache_hit(self, request_id: str, url: str):
        """Log cache hit"""
        self.log_step(request_id, "cache_check", details={'result': 'hit', 'url': url})
    
    def log_cache_miss(self, request_id: str, url: str):
        """Log cache miss"""
        self.log_step(request_id, "cache_check", details={'result': 'miss', 'url': url})
    
    def log_content_extraction(self, request_id: str, duration: float, content_length: int, error: str = None):
        """Log content extraction step"""
        details = {'content_length': content_length} if not error else {}
        self.log_step(request_id, "content_extraction", duration, details, error)
    
    def log_summarization(self, request_id: str, duration: float, summary_length: int, 
                         claims_count: int, error: str = None):
        """Log summarization step"""
        details = {
            'summary_length': summary_length,
            'claims_count': claims_count
        } if not error else {}
        self.log_step(request_id, "summarization", duration, details, error)
    
    def log_keyword_extraction(self, request_id: str, duration: float, keywords_count: int, error: str = None):
        """Log keyword extraction step"""
        details = {'keywords_count': keywords_count} if not error else {}
        self.log_step(request_id, "keyword_extraction", duration, details, error)
    
    def log_news_fetch(self, request_id: str, duration: float, articles_count: int, error: str = None):
        """Log news fetching step"""
        details = {'articles_fetched': articles_count} if not error else {}
        self.log_step(request_id, "news_fetch", duration, details, error)
    
    def log_similarity_analysis(self, request_id: str, duration: float, similarity_scores_count: int, 
                               avg_similarity: float = None, error: str = None):
        """Log similarity analysis step"""
        details = {
            'similarity_scores_count': similarity_scores_count,
            'avg_similarity': avg_similarity
        } if not error else {}
        self.log_step(request_id, "similarity_analysis", duration, details, error)
    
    def log_contradiction_check(self, request_id: str, duration: float, contradictions_found: int, error: str = None):
        """Log contradiction checking step"""
        details = {'contradictions_found': contradictions_found} if not error else {}
        self.log_step(request_id, "contradiction_check", duration, details, error)
    
    def log_decision_making(self, request_id: str, duration: float, verdict: str, 
                           confidence: float, error: str = None):
        """Log decision making step"""
        details = {
            'verdict': verdict,
            'confidence': confidence
        } if not error else {}
        self.log_step(request_id, "decision_making", duration, details, error)
    
    def complete_analysis(self, request_id: str, verdict: str, confidence: float, 
                         processing_time: float, error: str = None):
        """Complete analysis tracking"""
        if request_id not in self.performance_metrics:
            self.logger.warning(f"Request ID {request_id} not found in metrics")
            return
        
        metrics = self.performance_metrics[request_id]
        metrics['status'] = 'error' if error else 'completed'
        metrics['end_time'] = time.time()
        metrics['total_processing_time'] = processing_time
        metrics['verdict'] = verdict
        metrics['confidence'] = confidence
        
        if error:
            metrics['final_error'] = error
            self.logger.error(f"[{request_id}] Analysis failed: {error}")
        else:
            self.logger.info(f"[{request_id}] Analysis completed - Verdict: {verdict}, "
                           f"Confidence: {confidence:.1%}, Time: {processing_time:.2f}s")
        
        # Log performance summary
        self._log_performance_summary(request_id)
    
    def _log_performance_summary(self, request_id: str):
        """Log performance summary for analysis"""
        metrics = self.performance_metrics[request_id]
        
        # Calculate step timings
        step_timings = {}
        for step_name, step_data in metrics['steps'].items():
            if step_data['duration']:
                step_timings[step_name] = step_data['duration']
        
        # Find slowest steps
        if step_timings:
            slowest_steps = sorted(step_timings.items(), key=lambda x: x[1], reverse=True)[:3]
            slowest_info = ", ".join([f"{step}: {duration:.2f}s" for step, duration in slowest_steps])
            
            self.logger.info(f"[{request_id}] Performance summary - "
                           f"Total: {metrics.get('total_processing_time', 0):.2f}s, "
                           f"Slowest steps: {slowest_info}")
    
    def log_api_failure(self, request_id: str, api_name: str, error: str):
        """Log API failure"""
        self.logger.error(f"[{request_id}] {api_name} API failure: {error}")
        
        if request_id in self.performance_metrics:
            self.performance_metrics[request_id]['errors'].append({
                'api': api_name,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
    
    def log_timeout(self, request_id: str, operation: str, timeout_seconds: int):
        """Log timeout occurrence"""
        self.logger.warning(f"[{request_id}] {operation} timed out after {timeout_seconds}s")
    
    def log_retry_attempt(self, request_id: str, operation: str, attempt: int, max_attempts: int):
        """Log retry attempt"""
        self.logger.info(f"[{request_id}] {operation} retry attempt {attempt}/{max_attempts}")
    
    def get_metrics(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a request"""
        return self.performance_metrics.get(request_id)
    
    def clear_old_metrics(self, max_age_hours: int = 24):
        """Clear old performance metrics to prevent memory buildup"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        old_requests = []
        for request_id, metrics in self.performance_metrics.items():
            if metrics.get('start_time', current_time) < cutoff_time:
                old_requests.append(request_id)
        
        for request_id in old_requests:
            del self.performance_metrics[request_id]
        
        if old_requests:
            self.logger.info(f"Cleared {len(old_requests)} old metric entries")

# Global logger instance
performance_logger = PerformanceLogger()