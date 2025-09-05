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
from event_handlers import UserServiceEventHandler

from config import settings

import logging
logger = logging.getLogger(__name__)

event_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_handler

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
    await rabbitmq_client.connect()
    event_handler = UserServiceEventHandler()
    await event_handler.setup_handlers()


    # Start event handler
    event_handler = UserServiceEventHandler()
    asyncio.create_task(event_handler.start_consuming())
    
    logger.info("User service started successfully")

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

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(preference_routes.router, prefix="/api/v1/preferences", tags=["Preferences"])
app.include_router(notification_routes.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(session_routes.router, prefix="/api/v1/sessions", tags=["Sessions"])

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