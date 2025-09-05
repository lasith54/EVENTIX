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
from routes import booking_routes, saga_routes
import time
import asyncio

from shared.rabbitmq_client import rabbitmq_client
from event_handlers import BookingServiceEventHandler

import logging
logger = logging.getLogger(__name__)

event_handler = None

from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_handler

    # Setup RabbitMQ
    await rabbitmq_client.connect()
    event_handler = BookingServiceEventHandler()
    await event_handler.setup_handlers()
    
    # Start event handler
    asyncio.create_task(event_handler.start_consuming())
    
    logger.info("Booking service started successfully")
    
    yield
    
    # Cleanup
    await rabbitmq_client.disconnect()

app = FastAPI(
    title="Booking Service",
    description="Ticket Booking Service",
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
api_router.include_router(booking_routes.router)
api_router.include_router(saga_routes.router)
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
    return {"status": "healthy", "service": "booking-service"}

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
    uvicorn.run(app, host="0.0.0.0", port=8002)