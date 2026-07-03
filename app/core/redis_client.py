import redis.asyncio as redis
from typing import Optional, Any
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client wrapper"""
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    async def get_instance(cls) -> redis.Redis:
        """Get or create Redis instance"""
        if cls._instance is None:
            try:
                cls._instance = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf8",
                    decode_responses=True,
                    retry_on_timeout=True
                )
                # Test connection
                await cls._instance.ping()
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._instance
    
    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None


async def get_redis() -> redis.Redis:
    """Get Redis instance dependency"""
    return await RedisClient.get_instance()


class RedisService:
    """Redis service for caching and sessions"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Set key-value pair"""
        try:
            if expire:
                await self.redis.setex(key, expire, str(value))
            else:
                await self.redis.set(key, str(value))
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return await self.redis.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            return await self.redis.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return 0
    
    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to set"""
        try:
            await self.redis.sadd(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SADD error: {e}")
            return False
    
    async def remove_from_set(self, key: str, value: str) -> bool:
        """Remove value from set"""
        try:
            await self.redis.srem(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis SREM error: {e}")
            return False
    
    async def is_in_set(self, key: str, value: str) -> bool:
        """Check if value in set"""
        try:
            return await self.redis.sismember(key, value)
        except Exception as e:
            logger.error(f"Redis SISMEMBER error: {e}")
            return False
    
    async def add_to_blacklist(self, token: str, expire: int) -> bool:
        """Add token to blacklist"""
        key = f"token_blacklist:{token}"
        return await self.set(key, "1", expire)
    
    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        key = f"token_blacklist:{token}"
        return await self.exists(key)
    
    async def set_rate_limit(self, key: str, max_requests: int, period: int) -> bool:
        """Set rate limit"""
        current = await self.increment(key)
        if current == 1:
            await self.redis.expire(key, period)
        return current <= max_requests
    
    async def get_rate_limit_remaining(self, key: str) -> int:
        """Get remaining requests for rate limit"""
        value = await self.get(key)
        return int(value) if value else 0
