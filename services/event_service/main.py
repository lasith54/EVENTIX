import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import models
from fastapi import FastAPI, Request, status, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, SessionLocal
import logging
from routes import( events_routes, categories_routes, schedules_routes, pricing_routes, venue_routes,
                   utility_routes, seat_management_routes, seat_reservation_routes)
import time
import asyncio

from config import settings

# RabbitMQ imports
from shared.rabbitmq_client import rabbitmq_client
from event_handlers import EventServiceEventHandler

import logging
logger = logging.getLogger(__name__)

event_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_handler

    await rabbitmq_client.connect()
    event_handler = EventServiceEventHandler()
    await event_handler.setup_handlers()
    
    # Start event handler
    asyncio.create_task(event_handler.start_consuming())

    logger.info("Event service started successfully")
    
    yield
    
    # Cleanup
    await rabbitmq_client.disconnect()

app = FastAPI(
    title="Event Service",
    description="Event Management Service",
    version="1.0.0",
    lifespan=lifespan
)

models.Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "event-service"}

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