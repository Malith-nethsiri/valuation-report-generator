"""
Base class for AI-powered narrative generation services.
Provides common patterns for Claude API interaction used across all narrative types.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

from .anthropic_client import get_anthropic_client, is_anthropic_configured

logger = logging.getLogger(__name__)


class BaseNarrativeService(ABC):
    """
    Abstract base class for AI-powered narrative generation services.

    Provides common functionality for:
    - Claude API client management
    - Error handling and logging
    - Configuration validation
    - Message creation pattern

    Subclasses must implement:
    - get_service_name(): Return service identifier for logging
    - get_system_context(): Return optional system prompt
    - build_prompt(data): Build the user prompt from input data
    - get_max_tokens(): Return max tokens for this narrative type
    """

    # Default model for all narrative services
    MODEL = "claude-3-5-haiku-20241022"

    # Default temperature for narrative generation
    TEMPERATURE = 0.7

    @abstractmethod
    def get_service_name(self) -> str:
        """Return the service name for logging purposes (e.g., 'BUILDING_NARRATIVE')."""
        pass

    @abstractmethod
    def build_prompt(self, data: Dict[str, Any]) -> str:
        """
        Build the user prompt from input data.

        Args:
            data: Dictionary containing the narrative input data

        Returns:
            The formatted prompt string for Claude
        """
        pass

    @abstractmethod
    def get_max_tokens(self) -> int:
        """Return the maximum tokens for this narrative type."""
        pass

    def get_system_context(self) -> Optional[str]:
        """
        Return optional system context for the API call.
        Override in subclass if system prompt is needed.
        """
        return None

    def get_temperature(self) -> float:
        """Return temperature setting. Override to customize."""
        return self.TEMPERATURE

    def is_configured(self) -> bool:
        """Check if the AI service is properly configured."""
        return is_anthropic_configured()

    def log_info(self, message: str) -> None:
        """Log info message with service name prefix."""
        logger.info("[%s] %s", self.get_service_name(), message)

    def log_warning(self, message: str) -> None:
        """Log warning message with service name prefix."""
        logger.warning("[%s] %s", self.get_service_name(), message)

    def log_error(self, message: str) -> None:
        """Log error message with service name prefix."""
        logger.error("[%s] %s", self.get_service_name(), message)

    async def generate(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Generate narrative using Claude API.

        This method handles:
        - Configuration validation
        - Client acquisition
        - API call with retry logic
        - Error handling and logging

        Args:
            data: Dictionary containing the narrative input data

        Returns:
            Generated narrative text or None if generation fails
        """
        if not self.is_configured():
            self.log_warning("ANTHROPIC_API_KEY not set")
            return None

        try:
            client = get_anthropic_client()

            # Build the prompt
            prompt = self.build_prompt(data)

            # Prepare message creation kwargs
            create_kwargs = {
                "model": self.MODEL,
                "max_tokens": self.get_max_tokens(),
                "messages": [{"role": "user", "content": prompt}]
            }

            # Add temperature if not default
            temperature = self.get_temperature()
            if temperature != 1.0:  # Claude default is 1.0
                create_kwargs["temperature"] = temperature

            # Add system context if provided
            system_context = self.get_system_context()
            if system_context:
                create_kwargs["system"] = system_context

            # Make the API call
            message = client.messages.create(**create_kwargs)

            # Extract and return the response
            if message.content and len(message.content) > 0:
                narrative = message.content[0].text.strip()
                self.log_info(f"Generated {len(narrative)} chars")
                return narrative
            else:
                self.log_warning("No content in Claude response")
                return None

        except Exception as e:
            self.log_error(str(e))
            return None
