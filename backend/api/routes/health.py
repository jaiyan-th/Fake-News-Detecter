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
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/health/test-search", summary="Search Diagnostics")
async def test_search_diagnostics(
    q: str = "Vijay",
    newsapi_service: NewsAPIService = Depends(get_newsapi_service),
    serpapi_service: SerpAPIService = Depends(get_serpapi_service)
):
    import httpx, xml.etree.ElementTree as ET
    # Test Google News RSS directly
    rss_status = "unknown"
    rss_items_count = 0
    rss_error = None
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            r = await client.get(f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en", headers={"User-Agent": "Mozilla/5.0"})
            rss_status = r.status_code
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                rss_items_count = len(root.findall(".//item"))
    except Exception as e:
        rss_error = str(e)

    news_res = await newsapi_service.search([q])
    serp_res = await serpapi_service.search_google_news([q])
    return {
        "query": q,
        "direct_rss": {"status": rss_status, "count": rss_items_count, "error": rss_error},
        "newsapi": {"configured": newsapi_service.is_configured(), "count": len(news_res), "sample": [a["title"] for a in news_res[:2]]},
        "serpapi": {"configured": bool(serpapi_service.api_key), "count": len(serp_res), "sample": [a["title"] for a in serp_res[:2]]}
    }
