"""
Main FastAPI application entry point for CBT system.
"""

import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .core.config import settings
from .core.database import db_manager, init_db
from .core.redis import redis_manager
from .core.security import security
from .api.middleware import setup_cors_middleware, setup_security_middleware
from .services.audit_service import AuditService
from .api import auth, students, courses, examinations, questions, academics, users, exam_blueprint, security_hardening, biometric

# Configure logging
log_file_path = Path(settings.log_file)
log_file_path.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file_path),
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting CBT system...")
    
    try:
        # Initialize database
        logger.info("Initializing database connection...")
        await init_db()
        await db_manager.health_check()
        
        # Initialize Redis
        logger.info("Initializing Redis connection...")
        await redis_manager.connect()

        logger.info("CBT system started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start CBT system: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down CBT system...")
    
    try:
        # Close database connections
        await db_manager.close()
        
        # Close Redis connections
        await redis_manager.disconnect()
        
        logger.info("CBT system shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Computer-Based Testing System for CUSTECH",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None,
    lifespan=lifespan,
)

# Add CORS middleware
setup_cors_middleware(app)

# Security middleware must be registered at import time (not in lifespan).
_audit_service = AuditService()
setup_security_middleware(app, _audit_service)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """404 error handler."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "message": f"Endpoint {request.url.path} not found",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(405)
async def method_not_allowed_handler(request: Request, exc):
    """405 error handler."""
    return JSONResponse(
        status_code=405,
        content={
            "error": "Method not allowed",
            "message": f"Method {request.method} not allowed for {request.url.path}",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    """422 validation error handler."""
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "message": "Request validation failed",
            "details": exc.detail if hasattr(exc, 'detail') else str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database
        db_health = await db_manager.health_check()
        
        # Check Redis
        redis_health = await redis_manager.health_check()
        
        # Overall health
        overall_healthy = (
            db_health.get("status") == "healthy" and
            redis_health.get("status") == "healthy"
        )
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "database": db_health,
            "redis": redis_health,
            "timestamp": security.generate_hmac_signature(str(datetime.utcnow()))
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": settings.app_version,
            "environment": settings.environment
        }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.is_development else "Documentation not available in production"
    }


if settings.metrics_enabled:
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)





# Include API routers
# Core
app.include_router(auth.router, prefix=settings.api_v1_str)
app.include_router(users.router, prefix=settings.api_v1_str)
app.include_router(students.router, prefix=settings.api_v1_str)
app.include_router(courses.router, prefix=settings.api_v1_str)
app.include_router(academics.router, prefix=settings.api_v1_str)
app.include_router(examinations.router, prefix=settings.api_v1_str)

# Question bank
app.include_router(questions.router, prefix=settings.api_v1_str)

# Blueprint configuration
app.include_router(exam_blueprint.router, prefix=settings.api_v1_str)

# Security & biometric
app.include_router(security_hardening.router, prefix=settings.api_v1_str)
app.include_router(biometric.router, prefix=settings.api_v1_str)


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "cbt.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
        access_log=True,
    )
