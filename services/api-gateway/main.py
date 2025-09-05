# services/api-gateway/main.py

import os
import time
import hashlib
import logging
import asyncio
from typing import List, Optional, Dict
import httpx
import redis
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import jwt
from contextlib import asynccontextmanager
from dataclasses import dataclass

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "32890498303745r0u98u3498u3498u3498")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

# Service URLs with load balancing
SERVICE_URLS = {
    "user": [
        os.getenv("USER_SERVICE_URL", "http://user-service:8000"),
        # Add more instances for load balancing
    ],
    "event": [
        os.getenv("EVENT_SERVICE_URL", "http://event-service:8001"),
    ],
    "booking": [
        os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8002"),
    ],
    "payment": [
        os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8003"),
    ]
}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

@dataclass
class ServiceHealth:
    url: str
    is_healthy: bool
    response_time: float
    last_check: float

class LoadBalancer:
    """Round-robin load balancer with health checks"""
    
    def __init__(self):
        self.service_health: Dict[str, List[ServiceHealth]] = {}
        self.current_index: Dict[str, int] = {}
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize service health tracking"""
        for service_name, urls in SERVICE_URLS.items():
            self.service_health[service_name] = [
                ServiceHealth(url, True, 0.0, 0.0) for url in urls
            ]
            self.current_index[service_name] = 0
    
    async def get_healthy_service(self, service_name: str) -> Optional[str]:
        """Get next healthy service URL using round-robin"""
        if service_name not in self.service_health:
            return None
        
        services = self.service_health[service_name]
        healthy_services = [s for s in services if s.is_healthy]
        
        if not healthy_services:
            # Try to use any service if none are healthy
            logger.warning(f"No healthy {service_name} services available")
            return services[0].url if services else None
        
        # Round-robin selection
        current_idx = self.current_index[service_name]
        service = healthy_services[current_idx % len(healthy_services)]
        self.current_index[service_name] = (current_idx + 1) % len(healthy_services)
        
        return service.url
    
    async def health_check(self, service_name: str, service_health: ServiceHealth):
        """Perform health check on a service"""
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_health.url}/health")
                response_time = time.time() - start_time
                
                service_health.is_healthy = response.status_code == 200
                service_health.response_time = response_time
                service_health.last_check = time.time()
                
                if service_health.is_healthy:
                    logger.debug(f"{service_name} service healthy: {service_health.url}")
                else:
                    logger.warning(f"{service_name} service unhealthy: {service_health.url}")
                    
        except Exception as e:
            logger.error(f"Health check failed for {service_name} at {service_health.url}: {e}")
            service_health.is_healthy = False
            service_health.last_check = time.time()

# Global load balancer instance
load_balancer = LoadBalancer()

class RateLimiter:
    """Redis-based rate limiter"""
    
    @staticmethod
    async def is_allowed(client_ip: str, limit: int = RATE_LIMIT_PER_MINUTE) -> bool:
        """Check if request is within rate limit"""
        try:
            key = f"rate_limit:{client_ip}"
            current = redis_client.get(key)
            
            if current is None:
                redis_client.setex(key, 60, 1)
                return True
            
            if int(current) >= limit:
                return False
            
            redis_client.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow on error

class SecurityMiddleware:
    """Custom security middleware"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    @staticmethod
    async def validate_jwt(credentials: HTTPAuthorizationCredentials) -> dict:
        """Validate JWT token"""
        try:
            payload = jwt.decode(
                credentials.credentials,
                JWT_SECRET_KEY,
                algorithms=[JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

# Health check background task
async def health_check_background():
    """Background task for service health checks"""
    while True:
        try:
            tasks = []
            for service_name, services in load_balancer.service_health.items():
                for service_health in services:
                    tasks.append(load_balancer.health_check(service_name, service_health))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Health check background task error: {e}")
            await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Start background health checks
    health_task = asyncio.create_task(health_check_background())
    logger.info("API Gateway started with health monitoring")
    
    yield
    
    # Cleanup
    health_task.cancel()
    logger.info("API Gateway shutdown complete")

# FastAPI application
app = FastAPI(
    title="EVENTIX API Gateway",
    description="Scalable API Gateway with Load Balancing and Security",
    version="2.0.0",
    lifespan=lifespan
)

# Security middleware
security = HTTPBearer(auto_error=False)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Rate limiting
    client_ip = SecurityMiddleware.get_client_ip(request)
    if not await RateLimiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    # Process request
    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Log metrics
    try:
        redis_client.lpush(
            "api_metrics",
            f"{request.method}:{request.url.path}:{response.status_code}:{process_time:.3f}:{client_ip}"
        )
        redis_client.ltrim("api_metrics", 0, 9999)  # Keep last 10k metrics
    except Exception as e:
        logger.error(f"Metrics logging error: {e}")
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Gateway health check"""
    service_status = {}
    overall_healthy = True
    
    for service_name, services in load_balancer.service_health.items():
        healthy_count = sum(1 for s in services if s.is_healthy)
        total_count = len(services)
        service_status[service_name] = {
            "healthy_instances": healthy_count,
            "total_instances": total_count,
            "is_healthy": healthy_count > 0
        }
        if healthy_count == 0:
            overall_healthy = False
    
    # Check Redis
    redis_healthy = True
    try:
        redis_client.ping()
    except Exception:
        redis_healthy = False
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "services": service_status,
        "redis": "healthy" if redis_healthy else "unhealthy",
        "timestamp": time.time()
    }

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get API metrics"""
    try:
        metrics = redis_client.lrange("api_metrics", 0, 99)
        parsed_metrics = []
        
        for metric in metrics:
            parts = metric.split(":")
            if len(parts) >= 5:
                parsed_metrics.append({
                    "method": parts[0],
                    "path": parts[1],
                    "status_code": int(parts[2]),
                    "response_time": float(parts[3]),
                    "client_ip": parts[4]
                })
        
        return {"metrics": parsed_metrics}
    except Exception as e:
        logger.error(f"Metrics retrieval error: {e}")
        return {"metrics": []}

# Service proxy function
async def proxy_request(request: Request, service_name: str, path: str = ""):
    """Proxy request to appropriate service"""
    service_url = await load_balancer.get_healthy_service(service_name)
    
    if not service_url:
        raise HTTPException(
            status_code=503,
            detail=f"{service_name} service unavailable"
        )
    
    # Prepare request
    url = f"{service_url}{path}"
    headers = dict(request.headers)
    
    # Remove hop-by-hop headers
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if request.method == "GET":
                response = await client.get(url, headers=headers, params=request.query_params)
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            return JSONResponse(
                content=response.json() if response.content else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except Exception as e:
        logger.error(f"Proxy error for {service_name}: {e}")
        raise HTTPException(status_code=502, detail="Service error")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    return await SecurityMiddleware.validate_jwt(credentials)

# Route definitions
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_auth_routes(request: Request, path: str):
    """User authentication routes (public)"""
    return await proxy_request(request, "user", f"/api/v1/auth/{path}")

@app.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_routes(request: Request, path: str, user=Depends(get_current_user)):
    """User management routes (authenticated)"""
    return await proxy_request(request, "user", f"/api/v1/users/{path}")

@app.api_route("/api/v1/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def event_routes(request: Request, path: str):
    """Event routes (public for GET, authenticated for others)"""
    if request.method == "GET":
        return await proxy_request(request, "event", f"/api/v1/events/{path}")
    else:
        # Require authentication for non-GET requests
        credentials = await security(request)
        await SecurityMiddleware.validate_jwt(credentials)
        return await proxy_request(request, "event", f"/api/v1/events/{path}")

@app.api_route("/api/v1/bookings/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def booking_routes(request: Request, path: str, user=Depends(get_current_user)):
    """Booking routes (authenticated)"""
    return await proxy_request(request, "booking", f"/api/v1/bookings/{path}")

@app.api_route("/api/v1/payments/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def payment_routes(request: Request, path: str, user=Depends(get_current_user)):
    """Payment routes (authenticated)"""
    return await proxy_request(request, "payment", f"/api/v1/payments/{path}")

# Root endpoint
@app.get("/")
async def root():
    """API Gateway information"""
    return {
        "service": "EVENTIX API Gateway",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "auth": "/api/v1/auth/*",
            "users": "/api/v1/users/*",
            "events": "/api/v1/events/*",
            "bookings": "/api/v1/bookings/*",
            "payments": "/api/v1/payments/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info",
        access_log=True
    )