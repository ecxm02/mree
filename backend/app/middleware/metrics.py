"""Prometheus metrics middleware for monitoring"""
import time
import logging
from typing import Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import redis

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections_total',
    'Active connections'
)

DOWNLOAD_QUEUE_SIZE = Gauge(
    'download_queue_size',
    'Number of songs in download queue'
)

ELASTICSEARCH_SONGS = Gauge(
    'elasticsearch_songs_total',
    'Total songs in Elasticsearch'
)

USER_COUNT = Gauge(
    'users_total',
    'Total registered users'
)

STORAGE_USED_BYTES = Gauge(
    'storage_used_bytes',
    'Storage space used in bytes',
    ['storage_type']
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""
    
    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis for metrics")
            except Exception as e:
                logger.warning(f"Redis not available for metrics: {e}")
    
    async def dispatch(self, request: Request, call_next):
        # Skip metrics collection for metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract endpoint (remove query params)
            endpoint = request.url.path
            method = request.method
            status_code = response.status_code
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Record error metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            raise
        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()

def update_background_metrics():
    """Update metrics that require database/service queries"""
    try:
        from ..database import SessionLocal
        from ..models.user import User
        from ..services.elasticsearch_service import ElasticsearchService
        import os
        from pathlib import Path
        from ..config import settings
        
        # Skip if metrics disabled
        if not settings.METRICS_ENABLED:
            return
        
        # Update user count
        try:
            db = SessionLocal()
            user_count = db.query(User).count()
            USER_COUNT.set(user_count)
            db.close()
        except Exception as e:
            logger.error(f"Failed to update user count metric: {e}")
        
        # Update Elasticsearch song count
        try:
            es_service = ElasticsearchService()
            song_count = es_service.get_total_songs()
            ELASTICSEARCH_SONGS.set(song_count)
        except Exception as e:
            logger.error(f"Failed to update Elasticsearch song count: {e}")
        
        # Update storage metrics
        for storage_type, path in [
            ("music", settings.MUSIC_STORAGE_PATH),
            ("images", settings.IMAGE_STORAGE_PATH),
            ("downloads", settings.MUSIC_DOWNLOAD_PATH)
        ]:
            try:
                if os.path.exists(path):
                    total_size = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(path)
                        for filename in filenames
                    )
                    STORAGE_USED_BYTES.labels(storage_type=storage_type).set(total_size)
            except Exception as e:
                logger.error(f"Failed to update storage metric for {storage_type}: {e}")
                
    except Exception as e:
        logger.error(f"Failed to update background metrics: {e}")

def get_metrics_response() -> Response:
    """Get Prometheus metrics response"""
    try:
        # Update background metrics before serving
        update_background_metrics()
        
        # Generate metrics
        metrics_data = generate_latest()
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error(f"Failed to generate metrics: {e}")
        return Response(
            content="# Failed to generate metrics\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )
