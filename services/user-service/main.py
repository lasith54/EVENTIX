import sys
import os

import models
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from routes import (auth, preference_routes, notification_routes, session_routes)
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import DatabaseManager, CacheManager, create_all_tables
import time

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting User Service...")
    
    # Create database tables
    try:
        create_all_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise
    
    # Test connections
    db_healthy = DatabaseManager.health_check()
    cache_healthy = CacheManager.health_check()
    
    if not db_healthy:
        logger.error("❌ Database connection failed")
        raise Exception("Database connection failed")
    
    if not cache_healthy:
        logger.warning("⚠️ Cache connection failed - continuing without cache")
    
    logger.info("✅ User Service startup complete")
    yield
    logger.info("🛑 User Service shutdown")

# FastAPI application
app = FastAPI(
    title="EVENTIX User Service",
    description="User management and authentication service",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Service health check"""
    db_status = DatabaseManager.health_check()
    cache_status = CacheManager.health_check()
    
    return {
        "service": "user-service",
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "cache": "connected" if cache_status else "disconnected",
        "version": "2.0.0"
    }

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Service metrics for monitoring"""
    return {
        "service": "user-service",
        "metrics": {
            "active_users": 0,  # Implement actual metrics
            "total_sessions": 0,
            "database_connections": 0
        }
    }

# Database dependency
def get_db():
    """Get database session"""
    return DatabaseManager.get_db()

# Root endpoint
@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "EVENTIX User Service",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }
app.include_router(auth.router)
app.include_router(preference_routes.router)
app.include_router(notification_routes.router)
app.include_router(session_routes.router)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Incoming request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Request processed: {request.method} {request.url} - "
        f"Status: {response.status_code} - Time: {process_time:.4f}s"
    )
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)