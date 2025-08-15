import models
from fastapi import FastAPI, Request, status, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from database import engine, SessionLocal
from admin import create_admin_user
import logging
import auth
import time

from config import settings

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
    
    yield
    
    print("Application shutting down...")

app = FastAPI(lifespan=lifespan)

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