"""
Redis client wrapper for production-ready caching and job queuing.

Features:
- Connection pooling via redis-py async
- Health check method
- Automatic reconnection
- Environment-based configuration (REDIS_URL)
- Graceful fallback when Redis unavailable
"""

import os
import logging
from typing import Optional, Any
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[redis.Redis] = None
_connection_pool: Optional[ConnectionPool] = None


def is_production() -> bool:
    """Check if running in production mode."""
    env = os.getenv("ENV", "development").lower()
    return env == "production"


async def get_redis_client() -> Optional[redis.Redis]:
    """
    Get or create Redis client with connection pooling.

    In production mode, Redis is REQUIRED for proper rate limiting across instances.
    In development mode, Redis is optional and falls back to in-memory storage.

    Returns:
        Redis client instance or None if Redis is unavailable (development only)

    Raises:
        RuntimeError: In production if REDIS_URL is not configured
    """
    global _redis_client, _connection_pool

    if _redis_client is not None:
        return _redis_client

    redis_url = os.getenv("REDIS_URL")

    if not redis_url:
        if is_production():
            # In production, Redis is required for distributed rate limiting
            error_msg = (
                "CRITICAL: REDIS_URL not configured in production! "
                "Redis is required for rate limiting across multiple instances. "
                "Set REDIS_URL environment variable to connect to Redis."
            )
            logger.critical(error_msg)
            raise RuntimeError(error_msg)
        else:
            logger.warning("REDIS_URL not configured. Redis features will be disabled (development mode only).")
            return None

    try:
        # Create connection pool
        _connection_pool = ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )

        # Create Redis client with connection pool
        _redis_client = redis.Redis(connection_pool=_connection_pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established successfully")

        return _redis_client

    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_client = None
        _connection_pool = None
        return None


async def close_redis_connection():
    """Close Redis connection and cleanup."""
    global _redis_client, _connection_pool

    if _redis_client:
        try:
            await _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None

    if _connection_pool:
        try:
            await _connection_pool.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting Redis pool: {e}")
        finally:
            _connection_pool = None


async def redis_health_check() -> dict:
    """
    Check Redis connection health.

    Returns:
        Dict with status and details
    """
    client = await get_redis_client()

    if not client:
        return {
            "status": "unavailable",
            "message": "Redis not configured or connection failed"
        }

    try:
        # Test ping
        await client.ping()

        # Get basic info
        info = await client.info("server")

        return {
            "status": "healthy",
            "message": "Redis connected",
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis error: {str(e)}"
        }


class RedisCache:
    """
    High-level Redis cache wrapper with graceful fallback.

    Provides simple get/set operations that fail silently
    when Redis is unavailable (allows app to function without cache).
    """

    @staticmethod
    async def get(key: str) -> Optional[str]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/unavailable
        """
        try:
            client = await get_redis_client()
            if not client:
                return None
            return await client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed for key {key}: {e}")
            return None

    @staticmethod
    async def set(key: str, value: str, ttl_seconds: int = 3600) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (default: 1 hour)

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            if not client:
                return False
            await client.set(key, value, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key {key}: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            if not client:
                return False
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE failed for key {key}: {e}")
            return False

    @staticmethod
    async def exists(key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        try:
            client = await get_redis_client()
            if not client:
                return False
            return await client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Redis EXISTS failed for key {key}: {e}")
            return False

    @staticmethod
    async def incr(key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter in Redis.

        Args:
            key: Counter key
            amount: Amount to increment by

        Returns:
            New value or None if failed
        """
        try:
            client = await get_redis_client()
            if not client:
                return None
            return await client.incrby(key, amount)
        except Exception as e:
            logger.warning(f"Redis INCR failed for key {key}: {e}")
            return None

    @staticmethod
    async def expire(key: str, ttl_seconds: int) -> bool:
        """
        Set expiration on a key.

        Args:
            key: Cache key
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            client = await get_redis_client()
            if not client:
                return False
            return await client.expire(key, ttl_seconds)
        except Exception as e:
            logger.warning(f"Redis EXPIRE failed for key {key}: {e}")
            return False

    @staticmethod
    async def get_json(key: str) -> Optional[Any]:
        """
        Get JSON value from cache.

        Args:
            key: Cache key

        Returns:
            Parsed JSON value or None
        """
        import json
        try:
            value = await RedisCache.get(key)
            if value:
                return json.loads(value)
            return None
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in cache for key {key}")
            return None

    @staticmethod
    async def set_json(key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Set JSON value in cache.

        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl_seconds: Time-to-live in seconds

        Returns:
            True if successful, False otherwise
        """
        import json
        try:
            json_value = json.dumps(value)
            return await RedisCache.set(key, json_value, ttl_seconds)
        except (TypeError, ValueError) as e:
            logger.warning(f"Failed to serialize value for key {key}: {e}")
            return False


# Export
__all__ = [
    'get_redis_client',
    'close_redis_connection',
    'redis_health_check',
    'RedisCache'
]
