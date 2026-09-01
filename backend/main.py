"""
AI News Verification System - FastAPI Main Application
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.config import settings
from backend.core.exceptions import NewsVerificationException, news_verification_exception_handler
from backend.db.database import init_db
from backend.api.routes.verification import router as verification_router
from backend.api.routes.health import router as health_router
from backend.api.routes.auth import router as auth_router
from backend.api.routes.history import router as history_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("news_verification.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    # Initialize database tables
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")

    logger.info(f"Groq API Key configured: {bool(settings.GROQ_API_KEY)}")
    logger.info(f"NewsAPI Key configured: {bool(settings.NEWS_API_KEY)}")
    logger.info(f"SerpAPI Key configured: {bool(settings.SERPAPI_KEY)}")
    logger.info(f"Qdrant URL: {settings.QDRANT_URL} (collection: {settings.QDRANT_COLLECTION})")
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


# Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    description=(
        "Production-grade evidence-based News Verification API.\n\n"
        "Features JWT Authentication, User Verification History, real-time news retrieval (NewsAPI & SerpAPI), "
        "FastEmbed semantic vector embeddings, Qdrant vector similarity search, and Groq LLMs for grounded claim verification."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
app.add_exception_handler(NewsVerificationException, news_verification_exception_handler)

# Include Routers
app.include_router(verification_router)
app.include_router(auth_router)
app.include_router(history_router)
app.include_router(health_router)

# Mount Frontend static files if available
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"message": f"{settings.APP_NAME} API is running. Visit /docs for Swagger UI."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
