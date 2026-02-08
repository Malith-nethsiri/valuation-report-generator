from datetime import datetime, timedelta
from typing import Optional
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
from . import crud, models
from .database import get_db

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
# Separate secret for refresh tokens - falls back to SECRET_KEY for backwards compatibility
REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY", SECRET_KEY)
ALGORITHM = "HS256"

# Token lifetimes - reduced for security
# Access tokens are short-lived, refresh tokens allow getting new access tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes - short for security
REFRESH_TOKEN_EXPIRE_MINUTES = 240  # 4 hours - reduced from 8 hours, tokens are rotated on refresh

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Common passwords list - prevents users from using well-known weak passwords
# These are commonly used in password spraying attacks and should be blocked
COMMON_PASSWORDS = frozenset([
    # Most common passwords worldwide
    "password", "123456", "12345678", "qwerty", "abc123",
    "monkey", "1234567", "letmein", "trustno1", "dragon",
    "baseball", "iloveyou", "master", "sunshine", "ashley",
    "football", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "password1", "password123", "welcome",
    "welcome1", "p@ssw0rd", "passw0rd", "admin", "admin123",
    "root", "toor", "pass", "test", "guest",
    "qwerty123", "login", "admin@123", "changeme", "ch@ngeme",
    # Keyboard patterns
    "qwertyuiop", "asdfghjkl", "zxcvbnm", "1qaz2wsx", "qweasdzxc",
    # Simple variations
    "password!", "password1!", "welcome!", "letmein!", "123456789",
    "1234567890", "0987654321", "11111111", "00000000", "12341234",
])

# Security scheme for JWT
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)  # Don't auto-raise 403, let us handle it

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate hash from a plain password."""
    return pwd_context.hash(password)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not a commonly used password

    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    # Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, f"Password must contain at least one special character ({special_chars})"

    # Check against common passwords list
    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a more unique password."

    return True, ""

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with unique JTI for revocation support."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
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
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """Authenticate user with email and password."""
    user = crud.get_user_by_email(db, email=email)
    if not user:
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

    # Check if token has been revoked (if it has a JTI)
    jti = payload.get("jti")
    if jti:
        blacklisted = db.query(models.TokenBlacklist).filter(
            models.TokenBlacklist.jti == jti
        ).first()
        if blacklisted:
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