from datetime import datetime, timedelta, timezone
from typing import Optional
import time
import uuid
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import os
from . import crud, models
from .database import get_db
from .utils.password_utils import pwd_context, _FAKE_HASH, verify_password, get_password_hash, validate_password_strength

# Re-export so existing callers that do `from .auth import get_password_hash` keep working.
__all__ = [
    "verify_password", "get_password_hash", "validate_password_strength",
    "create_access_token", "create_refresh_token", "verify_refresh_token",
    "verify_token", "authenticate_user", "get_current_user", "require_admin",
    "security", "security_optional",
    "ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_MINUTES",
]

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
# Separate secret for refresh tokens — must be set independently (no fallback to SECRET_KEY)
REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY")
if not REFRESH_TOKEN_SECRET_KEY:
    raise ValueError("REFRESH_TOKEN_SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"

# Token lifetimes - reduced for security
# Access tokens are short-lived, refresh tokens allow getting new access tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes - short for security
REFRESH_TOKEN_EXPIRE_MINUTES = 240  # 4 hours - reduced from 8 hours, tokens are rotated on refresh

# Security scheme for JWT
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)  # Don't auto-raise 403, let us handle it

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with unique JTI for revocation support."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4())  # Unique token ID for revocation
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with unique JTI for revocation support.

    Uses REFRESH_TOKEN_SECRET_KEY for additional security isolation.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4())  # Unique token ID for revocation
    })
    encoded_jwt = jwt.encode(to_encode, REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Verify and decode a refresh token.

    Returns payload if valid, None otherwise.
    Also validates that this is a refresh token, not an access token.
    Uses REFRESH_TOKEN_SECRET_KEY for verification.
    """
    try:
        payload = jwt.decode(token, REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        # Ensure this is a refresh token
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT access token.

    Rejects tokens not explicitly typed as 'access' to prevent refresh tokens
    from being accepted where access tokens are expected.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate user with email and password.

    Runs bcrypt even when the user does not exist so that response time is
    identical regardless of whether the email is registered, preventing
    timing-based user enumeration attacks.
    """
    user = crud.get_user_by_email(db, email=email)
    if not user:
        # Equalise timing — discard the result
        pwd_context.verify(password, _FAKE_HASH)
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

from fastapi import Request, Cookie

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: Session = Depends(get_db)
) -> models.User:
    """Dependency to get the current authenticated user.

    Supports both:
    - HttpOnly cookie auth (preferred, XSS-safe)
    - Authorization header auth (backwards compatibility)

    Also checks if the token has been revoked (blacklisted).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try cookie first (more secure), then header (backwards compatibility)
    token = None
    if access_token_cookie:
        token = access_token_cookie
    elif credentials:
        token = credentials.credentials

    if not token:
        raise credentials_exception

    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    # Check if token has been revoked (if it has a JTI).
    # Redis is checked first to avoid a DB hit on every request; the DB is the
    # authoritative fallback when Redis is unavailable or the entry is not cached.
    jti = payload.get("jti")
    if jti:
        from .services.redis_client import get_redis_client
        redis_cache_key = f"token_blacklist:{jti}"
        redis_client = None

        try:
            redis_client = await get_redis_client()
            if redis_client and await redis_client.get(redis_cache_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except HTTPException:
            raise
        except Exception:
            pass  # Redis unavailable — fall through to DB check

        blacklisted = db.query(models.TokenBlacklist).filter(
            models.TokenBlacklist.jti == jti
        ).first()
        if blacklisted:
            # Populate the cache so future requests skip the DB
            try:
                if redis_client:
                    exp = payload.get("exp", 0)
                    ttl = max(1, int(exp) - int(time.time()))
                    await redis_client.setex(redis_cache_key, ttl, "1")
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user

async def require_admin(
    current_user: models.User = Depends(get_current_user)
) -> models.User:
    """
    Dependency to require admin role for an endpoint.

    Raises:
        HTTPException: 403 if user is not an admin
    """
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user