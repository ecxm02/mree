from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import init_db
from .routers import auth, search, health
from .services.elasticsearch_service import ElasticsearchService
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.error_handling import ErrorHandlingMiddleware, create_error_handler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Music Streaming API...")
    await init_db()
    
    # Initialize Elasticsearch
    es_service = ElasticsearchService()
    await es_service.ensure_index_exists()
    
    logger.info("✅ Database and Elasticsearch initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Music Streaming API...")


app = FastAPI(
    title="Music Streaming API",
    description="Backend API for music streaming app with YouTube downloads and Spotify metadata",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add global error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# CORS middleware for Flutter app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else settings.CORS_ORIGINS,  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add custom exception handlers
app.add_exception_handler(RequestValidationError, create_error_handler())

# Static file serving for music and images
app.mount("/music", StaticFiles(directory=settings.MUSIC_STORAGE_PATH), name="music")
app.mount("/images", StaticFiles(directory=settings.IMAGE_STORAGE_PATH), name="images")

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(health.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Music Streaming API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    
    return {
        "status": "healthy",
        "timestamp": "2025-06-26T11:52:00Z"
    }
