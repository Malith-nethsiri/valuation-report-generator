"""
Password hashing, verification, and strength validation utilities.

Extracted from auth.py to break the circular import between auth.py and user_crud.py:
  auth.py → crud.get_user_by_email → (via __init__) user_crud.py → auth.get_password_hash
"""

from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Common passwords list — prevents users from choosing well-known weak passwords
# These appear in password spraying attacks and should always be blocked.
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

# Pre-computed bcrypt hash used to equalise timing when a user does not exist.
# Without this, an attacker can distinguish valid emails from invalid ones by
# measuring response time (bcrypt takes ~300 ms; a missing-user early-return is ~1 ms).
_FAKE_HASH = pwd_context.hash("_constant_time_dummy_password_do_not_use_")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash from a plain password."""
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

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, f"Password must contain at least one special character ({special_chars})"

    if password.lower() in COMMON_PASSWORDS:
        return False, "This password is too common. Please choose a more unique password."

    return True, ""
