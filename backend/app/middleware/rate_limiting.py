"""Redis-based rate limiting middleware"""
try:
    import redis
except ImportError:
    redis = None

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Dict, Optional, Union

from ..config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-based rate limiting middleware"""
    
    def __init__(self, app, redis_url: Optional[str] = None):
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = None
        
        if redis:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        else:
            logger.warning("Redis not available, rate limiting disabled")
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if Redis is unavailable
        if not self.redis_client:
            return await call_next(request)
        
        # Get rate limit config for endpoint
        endpoint = request.url.path
        rate_limit_config = self._get_rate_limit_config(endpoint)
        
        if not rate_limit_config:
            return await call_next(request)
        
        # Get client identifier (user_id if authenticated, IP otherwise)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_id, endpoint, rate_limit_config):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded: {rate_limit_config['requests']} requests per {rate_limit_config['window']} seconds",
                    "retry_after": rate_limit_config['window']
                }
            )
        
        return await call_next(request)
    
    def _get_rate_limit_config(self, endpoint: str) -> Optional[Dict]:
        """Get rate limit configuration for endpoint"""
        rate_limits = {
            "/api/v1/search": {"requests": 60, "window": 60},  # 60 requests per minute
            "/api/v1/download": {"requests": 10, "window": 60},  # 10 downloads per minute
            "/api/v1/auth/login": {"requests": 5, "window": 300},  # 5 login attempts per 5 minutes
            "/api/v1/auth/register": {"requests": 3, "window": 3600},  # 3 registrations per hour
        }
        
        for pattern, config in rate_limits.items():
            if endpoint.startswith(pattern):
                return config
        
        return None
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    def _check_rate_limit(self, client_id: str, endpoint: str, config: Dict) -> bool:
        """Check if request is within rate limit using sliding window"""
        if not self.redis_client:
            return True
            
        try:
            key = f"rate_limit:{client_id}:{endpoint}"
            current_time = int(time.time())
            window_start = current_time - config['window']
            
            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(key, config['window'])
            
            results = pipe.execute()
            current_requests = results[1]
            
            # Check if limit exceeded
            return current_requests < config['requests']
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Allow request if Redis fails
            return True
