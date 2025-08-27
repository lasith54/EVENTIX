from fastapi import HTTPException
import time
from collections import defaultdict, deque
from typing import Dict
import asyncio
import httpx
from config import config

class RateLimiter:
    def __init__(self, max_requests: int = None, window_seconds: int = None):
        self.max_requests = max_requests or config.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or config.RATE_LIMIT_WINDOW
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests outside the window
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True
    
    def get_remaining_requests(self, client_ip: str) -> int:
        """Get remaining requests for a client"""
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove old requests
        while client_requests and client_requests[0] <= now - self.window_seconds:
            client_requests.popleft()
        
        return max(0, self.max_requests - len(client_requests))
    

class CircuitBreaker:
    def __init__(self, failure_threshold: int = None, timeout: int = None):
        self.failure_threshold = failure_threshold or config.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self.timeout = timeout or config.CIRCUIT_BREAKER_TIMEOUT
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        async def wrapper(*args, **kwargs):
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.timeout:
                    self.state = "HALF_OPEN"
                else:
                    raise HTTPException(
                        status_code=503, 
                        detail=f"Circuit breaker is OPEN. Service temporarily unavailable."
                    )
            
            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                
                raise e
        
        return wrapper
    
    def get_state(self) -> Dict[str, any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout": self.timeout
        }

# Global instances
rate_limiter = RateLimiter()
circuit_breakers = {
    "user": CircuitBreaker(),
    "event": CircuitBreaker(), 
    "booking": CircuitBreaker(),
    "payment": CircuitBreaker()
}