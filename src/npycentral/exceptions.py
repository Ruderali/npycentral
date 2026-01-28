"""Custom exceptions for npycentral SDK."""
from typing import Optional, Dict, Any


class NCentralError(Exception):
    """Base exception for all N-Central API errors."""
    pass


class AuthenticationError(NCentralError):
    """Raised when authentication fails."""
    pass


class APIError(NCentralError):
    """Raised when API request fails."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code
            response: API response dictionary
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Raised when resource is not found (404)."""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded (429)."""
    pass


class ValidationError(NCentralError):
    """Raised when input validation fails."""
    pass


class TaskError(NCentralError):
    """Raised when task execution fails."""
    pass


class CacheError(NCentralError):
    """Raised when caching operations fail."""
    pass