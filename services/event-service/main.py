import sys
import os

import models
from fastapi import FastAPI, Request, status, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging
from routes import( events_routes, categories_routes, schedules_routes, pricing_routes, venue_routes,
                   utility_routes, seat_management_routes, seat_reservation_routes)
import time

# Add shared module to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../shared'))
from shared.database import DatabaseManager, CacheManager, create_all_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting Event Service...")
    
    try:
        create_all_tables()
        logger.info("✅ Database tables created/verified")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise
    
    db_healthy = DatabaseManager.health_check()
    cache_healthy = CacheManager.health_check()
    
    if not db_healthy:
        raise Exception("Database connection failed")
    
    logger.info("✅ Event Service startup complete")
    yield
    logger.info("🛑 Event Service shutdown")

app = FastAPI(
    title="EVENTIX Event Service",
    description="Event and venue management service",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Service health check"""
    db_status = DatabaseManager.health_check()
    cache_status = CacheManager.health_check()
    
    return {
        "service": "event-service",
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "cache": "connected" if cache_status else "disconnected",
        "version": "2.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Service metrics"""
    return {
        "service": "event-service",
        "metrics": {
            "total_events": 0,
            "active_events": 0,
            "total_venues": 0
        }
    }

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "EVENTIX Event Service",
        "version": "2.0.0",
        "status": "running"
    }

def get_db():
    return DatabaseManager.get_db()

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(events_routes.router)
api_router.include_router(categories_routes.router)
api_router.include_router(schedules_routes.router)
api_router.include_router(pricing_routes.router)
api_router.include_router(venue_routes.router)
api_router.include_router(seat_management_routes.router)
api_router.include_router(seat_reservation_routes.router)
api_router.include_router(utility_routes.router)
app.include_router(api_router)

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
    uvicorn.run(app, host="0.0.0.0", port=8001)