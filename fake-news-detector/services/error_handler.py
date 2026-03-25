"""
Comprehensive error handling service
"""

import traceback
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from flask import jsonify
from services.security import security_validator
from services.logger import performance_logger

class ErrorType(Enum):
    """Error type classifications"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    DATABASE_ERROR = "database_error"
    PROCESSING_ERROR = "processing_error"
    INTERNAL_ERROR = "internal_error"
    RESOURCE_ERROR = "resource_error"

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorHandler:
    """Centralized error handling service"""
    
    def __init__(self):
        """Initialize error handler"""
        self.logger = logging.getLogger('fake_news_detector.errors')
        
        # Error code mappings
        self.error_codes = {
            ErrorType.VALIDATION_ERROR: (400, "Bad Request"),
            ErrorType.AUTHENTICATION_ERROR: (401, "Unauthorized"),
            ErrorType.RATE_LIMIT_ERROR: (429, "Too Many Requests"),
            ErrorType.TIMEOUT_ERROR: (408, "Request Timeout"),
            ErrorType.NETWORK_ERROR: (502, "Bad Gateway"),
            ErrorType.API_ERROR: (503, "Service Unavailable"),
            ErrorType.DATABASE_ERROR: (500, "Internal Server Error"),
            ErrorType.PROCESSING_ERROR: (422, "Unprocessable Entity"),
            ErrorType.INTERNAL_ERROR: (500, "Internal Server Error"),
            ErrorType.RESOURCE_ERROR: (507, "Insufficient Storage")
        }
        
        # User-friendly error messages
        self.user_messages = {
            ErrorType.VALIDATION_ERROR: "Invalid input provided",
            ErrorType.AUTHENTICATION_ERROR: "Authentication required",
            ErrorType.RATE_LIMIT_ERROR: "Too many requests, please try again later",
            ErrorType.TIMEOUT_ERROR: "Request timed out, please try again",
            ErrorType.NETWORK_ERROR: "Network connectivity issue",
            ErrorType.API_ERROR: "External service temporarily unavailable",
            ErrorType.DATABASE_ERROR: "Data storage issue",
            ErrorType.PROCESSING_ERROR: "Unable to process the request",
            ErrorType.INTERNAL_ERROR: "Internal server error",
            ErrorType.RESOURCE_ERROR: "System resources temporarily unavailable"
        }
    
    def handle_error(self, error: Exception, error_type: ErrorType, 
                    request_id: str = None, context: Dict[str, Any] = None,
                    user_message: str = None) -> Tuple[Dict, int]:
        """
        Handle error with comprehensive logging and response formatting
        
        Args:
            error: The exception that occurred
            error_type: Classification of the error
            request_id: Request ID for tracking
            context: Additional context information
            user_message: Custom user-friendly message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        # Determine severity
        severity = self._determine_severity(error_type, error)
        
        # Get error code and status
        status_code, status_text = self.error_codes.get(error_type, (500, "Internal Server Error"))
        
        # Create error ID for tracking
        error_id = f"err_{int(__import__('time').time() * 1000)}"
        
        # Log error with appropriate level
        self._log_error(error, error_type, severity, error_id, request_id, context)
        
        # Create user-friendly response
        response_data = {
            'error': True,
            'error_type': error_type.value,
            'message': user_message or self.user_messages.get(error_type, "An error occurred"),
            'error_id': error_id,
            'status': status_code
        }
        
        # Add context for debugging (only in development)
        if self._is_debug_mode():
            response_data['debug'] = {
                'error_class': error.__class__.__name__,
                'error_message': str(error),
                'context': context or {}
            }
        
        # Add retry information for recoverable errors
        if self._is_recoverable_error(error_type):
            response_data['retry_after'] = self._get_retry_delay(error_type)
            response_data['recoverable'] = True
        
        return response_data, status_code
    
    def create_error_response(self, error: Exception, error_type: ErrorType,
                            request_id: str = None, context: Dict[str, Any] = None,
                            user_message: str = None, processing_time: float = None):
        """Create Flask response with error handling"""
        response_data, status_code = self.handle_error(
            error, error_type, request_id, context, user_message
        )
        
        # Add processing time if provided
        if processing_time is not None:
            response_data['processing_time'] = round(processing_time, 2)
        
        # Create Flask response
        response = jsonify(response_data)
        
        # Add security headers
        headers = security_validator.get_security_headers()
        for header, value in headers.items():
            response.headers[header] = value
        
        # Add error-specific headers
        if error_type == ErrorType.RATE_LIMIT_ERROR:
            response.headers['Retry-After'] = str(self._get_retry_delay(error_type))
        
        response.status_code = status_code
        return response
    
    def handle_database_error(self, error: Exception, operation: str, 
                            request_id: str = None) -> Tuple[Dict, int]:
        """Handle database-specific errors"""
        context = {'operation': operation}
        
        # Check for specific database errors
        error_msg = str(error).lower()
        
        if 'locked' in error_msg or 'busy' in error_msg:
            return self.handle_error(
                error, ErrorType.DATABASE_ERROR, request_id, context,
                "Database temporarily busy, please try again"
            )
        elif 'disk' in error_msg or 'space' in error_msg:
            return self.handle_error(
                error, ErrorType.RESOURCE_ERROR, request_id, context,
                "Storage space temporarily unavailable"
            )
        elif 'corrupt' in error_msg:
            return self.handle_error(
                error, ErrorType.DATABASE_ERROR, request_id, context,
                "Data integrity issue detected"
            )
        else:
            return self.handle_error(
                error, ErrorType.DATABASE_ERROR, request_id, context,
                "Database operation failed"
            )
    
    def handle_api_error(self, error: Exception, api_name: str,
                        request_id: str = None) -> Tuple[Dict, int]:
        """Handle external API errors"""
        context = {'api_name': api_name}
        
        # Check for specific API errors
        error_msg = str(error).lower()
        
        if 'timeout' in error_msg:
            return self.handle_error(
                error, ErrorType.TIMEOUT_ERROR, request_id, context,
                f"{api_name} service timed out"
            )
        elif 'rate limit' in error_msg or '429' in error_msg:
            return self.handle_error(
                error, ErrorType.RATE_LIMIT_ERROR, request_id, context,
                f"{api_name} rate limit exceeded"
            )
        elif 'unauthorized' in error_msg or '401' in error_msg:
            return self.handle_error(
                error, ErrorType.AUTHENTICATION_ERROR, request_id, context,
                f"{api_name} authentication failed"
            )
        elif 'network' in error_msg or 'connection' in error_msg:
            return self.handle_error(
                error, ErrorType.NETWORK_ERROR, request_id, context,
                f"Network error connecting to {api_name}"
            )
        else:
            return self.handle_error(
                error, ErrorType.API_ERROR, request_id, context,
                f"{api_name} service temporarily unavailable"
            )
    
    def handle_processing_error(self, error: Exception, step: str,
                              request_id: str = None) -> Tuple[Dict, int]:
        """Handle processing-specific errors"""
        context = {'processing_step': step}
        
        # Check for specific processing errors
        error_msg = str(error).lower()
        
        if 'content too short' in error_msg or 'insufficient content' in error_msg:
            return self.handle_error(
                error, ErrorType.PROCESSING_ERROR, request_id, context,
                "Article content too short for analysis"
            )
        elif 'language not supported' in error_msg:
            return self.handle_error(
                error, ErrorType.PROCESSING_ERROR, request_id, context,
                "Article language not supported"
            )
        elif 'invalid format' in error_msg:
            return self.handle_error(
                error, ErrorType.PROCESSING_ERROR, request_id, context,
                "Article format not supported"
            )
        else:
            return self.handle_error(
                error, ErrorType.PROCESSING_ERROR, request_id, context,
                f"Processing failed at {step} step"
            )
    
    def _determine_severity(self, error_type: ErrorType, error: Exception) -> ErrorSeverity:
        """Determine error severity based on type and content"""
        if error_type in [ErrorType.INTERNAL_ERROR, ErrorType.DATABASE_ERROR]:
            return ErrorSeverity.CRITICAL
        elif error_type in [ErrorType.API_ERROR, ErrorType.NETWORK_ERROR]:
            return ErrorSeverity.HIGH
        elif error_type in [ErrorType.TIMEOUT_ERROR, ErrorType.PROCESSING_ERROR]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _log_error(self, error: Exception, error_type: ErrorType, severity: ErrorSeverity,
                  error_id: str, request_id: str = None, context: Dict[str, Any] = None):
        """Log error with appropriate level and details"""
        log_data = {
            'error_id': error_id,
            'error_type': error_type.value,
            'severity': severity.value,
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'request_id': request_id,
            'context': context or {}
        }
        
        # Include stack trace for high severity errors
        if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            log_data['stack_trace'] = traceback.format_exc()
        
        # Log with appropriate level
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"Critical error: {log_data}")
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(f"High severity error: {log_data}")
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"Medium severity error: {log_data}")
        else:
            self.logger.info(f"Low severity error: {log_data}")
        
        # Also log to performance logger if request_id available
        if request_id and performance_logger:
            performance_logger.log_step(
                request_id, f"error_{error_type.value}",
                error=f"{error.__class__.__name__}: {str(error)}"
            )
    
    def _is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        import os
        return os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    def _is_recoverable_error(self, error_type: ErrorType) -> bool:
        """Check if error is recoverable with retry"""
        recoverable_types = {
            ErrorType.TIMEOUT_ERROR,
            ErrorType.NETWORK_ERROR,
            ErrorType.API_ERROR,
            ErrorType.RATE_LIMIT_ERROR,
            ErrorType.DATABASE_ERROR
        }
        return error_type in recoverable_types
    
    def _get_retry_delay(self, error_type: ErrorType) -> int:
        """Get recommended retry delay in seconds"""
        retry_delays = {
            ErrorType.TIMEOUT_ERROR: 30,
            ErrorType.NETWORK_ERROR: 60,
            ErrorType.API_ERROR: 120,
            ErrorType.RATE_LIMIT_ERROR: 300,
            ErrorType.DATABASE_ERROR: 10
        }
        return retry_delays.get(error_type, 60)
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        # This would typically be implemented with persistent storage
        # For now, return basic info
        return {
            'error_types_supported': len(ErrorType),
            'severity_levels': len(ErrorSeverity),
            'recoverable_error_types': len([t for t in ErrorType if self._is_recoverable_error(t)])
        }

# Global error handler instance
error_handler = ErrorHandler()