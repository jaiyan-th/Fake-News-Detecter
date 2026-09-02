"""
FastAPI Dependency Injection Provider
Initializes and provides singleton service instances, database sessions, and auth context.
"""

from functools import lru_cache
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.db.database import get_db_session
from backend.db.models import User
from backend.services.article_extractor import ArticleExtractor
from backend.services.groq_service import GroqService
from backend.services.claim_extractor import ClaimExtractor
from backend.services.query_generator import QueryGenerator
from backend.services.newsapi_service import NewsAPIService
from backend.services.serpapi_service import SerpAPIService
from backend.services.source_credibility import SourceCredibilityService
from backend.services.source_normalizer import SourceNormalizer
from backend.services.embedding_service import EmbeddingService
from backend.services.vector_service import VectorSearchService
from backend.services.evidence_analyzer import EvidenceAnalyzer
from backend.services.verdict_generator import VerdictGenerator
from backend.services.auth_service import AuthService
from backend.services.history_service import HistoryService
from backend.core.pipeline import VerificationPipeline

security_bearer = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Provide a database session per request"""
    yield from get_db_session()


@lru_cache()
def get_auth_service() -> AuthService:
    return AuthService()


@lru_cache()
def get_history_service() -> HistoryService:
    return HistoryService()


@lru_cache()
def get_groq_service() -> GroqService:
    return GroqService()


@lru_cache()
def get_article_extractor() -> ArticleExtractor:
    return ArticleExtractor()


@lru_cache()
def get_source_credibility_service() -> SourceCredibilityService:
    return SourceCredibilityService()


@lru_cache()
def get_source_normalizer() -> SourceNormalizer:
    return SourceNormalizer(get_source_credibility_service())


@lru_cache()
def get_newsapi_service() -> NewsAPIService:
    return NewsAPIService()


@lru_cache()
def get_serpapi_service() -> SerpAPIService:
    return SerpAPIService()


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@lru_cache()
def get_vector_service() -> VectorSearchService:
    return VectorSearchService(get_embedding_service())


@lru_cache()
def get_claim_extractor() -> ClaimExtractor:
    return ClaimExtractor(get_groq_service())


@lru_cache()
def get_query_generator() -> QueryGenerator:
    return QueryGenerator(get_groq_service())


@lru_cache()
def get_evidence_analyzer() -> EvidenceAnalyzer:
    return EvidenceAnalyzer(get_groq_service())


@lru_cache()
def get_verdict_generator() -> VerdictGenerator:
    return VerdictGenerator(get_groq_service())


@lru_cache()
def get_verification_pipeline() -> VerificationPipeline:
    return VerificationPipeline(
        article_extractor=get_article_extractor(),
        claim_extractor=get_claim_extractor(),
        query_generator=get_query_generator(),
        newsapi_service=get_newsapi_service(),
        serpapi_service=get_serpapi_service(),
        source_normalizer=get_source_normalizer(),
        vector_service=get_vector_service(),
        evidence_analyzer=get_evidence_analyzer(),
        verdict_generator=get_verdict_generator()
    )


def get_current_user(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Enforce authentication via Bearer JWT token"""
    if not auth_creds or not auth_creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = auth_service.decode_token(auth_creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or disabled.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def get_optional_current_user(
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Optional authentication for endpoints accessible anonymously"""
    if not auth_creds or not auth_creds.credentials:
        return None

    payload = auth_service.decode_token(auth_creds.credentials)
    if not payload or "sub" not in payload:
        return None

    try:
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        return user if (user and user.is_active) else None
    except Exception:
        return None
