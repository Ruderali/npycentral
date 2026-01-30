"""N-Central API Client with modular functionality via mixins."""
import logging
from typing import Any, Dict, Optional
import requests
from cachetools import TTLCache
from zoneinfo import ZoneInfo

from .mixins.device_mixin import DeviceMixin
from .mixins.customer_mixin import CustomerMixin
from .mixins.task_mixin import TaskMixin
from .mixins.property_mixin import PropertyMixin
from .mixins.filter_mixin import FilterMixin
from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class SecretString:
    """A string wrapper that hides its value in string representations."""

    __slots__ = ('_value',)

    def __init__(self, value: str):
        self._value = value

    def get_secret_value(self) -> str:
        """Explicitly retrieve the secret value."""
        return self._value

    def __repr__(self) -> str:
        return "SecretString('**********')"

    def __str__(self) -> str:
        return "**********"


class NCentralClient(DeviceMixin, CustomerMixin, TaskMixin, PropertyMixin, FilterMixin):
    """N-Central API Client with modular functionality via mixins."""

    def __init__(
        self,
        base_url: str = None,
        jwt: str = None,
        base_so_id: str = "50", # Default Service Organization ID for servers with a single SO
        default_timezone: str = "UTC",
        ui_port: int = 8443,
        token_ttl: int = 3600
    ):
        """
        Initialize N-Central API client.

        Args:
            base_url: N-Central server URL (e.g., https://ncentral.example.com)
            jwt: JWT token from N-Central UI
            base_so_id: Default Service Organization ID
            default_timezone: IANA timezone name for datetime operations
            ui_port: N-Central UI port (default: 8443)
            token_ttl: Access token cache TTL in seconds (default: 3600)

        Raises:
            ValueError: If base_url or jwt are not provided
        """
        if not base_url or not jwt:
            raise ValueError("base_url and jwt must be provided")

        # API Configuration
        self.base_url = base_url
        self._jwt = SecretString(jwt)
        self.base_so_id = base_so_id
        self.ui_port = ui_port

        # Configuration
        self.default_timezone = ZoneInfo(default_timezone)
        self.cache = TTLCache(maxsize=2, ttl=token_ttl)

    def __repr__(self) -> str:
        return f"NCentralClient(base_url='{self.base_url}')"

    # ========================================================================
    # AUTHENTICATION METHODS
    # ========================================================================

    def _get_auth(self) -> Dict[str, Any]:
        """
        Exchange JWT for access and refresh tokens.

        Returns:
            dict: Dictionary containing access_token, refresh_token, and expiry_seconds

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/auth/authenticate"
        headers = {"Authorization": f"Bearer {self._jwt.get_secret_value()}"}

        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            tokens = data.get("tokens", {})

            return {
                "access_token": SecretString(tokens.get("access", {}).get("token")),
                "refresh_token": SecretString(tokens.get("refresh", {}).get("token")),
                "expiry_seconds": tokens.get("access", {}).get("expirySeconds", 3600)
            }
        except requests.HTTPError as e:
            logger.error(f"Authentication failed: {e}")
            if e.response.status_code == 401:
                raise AuthenticationError(f"JWT authentication failed: {e}")
            else:
                raise APIError(
                    f"Authentication request failed: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Authentication request error: {e}")
            raise APIError(f"Network error during authentication: {e}")

    def get_token(self) -> str:
        """
        Return a cached access token, or fetch a new one if expired.

        Returns:
            str: Valid access token

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the request fails
        """
        if "tokens" not in self.cache:
            self.cache["tokens"] = self._get_auth()
        return self.cache["tokens"]["access_token"].get_secret_value()

    def refresh_token(self) -> str:
        """
        Use refresh token to get a new access token.

        Returns:
            str: New access token

        Raises:
            AuthenticationError: If refresh fails
            APIError: If the request fails
        """
        if "tokens" not in self.cache:
            return self.get_token()

        refresh_token = self.cache["tokens"].get("refresh_token")
        if not refresh_token:
            return self.get_token()

        url = f"{self.base_url}/api/auth/refresh"
        headers = {"Content-Type": "application/json"}
        payload = {"refresh_token": refresh_token.get_secret_value()}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()

            data = response.json()
            tokens = data.get("tokens", {})

            self.cache["tokens"] = {
                "access_token": SecretString(tokens.get("access", {}).get("token")),
                "refresh_token": SecretString(tokens.get("refresh", {}).get("token")),
                "expiry_seconds": tokens.get("access", {}).get("expirySeconds", 3600)
            }

            return self.cache["tokens"]["access_token"].get_secret_value()
        except requests.HTTPError as e:
            logger.warning(f"Token refresh failed: {e}, falling back to JWT auth")
            self.cache.clear()
            return self.get_token()
        except requests.RequestException as e:
            logger.warning(f"Token refresh request error: {e}, falling back to JWT auth")
            self.cache.clear()
            return self.get_token()

    # ========================================================================
    # BASE HTTP METHODS
    # ========================================================================

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the N-Central API.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            params: Query parameters

        Returns:
            dict: JSON response from the API

        Raises:
            AuthenticationError: If authentication fails (401)
            NotFoundError: If resource is not found (404)
            RateLimitError: If rate limit is exceeded (429)
            APIError: For other API errors
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {"Authorization": f"Bearer {self.get_token()}"}

        try:
            response = requests.get(url, headers=headers, params=params or {})
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP error for GET {endpoint}: {e}")
            if e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {endpoint}: {e}")
            elif e.response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {endpoint}",
                    status_code=404,
                    response=e.response.json() if e.response else None
                )
            elif e.response.status_code == 429:
                raise RateLimitError(
                    f"Rate limit exceeded for {endpoint}",
                    status_code=429,
                    response=e.response.json() if e.response else None
                )
            else:
                raise APIError(
                    f"API request failed for {endpoint}: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for GET {endpoint}: {e}")
            raise APIError(f"Network error for {endpoint}: {e}")

    def get_all(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        pagesize: int = 50,
        max_pages: Optional[int] = None
    ) -> list:
        """
        Fetch all pages for a given endpoint.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            params: Query parameters
            pagesize: Number of results per page (default: 50)
            max_pages: Maximum number of pages to fetch (default: None for all pages)

        Returns:
            list: Combined results from all pages

        Raises:
            AuthenticationError: If authentication fails
            APIError: If the request fails
        """
        results = []
        page = 1
        query_params = params.copy() if params else {}
        query_params["pageSize"] = pagesize

        while True:
            if max_pages and page > max_pages:
                break

            query_params["pageNumber"] = page
            page_response = self.get(endpoint, params=query_params)

            if not page_response:
                break

            page_data = page_response.get("data", [])
            if isinstance(page_response, list):
                page_data = page_response

            if not page_data:
                break

            results.extend(page_data)

            total_items = page_response.get("totalItems", 0)
            if isinstance(page_response, dict) and total_items:
                if len(results) >= total_items:
                    break

            if len(page_data) < pagesize:
                break

            page += 1

        return results

    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a POST request.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            data: Request body data

        Returns:
            dict: JSON response from the API

        Raises:
            AuthenticationError: If authentication fails (401)
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP error for POST {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.debug(f"Error details: {error_detail}")
                except Exception:
                    logger.debug(f"Response content: {e.response.text}")

            if e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {endpoint}: {e}")
            else:
                raise APIError(
                    f"POST request failed for {endpoint}: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for POST {endpoint}: {e}")
            raise APIError(f"Network error for {endpoint}: {e}")

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a PUT request.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            data: Request body data

        Returns:
            dict: JSON response from the API

        Raises:
            AuthenticationError: If authentication fails (401)
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP error for PUT {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.debug(f"Error details: {error_detail}")
                except Exception:
                    logger.debug(f"Response content: {e.response.text}")

            if e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {endpoint}: {e}")
            else:
                raise APIError(
                    f"PUT request failed for {endpoint}: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for PUT {endpoint}: {e}")
            raise APIError(f"Network error for {endpoint}: {e}")

    def patch(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a PATCH request.

        Args:
            endpoint: API endpoint (without /api/ prefix)
            data: Request body data

        Returns:
            dict: JSON response from the API

        Raises:
            AuthenticationError: If authentication fails (401)
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.get_token()}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.patch(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"HTTP error for PATCH {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.debug(f"Error details: {error_detail}")
                except Exception:
                    logger.debug(f"Response content: {e.response.text}")

            if e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {endpoint}: {e}")
            else:
                raise APIError(
                    f"PATCH request failed for {endpoint}: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for PATCH {endpoint}: {e}")
            raise APIError(f"Network error for {endpoint}: {e}")

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Perform a DELETE request.

        Args:
            endpoint: API endpoint (without /api/ prefix)

        Returns:
            dict: JSON response from the API, or {"success": True} if no content

        Raises:
            AuthenticationError: If authentication fails (401)
            APIError: If the request fails
        """
        url = f"{self.base_url}/api/{endpoint}"
        headers = {"Authorization": f"Bearer {self.get_token()}"}

        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            if response.text:
                return response.json()
            return {"success": True}
        except requests.HTTPError as e:
            logger.error(f"HTTP error for DELETE {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.debug(f"Error details: {error_detail}")
                except Exception:
                    logger.debug(f"Response content: {e.response.text}")

            if e.response.status_code == 401:
                raise AuthenticationError(f"Authentication failed for {endpoint}: {e}")
            else:
                raise APIError(
                    f"DELETE request failed for {endpoint}: {e}",
                    status_code=e.response.status_code,
                    response=e.response.json() if e.response else None
                )
        except requests.RequestException as e:
            logger.error(f"Request failed for DELETE {endpoint}: {e}")
            raise APIError(f"Network error for {endpoint}: {e}")