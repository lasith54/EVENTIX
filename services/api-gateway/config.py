import os
from typing import Dict

class GatewayConfig:
    # Service URLs
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
    EVENT_SERVICE_URL = os.getenv("EVENT_SERVICE_URL", "http://event-service:8001")
    BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8002")
    PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8003")
    
    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", "b2b1b1925b5b4e0afccbce63ea4c447c")
    JWT_ALGORITHM = "HS256"
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    # Circuit Breaker
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))
    
    @classmethod
    def get_service_urls(cls) -> Dict[str, str]:
        return {
            "user": cls.USER_SERVICE_URL,
            "event": cls.EVENT_SERVICE_URL,
            "booking": cls.BOOKING_SERVICE_URL,
            "payment": cls.PAYMENT_SERVICE_URL
        }

config = GatewayConfig()