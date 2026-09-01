"""
Custom Exceptions and Exception Handlers for FastAPI Backend
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("news_verification.exceptions")


class NewsVerificationException(Exception):
    """Base exception for all news verification errors"""
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ArticleExtractionError(NewsVerificationException):
    """Raised when URL content cannot be scraped or parsed"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=422,
            details=details
        )


class LLMServiceError(NewsVerificationException):
    """Raised when Groq API call fails or malformed response returned"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class SearchProviderError(NewsVerificationException):
    """Raised when external search provider fails critically"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details
        )


class VectorDBError(NewsVerificationException):
    """Raised when Qdrant operation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


async def news_verification_exception_handler(request: Request, exc: NewsVerificationException):
    logger.error(f"NewsVerificationException on {request.url.path}: {exc.message} - details: {exc.details}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )
