"""
Login attempt limiting service using Redis.

Provides protection against brute-force login attacks by:
- Tracking failed login attempts per IP + email combination
- Blocking after 5 failed attempts
- 15-minute lockout period
- Returning remaining attempts to inform users
"""

import logging
from typing import Tuple, Optional
from fastapi import HTTPException, status
from .redis_client import RedisCache

logger = logging.getLogger(__name__)

# Configuration
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 900  # 15 minutes
KEY_PREFIX = "login_attempts"


class LoginLimiter:
    """
    Redis-based login attempt limiter.

    Key format: login_attempts:{ip}:{email}
    Value: number of failed attempts

    Fails closed if Redis is unavailable (denies login with 503) to prevent
    brute-force attacks during a Redis outage.
    """

    @staticmethod
    def _get_key(ip: str, email: str) -> str:
        """Generate Redis key for login attempts."""
        # Normalize email to lowercase
        email_normalized = email.lower().strip()
        return f"{KEY_PREFIX}:{ip}:{email_normalized}"

    @staticmethod
    async def check_rate_limit(ip: str, email: str) -> Tuple[bool, int]:
        """
        Check if login is allowed for this IP + email.

        Args:
            ip: Client IP address
            email: Email attempting to login

        Returns:
            Tuple of (is_allowed, remaining_attempts)

        Raises:
            HTTPException 503 if Redis is unavailable (fail-closed to prevent
            brute-force attacks during a Redis outage).
        """
        key = LoginLimiter._get_key(ip, email)

        try:
            # Get current attempts
            attempts_str = await RedisCache.get(key)

            if attempts_str is None:
                # No previous attempts
                return True, MAX_ATTEMPTS

            attempts = int(attempts_str)

            if attempts >= MAX_ATTEMPTS:
                # Account is locked
                return False, 0

            remaining = MAX_ATTEMPTS - attempts
            return True, remaining

        except Exception as e:
            logger.error(f"Login limiter check failed — Redis unavailable, denying login: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Login service temporarily unavailable. Please try again shortly.",
            )

    @staticmethod
    async def record_failed_attempt(ip: str, email: str) -> Tuple[bool, int]:
        """
        Record a failed login attempt.

        Args:
            ip: Client IP address
            email: Email that failed login

        Returns:
            Tuple of (is_locked, remaining_attempts)
        """
        key = LoginLimiter._get_key(ip, email)

        try:
            # Increment attempts
            new_count = await RedisCache.incr(key)

            if new_count is None:
                # Redis unavailable, can't track
                return False, MAX_ATTEMPTS - 1

            # Set/refresh expiration
            await RedisCache.expire(key, LOCKOUT_SECONDS)

            if new_count >= MAX_ATTEMPTS:
                logger.warning(f"Account locked: {email} from {ip} after {new_count} failed attempts")
                return True, 0

            remaining = MAX_ATTEMPTS - new_count
            logger.info(f"Failed login attempt for {email} from {ip} - {remaining} attempts remaining")
            return False, remaining

        except Exception as e:
            logger.warning(f"Login limiter record failed: {e}")
            return False, MAX_ATTEMPTS - 1

    @staticmethod
    async def clear_attempts(ip: str, email: str) -> bool:
        """
        Clear login attempts after successful login.

        Args:
            ip: Client IP address
            email: Email that logged in successfully

        Returns:
            True if cleared, False otherwise
        """
        key = LoginLimiter._get_key(ip, email)

        try:
            await RedisCache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Failed to clear login attempts: {e}")
            return False

    @staticmethod
    async def get_lockout_remaining(ip: str, email: str) -> Optional[int]:
        """
        Get remaining lockout time in seconds.

        Args:
            ip: Client IP address
            email: Email to check

        Returns:
            Remaining seconds or None if not locked/Redis unavailable
        """
        from .redis_client import get_redis_client

        key = LoginLimiter._get_key(ip, email)

        try:
            client = await get_redis_client()
            if not client:
                return None

            # Check if key exists and get TTL
            ttl = await client.ttl(key)

            if ttl <= 0:
                return None

            # Check if actually locked
            attempts_str = await RedisCache.get(key)
            if attempts_str and int(attempts_str) >= MAX_ATTEMPTS:
                return ttl

            return None

        except Exception as e:
            logger.warning(f"Failed to get lockout remaining: {e}")
            return None


# Export
__all__ = ['LoginLimiter', 'MAX_ATTEMPTS', 'LOCKOUT_SECONDS']
