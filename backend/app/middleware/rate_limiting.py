"""
Rate limiting middleware using token bucket algorithm with Redis storage.

Provides protection against API abuse on expensive endpoints:
- OCR processing
- AI text generation
- Document generation
- Batch operations

Benefits:
- Prevents resource exhaustion
- Fair usage across users
- Configurable per-endpoint limits
- Redis-based storage (persists across restarts, works across instances)
- Automatic expiration via Redis TTL
- Falls back to in-memory storage if Redis unavailable
"""

import time
import json
import logging
import hashlib
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

logger = logging.getLogger(__name__)

# Redis key prefix and TTL
REDIS_KEY_PREFIX = "ratelimit"
REDIS_BUCKET_TTL = 3600  # 1 hour - buckets expire if not used


class TokenBucket:
    """
    Token bucket algorithm for rate limiting (in-memory fallback).

    Tokens are added at a constant rate. Each request consumes one token.
    If no tokens available, request is rejected.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst limit)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient tokens
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill

        # Calculate tokens to add
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_retry_after(self) -> int:
        """
        Calculate seconds until next token available.

        Returns:
            Seconds to wait
        """
        if self.tokens >= 1:
            return 0

        tokens_needed = 1 - self.tokens
        return int(tokens_needed / self.refill_rate) + 1

    def to_dict(self) -> dict:
        """Serialize bucket state to dict for Redis storage."""
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "tokens": self.tokens,
            "last_refill": self.last_refill
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenBucket":
        """Deserialize bucket state from dict."""
        bucket = cls(data["capacity"], data["refill_rate"])
        bucket.tokens = data["tokens"]
        bucket.last_refill = data["last_refill"]
        return bucket


class RateLimiter:
    """
    Manages rate limits for different endpoints and clients.

    Uses Redis for storage when available, falls back to in-memory storage.
    """

    def __init__(self):
        # In-memory fallback buckets: {client_id: {endpoint: TokenBucket}}
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)

        # Endpoint configurations: {endpoint: (capacity, refill_rate)}
        self.endpoint_configs: Dict[str, Tuple[int, float]] = {}

        # Last cleanup time (for in-memory fallback)
        self.last_cleanup = datetime.now()

        # Track if Redis is available
        self._redis_available = None

    def configure_endpoint(self, endpoint: str, requests_per_minute: int):
        """
        Configure rate limit for an endpoint.

        Args:
            endpoint: Endpoint path pattern
            requests_per_minute: Maximum requests per minute
        """
        # Convert requests/minute to tokens/second
        capacity = requests_per_minute
        refill_rate = requests_per_minute / 60.0

        self.endpoint_configs[endpoint] = (capacity, refill_rate)
        logger.info(f"Rate limit configured: {endpoint} = {requests_per_minute} req/min")

    def _make_redis_key(self, client_id: str, endpoint: str) -> str:
        """
        Generate Redis key for rate limit bucket.

        Args:
            client_id: Client identifier
            endpoint: Endpoint path

        Returns:
            Redis key string
        """
        # Hash endpoint to avoid special characters in key
        endpoint_hash = hashlib.md5(endpoint.encode()).hexdigest()[:12]
        return f"{REDIS_KEY_PREFIX}:{client_id}:{endpoint_hash}"

    async def _get_redis_bucket(self, key: str, capacity: int, refill_rate: float) -> Optional[TokenBucket]:
        """
        Get bucket state from Redis.

        Args:
            key: Redis key
            capacity: Bucket capacity (for new buckets)
            refill_rate: Token refill rate (for new buckets)

        Returns:
            TokenBucket or None if Redis unavailable
        """
        try:
            from ..services.redis_client import RedisCache

            data = await RedisCache.get_json(key)

            if data:
                # Restore existing bucket
                bucket = TokenBucket.from_dict(data)
                # Update config in case it changed
                bucket.capacity = capacity
                bucket.refill_rate = refill_rate
                return bucket
            else:
                # Create new bucket
                return TokenBucket(capacity, refill_rate)

        except Exception as e:
            logger.debug(f"Redis bucket get failed: {e}")
            return None

    async def _set_redis_bucket(self, key: str, bucket: TokenBucket) -> bool:
        """
        Save bucket state to Redis.

        Args:
            key: Redis key
            bucket: TokenBucket to save

        Returns:
            True if saved successfully
        """
        try:
            from ..services.redis_client import RedisCache

            return await RedisCache.set_json(key, bucket.to_dict(), REDIS_BUCKET_TTL)

        except Exception as e:
            logger.debug(f"Redis bucket set failed: {e}")
            return False

    async def check_rate_limit_async(self, client_id: str, endpoint: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be allowed (async version with Redis).

        Args:
            client_id: Client identifier (IP or user ID)
            endpoint: Endpoint being accessed

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # Find matching endpoint configuration
        config = self._get_endpoint_config(endpoint)
        if not config:
            # No rate limit configured for this endpoint
            return True, None

        capacity, refill_rate = config

        # Try Redis first
        redis_key = self._make_redis_key(client_id, endpoint)
        bucket = await self._get_redis_bucket(redis_key, capacity, refill_rate)

        if bucket:
            # Redis available - use Redis-backed bucket
            if bucket.consume():
                await self._set_redis_bucket(redis_key, bucket)
                return True, None
            else:
                retry_after = bucket.get_retry_after()
                await self._set_redis_bucket(redis_key, bucket)
                logger.warning(f"Rate limit exceeded: {client_id} on {endpoint} (retry after {retry_after}s)")
                return False, retry_after
        else:
            # Fall back to in-memory
            return self.check_rate_limit(client_id, endpoint)

    def check_rate_limit(self, client_id: str, endpoint: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be allowed (sync in-memory version).

        Args:
            client_id: Client identifier (IP or user ID)
            endpoint: Endpoint being accessed

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # Find matching endpoint configuration
        config = self._get_endpoint_config(endpoint)
        if not config:
            # No rate limit configured for this endpoint
            return True, None

        capacity, refill_rate = config

        # Get or create bucket for this client+endpoint
        if endpoint not in self.buckets[client_id]:
            self.buckets[client_id][endpoint] = TokenBucket(capacity, refill_rate)

        bucket = self.buckets[client_id][endpoint]

        # Try to consume token
        if bucket.consume():
            return True, None
        else:
            retry_after = bucket.get_retry_after()
            logger.warning(f"Rate limit exceeded: {client_id} on {endpoint} (retry after {retry_after}s)")
            return False, retry_after

    def _get_endpoint_config(self, endpoint: str) -> Optional[Tuple[int, float]]:
        """
        Get configuration for endpoint (supports pattern matching).

        Args:
            endpoint: Endpoint path

        Returns:
            Configuration tuple or None
        """
        # Exact match
        if endpoint in self.endpoint_configs:
            return self.endpoint_configs[endpoint]

        # Pattern match (simple prefix matching)
        for pattern, config in self.endpoint_configs.items():
            if endpoint.startswith(pattern):
                return config

        return None

    def cleanup_old_buckets(self, max_age_minutes: int = 60):
        """
        Remove old in-memory buckets to prevent memory leak.
        (Redis buckets auto-expire via TTL)

        Args:
            max_age_minutes: Age threshold for cleanup
        """
        now = datetime.now()

        # Only cleanup once per hour
        if (now - self.last_cleanup) < timedelta(hours=1):
            return

        # Clean up buckets that haven't been used
        clients_to_remove = []
        endpoints_to_remove = []

        for client_id, endpoints in self.buckets.items():
            # Remove endpoints that are full (haven't been used in a while)
            for endpoint, bucket in endpoints.items():
                if bucket.tokens >= bucket.capacity:
                    endpoints_to_remove.append(endpoint)

            for endpoint in endpoints_to_remove:
                del endpoints[endpoint]

            # Remove client if no endpoints left
            if not endpoints:
                clients_to_remove.append(client_id)

        for client_id in clients_to_remove:
            del self.buckets[client_id]

        if clients_to_remove or endpoints_to_remove:
            logger.info(f"Rate limiter cleanup: removed {len(clients_to_remove)} clients")

        self.last_cleanup = now


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to requests.

    Uses Redis for distributed rate limiting when available,
    falls back to in-memory storage otherwise.
    """

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address or user ID from auth)
        client_ip = request.client.host if request.client else "unknown"

        # Try to get user ID from request state (if authenticated)
        client_id = getattr(request.state, "user_id", client_ip)

        # Get endpoint path
        endpoint = request.url.path

        # Check rate limit using async Redis-backed method
        is_allowed, retry_after = await rate_limiter.check_rate_limit_async(str(client_id), endpoint)

        if not is_allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "status": "error",
                    "error": "TooManyRequests",
                    "message": f"Rate limit exceeded. Please wait {retry_after} seconds and try again.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": "See endpoint configuration",
                    "X-RateLimit-Remaining": "0"
                }
            )

        # Process request
        response = await call_next(request)

        return response


# ===== CONFIGURATION HELPER =====

def configure_rate_limits():
    """
    Configure rate limits for all endpoints.

    Called during application startup.
    """
    # ===== SECURITY-CRITICAL: Authentication Endpoints =====
    # Password reset - strict limits to prevent brute force
    rate_limiter.configure_endpoint("/api/auth/reset-password", requests_per_minute=5)  # 5 attempts per minute
    rate_limiter.configure_endpoint("/api/auth/forgot-password", requests_per_minute=3)  # 3 per minute per IP
    rate_limiter.configure_endpoint("/api/auth/login", requests_per_minute=10)  # 10 login attempts per minute
    rate_limiter.configure_endpoint("/api/auth/register", requests_per_minute=5)  # 5 registrations per minute

    # ===== OCR endpoints (expensive, limit strictly) =====
    rate_limiter.configure_endpoint("/api/ocr/extract", requests_per_minute=10)

    # ===== AI generation endpoints (expensive) =====
    rate_limiter.configure_endpoint("/api/building/generate-description", requests_per_minute=20)
    rate_limiter.configure_endpoint("/api/land/generate-description", requests_per_minute=20)
    rate_limiter.configure_endpoint("/api/locality/generate-narrative", requests_per_minute=20)

    # ===== Document generation (resource intensive) =====
    rate_limiter.configure_endpoint("/api/reports", requests_per_minute=30)  # Prefix match for all report operations
    rate_limiter.configure_endpoint("/api/submit-and-generate", requests_per_minute=5)

    # ===== Maps API endpoints (has external quota) =====
    rate_limiter.configure_endpoint("/api/maps/geocode", requests_per_minute=60)
    rate_limiter.configure_endpoint("/api/maps/directions", requests_per_minute=60)
    rate_limiter.configure_endpoint("/api/maps/static-map", requests_per_minute=60)

    logger.info("Rate limits configured for all endpoints")


# ===== PERIODIC CLEANUP TASK =====

async def cleanup_task():
    """
    Background task to periodically cleanup old buckets.
    """
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            rate_limiter.cleanup_old_buckets()
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")


# Export
__all__ = [
    'RateLimitMiddleware',
    'rate_limiter',
    'configure_rate_limits',
    'cleanup_task'
]
