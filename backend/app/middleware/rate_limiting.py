"""
Rate limiting middleware using token bucket algorithm.

Provides protection against API abuse on expensive endpoints:
- OCR processing
- AI text generation
- Document generation
- Batch operations

Benefits:
- Prevents resource exhaustion
- Fair usage across users
- Configurable per-endpoint limits
- Automatic cleanup of old buckets
"""

import time
import logging
from typing import Dict, Optional, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.

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


class RateLimiter:
    """
    Manages rate limits for different endpoints and clients.
    """

    def __init__(self):
        # Client buckets: {client_id: {endpoint: TokenBucket}}
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)

        # Endpoint configurations: {endpoint: (capacity, refill_rate)}
        self.endpoint_configs: Dict[str, Tuple[int, float]] = {}

        # Last cleanup time
        self.last_cleanup = datetime.now()

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

    def check_rate_limit(self, client_id: str, endpoint: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be allowed.

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
        Remove old buckets to prevent memory leak.

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
    """

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address or user ID from auth)
        client_ip = request.client.host if request.client else "unknown"

        # Try to get user ID from request state (if authenticated)
        client_id = getattr(request.state, "user_id", client_ip)

        # Get endpoint path
        endpoint = request.url.path

        # Check rate limit
        is_allowed, retry_after = rate_limiter.check_rate_limit(str(client_id), endpoint)

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
    # OCR endpoints (expensive, limit strictly)
    rate_limiter.configure_endpoint("/api/ocr/extract", requests_per_minute=10)

    # AI generation endpoints (expensive)
    rate_limiter.configure_endpoint("/api/building/generate-description", requests_per_minute=20)
    rate_limiter.configure_endpoint("/api/land/generate-description", requests_per_minute=20)
    rate_limiter.configure_endpoint("/api/locality/generate-narrative", requests_per_minute=20)

    # Document generation (resource intensive)
    rate_limiter.configure_endpoint("/api/reports", requests_per_minute=30)  # Prefix match for all report operations
    rate_limiter.configure_endpoint("/api/submit-and-generate", requests_per_minute=5)

    # Maps API endpoints (has external quota)
    rate_limiter.configure_endpoint("/api/maps/geocode", requests_per_minute=60)
    rate_limiter.configure_endpoint("/api/maps/directions", requests_per_minute=60)
    rate_limiter.configure_endpoint("/api/maps/static-map", requests_per_minute=60)

    logger.info("✓ Rate limits configured for all endpoints")


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
