import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import models
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated, Dict, Any
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, SessionLocal, Base
from admin import create_admin_user
import logging
from routes import (auth, preference_routes, notification_routes, session_routes)
import time
import asyncio

from shared.rabbitmq_client import rabbitmq_client
from shared.event_handler import BaseEventHandler

from config import settings

import logging
logger = logging.getLogger(__name__)

class UserServiceEventHandler(BaseEventHandler):
    def __init__(self):
        super().__init__("user-service")

    async def handle_user_event(self, event_type: str, event_data: Dict[str, Any]):
        logger.info(f"User service received user event: {event_type}")
        # User service doesn't typically handle its own events

    async def handle_event_event(self, event_type: str, event_data: Dict[str, Any]):
        if event_type == "created":
            logger.info(f"New event created: {event_data['data'].get('title', 'Unknown')}")
            # TODO: Send notifications to interested users

    async def handle_booking_event(self, event_type: str, event_data: Dict[str, Any]):
        if event_type == "created":
            user_id = event_data['data']['user_id']
            logger.info(f"Booking created for user {user_id}")
            # TODO: Send booking confirmation email
            
        elif event_type == "confirmed":
            user_id = event_data['data']['user_id']
            logger.info(f"Booking confirmed for user {user_id}")

    async def handle_payment_event(self, event_type: str, event_data: Dict[str, Any]):
        if event_type == "completed":
            user_id = event_data['data']['user_id']
            logger.info(f"Payment completed for user {user_id}")
            # TODO: Send payment receipt

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """

    models.Base.metadata.create_all(bind=engine)
    
    # Create a separate session for the startup task
    db = SessionLocal()
    try:
        create_admin_user(
            db,
            admin_email="admin@eventix.com",
            admin_password="admin",
            admin_first_name="Admin",
            admin_last_name="User"
        )
    finally:
        db.close()
    
    print("Application shutting down...")

    # Setup RabbitMQ
    try:
        await rabbitmq_client.connect()
        await rabbitmq_client.setup_exchanges_and_queues("user-service")
    

        # Start event handler
        event_handler = UserServiceEventHandler()
        asyncio.create_task(
            rabbitmq_client.start_consuming("user-service", event_handler.handle_event)
        )
        
        logger.info("User service started successfully")
    except Exception as e:
            logger.error(f"Error setting up RabbitMQ: {e}")
            return
    yield
    
    # Cleanup
    logger.info("Application shutting down...")
    try:
        await rabbitmq_client.disconnect()
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

app = FastAPI(
    title="User Service",
    description="User Management and Authentication Service",
    version="1.0.0",
    lifespan=lifespan
)

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

app.include_router(auth.router)
app.include_router(preference_routes.router)
app.include_router(notification_routes.router)
app.include_router(session_routes.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "user-service"}

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