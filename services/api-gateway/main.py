from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging
from typing import Optional
import jwt
from datetime import datetime
import asyncio

# Import your config and middleware
from config import config
from middleware import rate_limiter, circuit_breakers, RateLimiter, CircuitBreaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Eventix API Gateway",
    description="Central API Gateway for Eventix Microservices",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware using config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get service URLs from config
SERVICES = config.get_service_urls()

class ServiceClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def forward_request(
        self, 
        service_url: str, 
        path: str, 
        method: str, 
        headers: dict = None,
        params: dict = None,
        json_data: dict = None,
        form_data: dict = None
    ):
        """Forward request to the appropriate microservice"""
        try:
            url = f"{service_url}{path}"
            
            # Remove host header to avoid conflicts
            if headers:
                headers = {k: v for k, v in headers.items() if k.lower() != "host"}
            
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                data=form_data
            )
            
            return response
            
        except httpx.RequestError as e:
            logger.error(f"Request to {service_url}{path} failed: {e}")
            raise HTTPException(
                status_code=503, 
                detail=f"Service temporarily unavailable: {str(e)}"
            )

service_client = ServiceClient()

# Authentication dependency
async def get_current_user(request: Request) -> Optional[dict]:
    """Extract user from JWT token if present"""
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Protected routes that require authentication
PROTECTED_ROUTES = {
    "/api/v1/auth/me",
    "/api/v1/auth/logout",
    "/api/v1/admin",
    "/api/v1/bookings",
    "/api/v1/payments",
    "/api/v1/users/profile"
}

# Admin routes that require admin role
ADMIN_ROUTES = {
    "/api/v1/admin",
    "/api/v1/events/admin"
}

def requires_auth(path: str) -> bool:
    """Check if path requires authentication"""
    return any(path.startswith(protected) for protected in PROTECTED_ROUTES)

def requires_admin(path: str) -> bool:
    """Check if path requires admin role"""
    return any(path.startswith(admin) for admin in ADMIN_ROUTES)

@app.middleware("http")
async def rate_limit_and_auth_middleware(request: Request, call_next):
    """Combined rate limiting and authentication middleware"""
    path = request.url.path
    client_ip = request.client.host
    
    # Skip middleware for health checks and docs
    if path in ["/health", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Rate limiting
    if not rate_limiter.is_allowed(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded. Max {config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW} seconds"
            }
        )
    
    # Authentication check
    if requires_auth(path):
        user = await get_current_user(request)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        # Check admin access
        if requires_admin(path):
            if user.get("role") not in ["admin", "organizer"]:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Admin access required"}
                )
    
    return await call_next(request)

# Health check
@app.get("/health")
async def health_check():
    """Gateway health check and service status"""
    service_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = await service_client.forward_request(
                service_url, "/health", "GET"
            )
            service_status[service_name] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
            }
        except Exception as e:
            service_status[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    return {
        "gateway": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": service_status,
        "config": {
            "rate_limit": f"{config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s",
            "circuit_breaker": f"threshold: {config.CIRCUIT_BREAKER_FAILURE_THRESHOLD}, timeout: {config.CIRCUIT_BREAKER_TIMEOUT}s"
        }
    }

# Route handlers with circuit breaker protection
@app.api_route("/api/v1/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/api/v1/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_proxy(request: Request, path: str):
    """Proxy requests to User Service with circuit breaker"""
    
    @circuit_breakers["user"].call
    async def call_user_service():
        service_path = f"/{path}"
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                pass
        
        response = await service_client.forward_request(
            SERVICES["user"],
            service_path,
            request.method,
            headers=dict(request.headers),
            params=dict(request.query_params),
            json_data=body
        )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else None,
            headers=dict(response.headers)
        )
    
    return await call_user_service()

@app.api_route("/api/v1/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def event_service_proxy(request: Request, path: str = ""):
    """Proxy requests to Event Service with circuit breaker"""
    
    @circuit_breakers["event"].call
    async def call_event_service():
        service_path = f"/{path}" if path else ""
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                pass
        
        response = await service_client.forward_request(
            SERVICES["event"],
            service_path,
            request.method,
            headers=dict(request.headers),
            params=dict(request.query_params),
            json_data=body
        )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else None,
            headers=dict(response.headers)
        )
    
    return await call_event_service()

@app.api_route("/api/v1/bookings/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def booking_service_proxy(request: Request, path: str = ""):
    """Proxy requests to Booking Service with circuit breaker"""
    
    @circuit_breakers["booking"].call
    async def call_booking_service():
        service_path = f"/{path}" if path else ""
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                pass
        
        response = await service_client.forward_request(
            SERVICES["booking"],
            service_path,
            request.method,
            headers=dict(request.headers),
            params=dict(request.query_params),
            json_data=body
        )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else None,
            headers=dict(response.headers)
        )
    
    return await call_booking_service()

@app.api_route("/api/v1/payments/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def payment_service_proxy(request: Request, path: str = ""):
    """Proxy requests to Payment Service with circuit breaker"""
    
    @circuit_breakers["payment"].call
    async def call_payment_service():
        service_path = f"/{path}" if path else ""
        
        # Get request body
        body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
            except:
                pass
        
        response = await service_client.forward_request(
            SERVICES["payment"],
            service_path,
            request.method,
            headers=dict(request.headers),
            params=dict(request.query_params),
            json_data=body
        )
        
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.content else None,
            headers=dict(response.headers)
        )
    
    return await call_payment_service()

# Configuration endpoint
@app.get("/api/v1/gateway/config")
async def gateway_config():
    """Get current gateway configuration"""
    return {
        "services": SERVICES,
        "rate_limiting": {
            "max_requests": config.RATE_LIMIT_REQUESTS,
            "window_seconds": config.RATE_LIMIT_WINDOW
        },
        "circuit_breaker": {
            "failure_threshold": config.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            "timeout_seconds": config.CIRCUIT_BREAKER_TIMEOUT
        },
        "cors": {
            "allowed_origins": config.ALLOWED_ORIGINS
        }
    }

# API Documentation aggregation
@app.get("/api/v1/services")
async def list_services():
    """List all available services and their endpoints"""
    return {
        "services": {
            "user": {
                "url": SERVICES["user"],
                "endpoints": [
                    "POST /api/v1/auth/register",
                    "POST /api/v1/auth/login", 
                    "GET /api/v1/auth/me",
                    "GET /api/v1/users/profile"
                ]
            },
            "event": {
                "url": SERVICES["event"],
                "endpoints": [
                    "GET /api/v1/events",
                    "GET /api/v1/events/{id}",
                    "POST /api/v1/events/admin",
                    "PUT /api/v1/events/admin/{id}"
                ]
            },
            "booking": {
                "url": SERVICES["booking"], 
                "endpoints": [
                    "POST /api/v1/bookings",
                    "GET /api/v1/bookings/{id}",
                    "PUT /api/v1/bookings/{id}/confirm",
                    "DELETE /api/v1/bookings/{id}"
                ]
            },
            "payment": {
                "url": SERVICES["payment"],
                "endpoints": [
                    "POST /api/v1/payments",
                    "GET /api/v1/payments/{id}",
                    "POST /api/v1/payments/{id}/refund"
                ]
            }
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)