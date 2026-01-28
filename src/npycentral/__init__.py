"""npycentral - Python SDK for N-Central RMM API.

This package provides a comprehensive Python SDK for interacting with
the N-able N-Central RMM API.

Basic usage:
    from npycentral import NCentralClient

    nc = NCentralClient(
        base_url="https://ncentral.example.com",
        jwt="your_jwt_token"
    )

    devices = nc.get_devices()
"""
import logging

from .client import NCentralClient
from .exceptions import (
    NCentralError,
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    TaskError,
    CacheError,
)
from ._version import __version__

# Set up null handler (library best practice)
logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = [
    'NCentralClient',
    'NCentralError',
    'APIError',
    'AuthenticationError',
    'NotFoundError',
    'RateLimitError',
    'ValidationError',
    'TaskError',
    'CacheError',
    '__version__',
]