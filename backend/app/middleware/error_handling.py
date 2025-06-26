"""Global error handling middleware and custom exceptions"""
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class CustomException(Exception):
    """Base custom exception"""
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(CustomException):
    """Input validation error"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, 400, {"field": field} if field else {})

class NotFoundError(CustomException):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, 404, {"resource": resource, "identifier": identifier})

class ServiceUnavailableError(CustomException):
    """External service unavailable error"""
    def __init__(self, service: str, message: Optional[str] = None):
        msg = f"{service} service unavailable"
        if message:
            msg += f": {message}"
        super().__init__(msg, 503, {"service": service})

class RateLimitError(CustomException):
    """Rate limit exceeded error"""
    def __init__(self, limit: int, window: int):
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window} seconds",
            429,
            {"limit": limit, "window": window}
        )

class AuthenticationError(CustomException):
    """Authentication failed error"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)

class AuthorizationError(CustomException):
    """Authorization failed error"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, 403)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except CustomException as e:
            logger.warning(f"Custom exception: {e.message}", extra={
                "status_code": e.status_code,
                "details": e.details,
                "path": request.url.path,
                "method": request.method
            })
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.message,
                    "details": e.details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path
                }
            )
        except HTTPException as e:
            # Let FastAPI handle its own HTTP exceptions
            raise e
        except Exception as e:
            # Log unexpected errors with full traceback
            logger.error(f"Unexpected error: {str(e)}", extra={
                "path": request.url.path,
                "method": request.method,
                "traceback": traceback.format_exc()
            })
            
            # Don't expose internal errors in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": request.url.path
                }
            )

def create_error_handler():
    """Create error handler for FastAPI exception handlers"""
    
    async def validation_exception_handler(request: Request, exc: Exception):
        """Handle validation errors"""
        logger.warning(f"Validation error: {str(exc)}", extra={
            "path": request.url.path,
            "method": request.method
        })
        
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation error",
                "details": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
                "path": request.url.path
            }
        )
    
    return validation_exception_handler
