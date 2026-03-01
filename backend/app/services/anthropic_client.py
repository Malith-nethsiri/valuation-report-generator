"""
Singleton Anthropic client provider for AI services.
Centralizes client initialization, configuration, and connection management.
"""

import os
from functools import lru_cache
from anthropic import Anthropic

# ---------------------------------------------------------------------------
# Model configuration
# Override via environment variables so model changes do not require redeployment.
# ---------------------------------------------------------------------------
AI_DEFAULT_MODEL: str = os.getenv("AI_DEFAULT_MODEL", "claude-3-5-haiku-20241022")
AI_VEHICLE_MODEL: str = os.getenv("AI_VEHICLE_MODEL", "claude-3-5-haiku-20241022")


@lru_cache(maxsize=1)
def get_anthropic_client() -> Anthropic:
    """
    Get a singleton Anthropic client instance.

    Uses lru_cache to ensure only one client is created and reused
    across all AI service calls. This provides:
    - Connection pooling benefits
    - Centralized configuration
    - Single point of monitoring/logging

    Returns:
        Anthropic: Configured Anthropic client instance

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set

    Example:
        from app.services.anthropic_client import get_anthropic_client

        client = get_anthropic_client()
        response = client.messages.create(...)
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    return Anthropic(api_key=api_key)


def get_api_key() -> str:
    """
    Get the Anthropic API key from environment.

    For backward compatibility with code that checks for the key
    before attempting AI operations.

    Returns:
        str: The API key or empty string if not set
    """
    return os.getenv("ANTHROPIC_API_KEY", "")


def is_anthropic_configured() -> bool:
    """
    Check if Anthropic API is properly configured.

    Returns:
        bool: True if API key is set, False otherwise
    """
    return bool(os.getenv("ANTHROPIC_API_KEY"))
