from fastapi import Request, HTTPException, status
from functools import wraps
import time
import threading
from typing import Dict, Tuple
from collections import defaultdict
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Module-level thread-safe rate limiting state (fixed - no longer reinitializing)
_lock = threading.Lock()
_requests: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, 0.0))

class RateLimiter:
    """Rate limiter with Redis support"""
    
    def __init__(self, requests: int = 100, period: int = 60):
        self.requests = requests
        self.period = period
        self.redis_client = None
    
    async def __call__(self, request: Request) -> bool:
        """Check if request is allowed"""
        client_ip = request.client.host
        
        # Try Redis first
        if settings.REDIS_URL:
            try:
                from app.core.redis_client import get_redis
                self.redis_client = await get_redis()
                return await self._redis_check(client_ip, request.url.path)
            except Exception as e:
                logger.warning(f"Redis rate limit check failed: {e}. Falling back to in-memory.")
        
        # Fallback to in-memory rate limiting
        return self._in_memory_check(client_ip)
    
    async def _redis_check(self, client_ip: str, path: str) -> bool:
        """Redis-based rate limiting"""
        key = f"rate_limit:{client_ip}:{path}"
        
        try:
            current = await self.redis_client.get(key)
            
            if current is None:
                await self.redis_client.setex(key, self.period, 1)
                return True
            
            count = int(current)
            if count >= self.requests:
                return False
            
            await self.redis_client.incr(key)
            return True
        except Exception as e:
            logger.error(f"Redis error in rate limit: {e}")
            return False
    
    def _in_memory_check(self, client_ip: str) -> bool:
        """Thread-safe in-memory rate limiting (fallback)"""
        with _lock:
            count, first_request = _requests[client_ip]
            current_time = time.time()
            
            # If window expired, reset counter
            if current_time - first_request > self.period:
                _requests[client_ip] = (1, current_time)
                return True
            
            # Check limit
            if count >= self.requests:
                return False
            
            # Increment counter
            _requests[client_ip] = (count + 1, first_request)
            return True

def rate_limit(requests: int = 100, period: int = 60):
    """Rate limiting decorator"""
    limiter = RateLimiter(requests, period)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not await limiter(request):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(limiter.period)}
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator