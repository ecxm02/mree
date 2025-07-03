from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import os

from .config import settings
from .database import init_db
from .routers import auth, search, health, streaming, admin, tasks, images
from .middleware.rate_limiting import RateLimitMiddleware
from .middleware.error_handling import ErrorHandlingMiddleware, create_error_handler
from .middleware.metrics import PrometheusMiddleware, get_metrics_response

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
    
    logger.info("✅ Database initialized")
    
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

# Add metrics middleware if enabled (before rate limiting for accurate measurements)
if settings.METRICS_ENABLED:
    app.add_middleware(PrometheusMiddleware, redis_url=settings.REDIS_URL)

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

# Static file serving for music
app.mount("/music", StaticFiles(directory=settings.MUSIC_STORAGE_PATH), name="music")

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(streaming.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(images.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Music Streaming API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def simple_health():
    """Simple health check for Docker health checks"""
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.METRICS_ENABLED:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return get_metrics_response()
