"""Health check endpoints for monitoring service status"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import time
import psutil
import logging
from datetime import datetime, timedelta

from ..database import SessionLocal, engine
from ..services.elasticsearch_service import ElasticsearchService
from ..config import settings

router = APIRouter(prefix="/health", tags=["health"])
logger = logging.getLogger(__name__)

class HealthStatus(BaseModel):
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    version: str = "1.0.0"
    uptime_seconds: float
    checks: Dict[str, Any]

class ComponentHealth(BaseModel):
    status: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

# Track service start time
SERVICE_START_TIME = time.time()

async def check_database() -> ComponentHealth:
    """Check PostgreSQL database connectivity"""
    start_time = time.time()
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute("SELECT 1")
        db.close()
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            status="healthy",
            response_time_ms=response_time
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Database health check failed: {e}")
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )

async def check_elasticsearch() -> ComponentHealth:
    """Check Elasticsearch connectivity"""
    start_time = time.time()
    try:
        es_service = ElasticsearchService()
        await es_service.ensure_index_exists()
        
        # Test with a simple cluster health check
        if hasattr(es_service.es, 'cluster') and hasattr(es_service.es.cluster, 'health'):
            health = es_service.es.cluster.health()
            es_status = health.get('status', 'unknown')
        else:
            es_status = "available"
        
        response_time = (time.time() - start_time) * 1000
        
        status = "healthy" if es_status in ["green", "yellow", "available"] else "degraded"
        
        return ComponentHealth(
            status=status,
            response_time_ms=response_time,
            details={"cluster_status": es_status}
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Elasticsearch health check failed: {e}")
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )

async def check_redis() -> ComponentHealth:
    """Check Redis connectivity"""
    start_time = time.time()
    try:
        # Import redis here to avoid import errors if not available
        import redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        
        response_time = (time.time() - start_time) * 1000
        return ComponentHealth(
            status="healthy",
            response_time_ms=response_time
        )
    except ImportError:
        return ComponentHealth(
            status="unavailable",
            error="Redis client not installed"
        )
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error(f"Redis health check failed: {e}")
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )

def get_system_metrics() -> Dict[str, Any]:
    """Get basic system metrics"""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {"error": str(e)}

@router.get("/", response_model=HealthStatus)
async def health_check():
    """
    Comprehensive health check endpoint
    Returns overall service health and individual component status
    """
    start_time = time.time()
    
    # Check all components
    db_health = await check_database()
    es_health = await check_elasticsearch()
    redis_health = await check_redis()
    
    # Determine overall status
    component_statuses = [db_health.status, es_health.status, redis_health.status]
    
    if all(status == "healthy" for status in component_statuses):
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in component_statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    # Get system metrics
    system_metrics = get_system_metrics()
    
    uptime = time.time() - SERVICE_START_TIME
    
    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        checks={
            "database": db_health.dict(),
            "elasticsearch": es_health.dict(),
            "redis": redis_health.dict(),
            "system": system_metrics
        }
    )

@router.get("/live")
async def liveness_probe():
    """
    Simple liveness probe for Kubernetes/Docker
    Returns 200 if service is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}

@router.get("/ready")
async def readiness_probe():
    """
    Readiness probe - checks if service is ready to handle requests
    Returns 200 only if critical dependencies are healthy
    """
    # Check critical components only
    db_health = await check_database()
    
    if db_health.status == "unhealthy":
        raise HTTPException(
            status_code=503,
            detail="Service not ready - database unavailable"
        )
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow(),
        "database": db_health.status
    }
