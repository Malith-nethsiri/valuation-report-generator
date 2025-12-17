"""
Robust HTTP API client with timeout, retry logic, and circuit breaker pattern.

This module provides a resilient HTTP client for external API calls with:
- Configurable timeouts
- Automatic retry with exponential backoff
- Circuit breaker to prevent cascading failures
- Centralized error handling
"""

import requests
import time
import logging
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open (too many failures)"""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, reject all requests
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting recovery (OPEN -> HALF_OPEN)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            # Check if timeout has passed
            if self.last_failure_time and \
               datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
                logger.info(f"Circuit breaker entering HALF_OPEN state for {func.__name__}")
            else:
                raise CircuitBreakerOpen(
                    f"Circuit breaker is OPEN for {func.__name__}. "
                    f"Too many failures. Retry after {self.timeout} seconds."
                )

        try:
            result = func(*args, **kwargs)
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                logger.info(f"Circuit breaker CLOSED for {func.__name__} - service recovered")
            self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                logger.error(
                    f"Circuit breaker OPEN for {func.__name__} "
                    f"after {self.failure_count} failures"
                )

            raise e


class APIClient:
    """
    Robust HTTP client with timeout and retry logic.

    Features:
    - Configurable timeout (default 30s)
    - Automatic retry with exponential backoff
    - Retries on specific status codes (429, 500, 502, 503, 504)
    - Circuit breaker integration
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        retry_statuses: tuple = (429, 500, 502, 503, 504),
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_statuses: HTTP status codes that trigger retry
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries (exponential backoff cap)
            circuit_breaker: Optional circuit breaker instance
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_statuses = retry_statuses
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.session = requests.Session()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff"""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)

    def _should_retry(self, response: Optional[requests.Response], exception: Optional[Exception]) -> bool:
        """Determine if request should be retried"""
        # Retry on connection errors, timeouts
        if exception:
            if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
                return True
            return False

        # Retry on specific status codes
        if response and response.status_code in self.retry_statuses:
            return True

        return False

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Optional request headers
            params: Optional query parameters
            json: Optional JSON body
            data: Optional request body
            **kwargs: Additional arguments passed to requests

        Returns:
            Response object

        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            requests.RequestException: If all retries failed
        """
        def _make_request():
            last_exception = None
            last_response = None

            for attempt in range(self.max_retries + 1):
                try:
                    logger.debug(
                        f"API request attempt {attempt + 1}/{self.max_retries + 1}: "
                        f"{method} {url}"
                    )

                    response = self.session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json,
                        data=data,
                        timeout=self.timeout,
                        **kwargs
                    )

                    # Success - return response
                    if response.status_code < 400 or not self._should_retry(response, None):
                        logger.debug(f"API request successful: {method} {url} -> {response.status_code}")
                        return response

                    # Failed but retryable
                    last_response = response
                    logger.warning(
                        f"API request failed with status {response.status_code}: {method} {url}"
                    )

                except (requests.ConnectionError, requests.Timeout) as e:
                    last_exception = e
                    logger.warning(f"API request error: {method} {url} -> {type(e).__name__}: {e}")

                # Don't sleep after last attempt
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f}s...")
                    time.sleep(delay)

            # All retries exhausted
            if last_exception:
                logger.error(f"API request failed after {self.max_retries + 1} attempts: {method} {url}")
                raise last_exception

            if last_response:
                logger.error(
                    f"API request failed after {self.max_retries + 1} attempts "
                    f"with status {last_response.status_code}: {method} {url}"
                )
                return last_response

            raise requests.RequestException(f"Request failed: {method} {url}")

        # Use circuit breaker if available
        return self.circuit_breaker.call(_make_request)

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request"""
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request"""
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> requests.Response:
        """Make PUT request"""
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> requests.Response:
        """Make DELETE request"""
        return self.request("DELETE", url, **kwargs)


# ===== GLOBAL CLIENT INSTANCES =====

# Google Maps API client
google_maps_client = APIClient(
    timeout=30,
    max_retries=3,
    circuit_breaker=CircuitBreaker(failure_threshold=5, timeout=60)
)

# Google Vision API client (for OCR)
google_vision_client = APIClient(
    timeout=45,  # OCR can take longer
    max_retries=3,
    circuit_breaker=CircuitBreaker(failure_threshold=5, timeout=60)
)

# Anthropic Claude API client (for AI parsing)
anthropic_client = APIClient(
    timeout=60,  # AI generation can take longer
    max_retries=2,  # Fewer retries for expensive AI calls
    circuit_breaker=CircuitBreaker(failure_threshold=3, timeout=120)
)


# ===== DECORATOR FOR EASY CIRCUIT BREAKER USAGE =====

def with_circuit_breaker(breaker: Optional[CircuitBreaker] = None):
    """
    Decorator to add circuit breaker protection to any function.

    Usage:
        @with_circuit_breaker()
        def my_api_call():
            return requests.get("https://api.example.com")
    """
    if breaker is None:
        breaker = CircuitBreaker()

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator
