"""
Health Check and Diagnostics Route Handler: GET /api/v1/health
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.schemas.health import HealthResponse
from backend.services.groq_service import GroqService
from backend.services.newsapi_service import NewsAPIService
from backend.services.serpapi_service import SerpAPIService
from backend.services.vector_service import VectorSearchService
from backend.api.deps import (
    get_groq_service, get_newsapi_service, get_serpapi_service, get_vector_service
)

router = APIRouter(prefix="/api/v1", tags=["Health & Diagnostics"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health and Diagnostics",
    description="Returns status of the FastAPI backend application and its core services (Groq, NewsAPI, SerpAPI, Vector Search Engine)."
)
async def check_system_health(
    groq_service: GroqService = Depends(get_groq_service),
    newsapi_service: NewsAPIService = Depends(get_newsapi_service),
    serpapi_service: SerpAPIService = Depends(get_serpapi_service),
    vector_service: VectorSearchService = Depends(get_vector_service)
) -> HealthResponse:
    groq_ok = groq_service.is_available()
    newsapi_ok = newsapi_service.is_configured()
    serpapi_ok = serpapi_service.is_configured()
    vector_ok = vector_service.is_available()

    overall_status = "healthy"
    if not groq_ok:
        overall_status = "degraded"

    dependencies = {
        "groq_llm": {
            "status": "operational" if groq_ok else "unconfigured_or_unavailable",
            "role": "Claim extraction, query generation, stance analysis, verdict synthesis"
        },
        "news_api": {
            "status": "operational" if newsapi_ok else "unconfigured",
            "role": "Real-time news retrieval"
        },
        "serp_api": {
            "status": "operational" if serpapi_ok else "unconfigured",
            "role": "Google News broad search"
        },
        "vector_search_engine": {
            "status": "operational" if vector_ok else "unavailable",
            "role": "In-memory semantic vector index & similarity retrieval"
        },
        "embedding_engine": {
            "status": "operational",
            "model": "BAAI/bge-small-en-v1.5",
            "dimension": 384
        }
    }

    return HealthResponse(
        status=overall_status,
        application="running",
        dependencies=dependencies,
        timestamp=datetime.now(timezone.utc)
    )
