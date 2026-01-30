"""
Singleton Anthropic client provider for AI services.
Centralizes client initialization, configuration, and connection management.
"""

import os
from functools import lru_cache
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment files: .env first, then .env.local overrides
env_path = Path(__file__).parent.parent.parent
load_dotenv(env_path / '.env')
load_dotenv(env_path / '.env.local', override=True)


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
