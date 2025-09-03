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
from shared.event_handler import BaseEventHandler
from event_handlers.user_event_handler import BookingServiceUserHandler
from event_handlers.payment_event_handler import BookingServicePaymentHandler

import logging
logger = logging.getLogger(__name__)

from config import settings

class BookingServiceEventHandler(BaseEventHandler):
    def __init__(self):
        super().__init__("booking-service")
        self.user_handler = BookingServiceUserHandler()
        self.payment_handler = BookingServicePaymentHandler()

    async def handle_user_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle user service events"""
        try:
            await self.user_handler.handle_user_event({
                "event_type": event_type,
                "data": event_data.get("data", {})
            })
        except Exception as e:
            logger.error(f"Error handling user event {event_type}: {str(e)}")

    async def handle_event_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle event service events"""
        if event_type == "created":
            event_id = event_data['data']['event_id']
            logger.info(f"Cache event details for booking: {event_id}")
        elif event_type == "seat_inventory_updated":
            event_id = event_data['data']['event_id']
            logger.info(f"Event {event_id} inventory updated")

    async def handle_booking_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle internal booking events"""
        logger.info(f"Booking service received booking event: {event_type}")

    async def handle_payment_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle payment service events"""
        try:
            await self.payment_handler.handle_payment_event({
                "event_type": event_type,
                "data": event_data.get("data", {})
            })
        except Exception as e:
            logger.error(f"Error handling payment event {event_type}: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup RabbitMQ
    await rabbitmq_client.connect()
    await rabbitmq_client.setup_exchanges_and_queues("booking-service")
    
    # Start event handler
    event_handler = BookingServiceEventHandler()
    asyncio.create_task(
        rabbitmq_client.start_consuming("booking-service", event_handler.handle_event)
    )
    
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
app.include_router(booking_routes.router)
app.include_router(saga_routes.router)
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