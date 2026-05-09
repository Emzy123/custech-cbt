"""
FastAPI middleware for security, logging, and request handling.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import JSONResponse

from ..core.config import settings
from ..core.security import security
from ..core.redis import cache_manager
from ..services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit and monitoring."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            # Add headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate duration
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": process_time,
                    "error": str(e),
                    "client_ip": request.client.host if request.client else None,
                }
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": request_id
                }
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware to prevent abuse."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.cache = cache_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        client_id = security.generate_hmac_signature(f"{client_ip}:{user_agent}")
        
        # Rate limit key
        rate_limit_key = f"rate_limit:{client_id}"
        
        # Check current count
        current_count = await self.cache.get(rate_limit_key) or 0
        
        if current_count >= self.calls:
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={"client_ip": client_ip, "current_count": current_count}
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": self.period
                },
                headers={"Retry-After": str(self.period)}
            )
        
        # Increment counter
        await self.cache.increment(rate_limit_key)
        
        # Set expiration if this is the first request
        if current_count == 0:
            await self.cache.expire(rate_limit_key, self.period)
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - current_count - 1))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.period)
        
        return response


class SessionValidationMiddleware(BaseHTTPMiddleware):
    """Validate user sessions for security."""
    
    def __init__(self, app, exempt_paths: list = None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/static",
        ]
        self.cache = cache_manager
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with session validation."""
        # Skip validation for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get session token
        session_token = request.headers.get("X-Session-Token")
        if not session_token:
            session_token = request.cookies.get(settings.session_cookie_name)
        
        # For endpoints that don't require authentication, skip validation
        if request.url.path.startswith("/api/v1/public"):
            return await call_next(request)
        
        # Validate session if token is present
        if session_token:
            session_data = await self.cache.get(f"session:{session_token}")
            if not session_data:
                # Session expired or invalid
                logger.warning(
                    f"Invalid session token from {request.client.host if request.client else 'unknown'}",
                    extra={"session_token": session_token[:10] + "..."}
                )
                
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid or expired session"}
                )
            
            # Check device fingerprint
            device_fingerprint = security.generate_device_fingerprint(
                request.headers.get("User-Agent", ""),
                request.client.host if request.client else "unknown"
            )
            
            if session_data.get("device_fingerprint") != device_fingerprint:
                logger.warning(
                    f"Device fingerprint mismatch for session {session_token[:10]}..."
                )
                
                return JSONResponse(
                    status_code=401,
                    content={"error": "Device fingerprint mismatch"}
                )
        
        return await call_next(request)


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit logging middleware for security and compliance."""
    
    def __init__(self, app, audit_service: AuditService):
        super().__init__(app)
        self.audit_service = audit_service
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with audit logging."""
        # Skip audit for health checks and static content
        if request.url.path.startswith(("/health", "/static")):
            return await call_next(request)
        
        # Get user info if available
        user_id = getattr(request.state, "user_id", None)
        session_id = getattr(request.state, "session_id", None)
        
        # Record request start
        await self.audit_service.log_request_start(
            user_id=user_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            session_id=session_id
        )
        
        try:
            response = await call_next(request)
            
            # Log successful request
            await self.audit_service.log_request_end(
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                success=True,
                session_id=session_id
            )
            
            return response
            
        except HTTPException as e:
            # Log HTTP exception
            await self.audit_service.log_request_end(
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=e.status_code,
                success=False,
                error_message=str(e.detail),
                session_id=session_id
            )
            
            raise
            
        except Exception as e:
            # Log unexpected error
            await self.audit_service.log_request_end(
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=500,
                success=False,
                error_message=str(e),
                session_id=session_id
            )
            
            raise


def setup_cors_middleware(app):
    """Set up CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"],
    )


def setup_security_middleware(app, audit_service: AuditService):
    """Set up all security middleware."""
    # Add middleware in reverse order (last added runs first)
    app.add_middleware(
        AuditMiddleware,
        audit_service=audit_service
    )
    
    app.add_middleware(
        SessionValidationMiddleware,
        exempt_paths=[
            "/health",
            "/docs",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/static",
            "/favicon.ico",
        ]
    )
    
    app.add_middleware(
        RateLimitMiddleware,
        calls=settings.rate_limit_per_minute,
        period=60
    )
    
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
