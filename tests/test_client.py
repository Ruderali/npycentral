"""Tests for NCentralClient and SecretString."""
import pytest
import requests
import responses
from zoneinfo import ZoneInfo

from npycentral.client import NCentralClient, SecretString
from npycentral.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from tests.conftest import (
    BASE_URL,
    TEST_JWT,
    FAKE_ACCESS_TOKEN,
    FAKE_REFRESH_TOKEN,
    AUTH_RESPONSE,
)


# ========================================================================
# SecretString TESTS
# ========================================================================

class TestSecretString:
    """Verify that SecretString masks its value in repr and str."""

    def test_repr_masks_value(self):
        s = SecretString("super-secret")
        assert repr(s) == "SecretString('**********')"

    def test_str_masks_value(self):
        s = SecretString("super-secret")
        assert str(s) == "**********"

    def test_get_secret_value_returns_actual_value(self):
        s = SecretString("super-secret")
        assert s.get_secret_value() == "super-secret"


# ========================================================================
# NCentralClient CONSTRUCTOR TESTS
# ========================================================================

class TestNCentralClientConstructor:
    """Verify constructor sets fields correctly and validates inputs."""

    def test_sets_base_url(self, client):
        assert client.base_url == BASE_URL

    def test_sets_jwt_as_secret_string(self, client):
        assert isinstance(client._jwt, SecretString)
        assert client._jwt.get_secret_value() == TEST_JWT

    def test_sets_base_so_id(self, client):
        assert client.base_so_id == "50"

    def test_sets_ui_port(self, client):
        assert client.ui_port == 8443

    def test_sets_default_timezone(self, client):
        assert client.default_timezone == ZoneInfo("UTC")

    def test_raises_value_error_when_base_url_missing(self):
        with pytest.raises(ValueError, match="base_url and jwt must be provided"):
            NCentralClient(base_url=None, jwt=TEST_JWT)

    def test_raises_value_error_when_jwt_missing(self):
        with pytest.raises(ValueError, match="base_url and jwt must be provided"):
            NCentralClient(base_url=BASE_URL, jwt=None)

    def test_raises_value_error_when_both_missing(self):
        with pytest.raises(ValueError, match="base_url and jwt must be provided"):
            NCentralClient()

    def test_repr_format(self, client):
        assert repr(client) == f"NCentralClient(base_url='{BASE_URL}')"


# ========================================================================
# AUTHENTICATION TESTS
# ========================================================================

class TestGetAuth:
    """Verify _get_auth() exchanges JWT for tokens."""

    def test_get_auth_success_returns_dict_with_secret_tokens(self, activate_responses, client):
        result = client._get_auth()
        assert isinstance(result["access_token"], SecretString)
        assert isinstance(result["refresh_token"], SecretString)
        assert result["access_token"].get_secret_value() == FAKE_ACCESS_TOKEN
        assert result["refresh_token"].get_secret_value() == FAKE_REFRESH_TOKEN
        assert result["expiry_seconds"] == 3600

    def test_get_auth_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.replace(
            responses.POST,
            f"{BASE_URL}/api/auth/authenticate",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client._get_auth()

    def test_get_auth_500_raises_api_error(self, activate_responses, client):
        activate_responses.replace(
            responses.POST,
            f"{BASE_URL}/api/auth/authenticate",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client._get_auth()

    def test_get_auth_network_error_raises_api_error(self, activate_responses, client):
        activate_responses.replace(
            responses.POST,
            f"{BASE_URL}/api/auth/authenticate",
            body=requests.exceptions.ConnectionError("Network error"),
        )
        with pytest.raises(APIError, match="Network error"):
            client._get_auth()


class TestGetToken:
    """Verify get_token() caches and returns access token."""

    def test_get_token_caches_across_calls(self, activate_responses, client):
        token1 = client.get_token()
        token2 = client.get_token()
        assert token1 == token2
        # Only one auth POST should have been made
        auth_calls = [
            c for c in activate_responses.calls
            if c.request.url == f"{BASE_URL}/api/auth/authenticate"
        ]
        assert len(auth_calls) == 1

    def test_get_token_returns_access_token_string(self, activate_responses, client):
        token = client.get_token()
        assert token == FAKE_ACCESS_TOKEN


class TestRefreshToken:
    """Verify refresh_token() refresh flow and fallback behaviour."""

    def test_refresh_token_with_no_cache_falls_back_to_jwt_auth(
        self, activate_responses, client
    ):
        # No cache populated; should call _get_auth via get_token
        token = client.refresh_token()
        assert token == FAKE_ACCESS_TOKEN

    def test_refresh_token_success_with_prepopulated_cache(
        self, activate_responses, client
    ):
        # Pre-populate the cache so refresh path is taken
        client.cache["tokens"] = {
            "access_token": SecretString("old-access-token"),
            "refresh_token": SecretString("old-refresh-token"),
            "expiry_seconds": 3600,
        }

        new_access = "refreshed-access-token"
        new_refresh = "refreshed-refresh-token"
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/auth/refresh",
            json={
                "tokens": {
                    "access": {"token": new_access, "expirySeconds": 3600},
                    "refresh": {"token": new_refresh, "expirySeconds": 86400},
                }
            },
            status=200,
        )

        token = client.refresh_token()
        assert token == new_access
        # Verify the cache was updated
        assert client.cache["tokens"]["access_token"].get_secret_value() == new_access
        assert client.cache["tokens"]["refresh_token"].get_secret_value() == new_refresh

    def test_refresh_token_failure_falls_back_to_jwt_auth(
        self, activate_responses, client
    ):
        # Pre-populate the cache so refresh path is attempted
        client.cache["tokens"] = {
            "access_token": SecretString("old-access-token"),
            "refresh_token": SecretString("old-refresh-token"),
            "expiry_seconds": 3600,
        }

        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/auth/refresh",
            json={"error": "token expired"},
            status=401,
        )

        # Should fall back to JWT auth and succeed
        token = client.refresh_token()
        assert token == FAKE_ACCESS_TOKEN


# ========================================================================
# GET METHOD TESTS
# ========================================================================

class TestGet:
    """Verify the get() HTTP helper."""

    def test_get_success(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/123",
            json={"deviceId": 123},
            status=200,
        )
        result = client.get("devices/123")
        assert result == {"deviceId": 123}

    def test_get_with_params(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": []},
            status=200,
        )
        client.get("devices", params={"filterName": "test"})
        # Verify query string was forwarded
        request = activate_responses.calls[-1].request
        assert "filterName=test" in request.url

    def test_get_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/1",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.get("devices/1")

    def test_get_404_raises_not_found_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/999",
            json={"error": "not found"},
            status=404,
        )
        with pytest.raises(NotFoundError) as exc_info:
            client.get("devices/999")
        assert exc_info.value.status_code == 404
        assert exc_info.value.response == {"error": "not found"}

    def test_get_429_raises_rate_limit_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"error": "rate limited"},
            status=429,
        )
        with pytest.raises(RateLimitError):
            client.get("devices")

    def test_get_500_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client.get("devices")

    def test_get_network_error_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/1",
            body=requests.exceptions.ConnectionError("Network error"),
        )
        with pytest.raises(APIError, match="Network error"):
            client.get("devices/1")

    def test_get_sends_bearer_token_header(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/1",
            json={"deviceId": 1},
            status=200,
        )
        client.get("devices/1")
        # The last call is the GET; find it among calls
        get_call = [
            c for c in activate_responses.calls
            if c.request.method == "GET"
        ][-1]
        assert get_call.request.headers["Authorization"] == f"Bearer {FAKE_ACCESS_TOKEN}"


# ========================================================================
# GET_ALL PAGINATION TESTS
# ========================================================================

class TestGetAll:
    """Verify get_all() pagination logic."""

    def test_single_page_with_total_items_matching(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 1}, {"id": 2}], "totalItems": 2},
            status=200,
        )
        results = client.get_all("devices", pagesize=50)
        assert results == [{"id": 1}, {"id": 2}]

    def test_multi_page_pagination(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 1}, {"id": 2}], "totalItems": 3},
            status=200,
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 3}], "totalItems": 3},
            status=200,
        )
        results = client.get_all("devices", pagesize=2)
        assert results == [{"id": 1}, {"id": 2}, {"id": 3}]

    def test_stops_when_page_returns_empty_data(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 1}], "totalItems": 100},
            status=200,
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [], "totalItems": 100},
            status=200,
        )
        results = client.get_all("devices", pagesize=50)
        assert results == [{"id": 1}]

    def test_stops_when_page_returns_fewer_items_than_pagesize(
        self, activate_responses, client
    ):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 1}, {"id": 2}]},
            status=200,
        )
        results = client.get_all("devices", pagesize=50)
        assert results == [{"id": 1}, {"id": 2}]
        # Only one GET request for devices
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET"
        ]
        assert len(get_calls) == 1

    def test_max_pages_limits_to_single_request(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": i} for i in range(50)], "totalItems": 200},
            status=200,
        )
        results = client.get_all("devices", pagesize=50, max_pages=1)
        assert len(results) == 50
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET"
        ]
        assert len(get_calls) == 1

    def test_custom_params_merged_with_pagination(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json={"data": [{"id": 1}], "totalItems": 1},
            status=200,
        )
        client.get_all("devices", params={"filterName": "test"}, pagesize=25)
        get_call = [
            c for c in activate_responses.calls
            if c.request.method == "GET"
        ][-1]
        assert "filterName=test" in get_call.request.url
        assert "pageSize=25" in get_call.request.url
        assert "pageNumber=1" in get_call.request.url


# ========================================================================
# POST METHOD TESTS
# ========================================================================

class TestPost:
    """Verify the post() HTTP helper."""

    def test_post_success(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/tasks",
            json={"taskId": 42},
            status=200,
        )
        result = client.post("tasks", data={"name": "reboot"})
        assert result == {"taskId": 42}

    def test_post_sends_json_body_and_content_type(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/tasks",
            json={"taskId": 42},
            status=200,
        )
        client.post("tasks", data={"name": "reboot"})
        # Find the POST to /api/tasks (not the auth POST)
        post_calls = [
            c for c in activate_responses.calls
            if c.request.url == f"{BASE_URL}/api/tasks"
        ]
        assert len(post_calls) == 1
        request = post_calls[0].request
        assert request.headers["Content-Type"] == "application/json"
        assert b'"name"' in request.body

    def test_post_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/tasks",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.post("tasks", data={"name": "reboot"})

    def test_post_500_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/tasks",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client.post("tasks", data={"name": "reboot"})

    def test_post_network_error_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/tasks",
            body=requests.exceptions.ConnectionError("Network error"),
        )
        with pytest.raises(APIError, match="Network error"):
            client.post("tasks", data={"name": "reboot"})


# ========================================================================
# PUT METHOD TESTS
# ========================================================================

class TestPut:
    """Verify the put() HTTP helper."""

    def test_put_success(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/1",
            json={"updated": True},
            status=200,
        )
        result = client.put("devices/1", data={"name": "new-name"})
        assert result == {"updated": True}

    def test_put_sends_json_body_and_content_type(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/1",
            json={"updated": True},
            status=200,
        )
        client.put("devices/1", data={"name": "new-name"})
        put_calls = [
            c for c in activate_responses.calls
            if c.request.method == "PUT"
        ]
        assert len(put_calls) == 1
        request = put_calls[0].request
        assert request.headers["Content-Type"] == "application/json"
        assert b'"name"' in request.body

    def test_put_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/1",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.put("devices/1", data={"name": "x"})

    def test_put_500_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/1",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client.put("devices/1", data={"name": "x"})

    def test_put_network_error_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/1",
            body=requests.exceptions.ConnectionError("Network error"),
        )
        with pytest.raises(APIError, match="Network error"):
            client.put("devices/1", data={"name": "x"})


# ========================================================================
# PATCH METHOD TESTS
# ========================================================================

class TestPatch:
    """Verify the patch() HTTP helper."""

    def test_patch_success(self, activate_responses, client):
        activate_responses.add(
            responses.PATCH,
            f"{BASE_URL}/api/devices/1",
            json={"patched": True},
            status=200,
        )
        result = client.patch("devices/1", data={"status": "active"})
        assert result == {"patched": True}

    def test_patch_sends_json_body_and_content_type(self, activate_responses, client):
        activate_responses.add(
            responses.PATCH,
            f"{BASE_URL}/api/devices/1",
            json={"patched": True},
            status=200,
        )
        client.patch("devices/1", data={"status": "active"})
        patch_calls = [
            c for c in activate_responses.calls
            if c.request.method == "PATCH"
        ]
        assert len(patch_calls) == 1
        request = patch_calls[0].request
        assert request.headers["Content-Type"] == "application/json"
        assert b'"status"' in request.body

    def test_patch_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.add(
            responses.PATCH,
            f"{BASE_URL}/api/devices/1",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.patch("devices/1", data={"status": "active"})

    def test_patch_500_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.PATCH,
            f"{BASE_URL}/api/devices/1",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client.patch("devices/1", data={"status": "active"})

    def test_patch_network_error_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.PATCH,
            f"{BASE_URL}/api/devices/1",
            body=requests.exceptions.ConnectionError("Network error"),
        )
        with pytest.raises(APIError, match="Network error"):
            client.patch("devices/1", data={"status": "active"})


# ========================================================================
# DELETE METHOD TESTS
# ========================================================================

class TestDelete:
    """Verify the delete() HTTP helper."""

    def test_delete_success_with_json_body(self, activate_responses, client):
        activate_responses.add(
            responses.DELETE,
            f"{BASE_URL}/api/devices/1",
            json={"deleted": True},
            status=200,
        )
        result = client.delete("devices/1")
        assert result == {"deleted": True}

    def test_delete_success_with_empty_body_returns_success(
        self, activate_responses, client
    ):
        activate_responses.add(
            responses.DELETE,
            f"{BASE_URL}/api/devices/1",
            body="",
            status=204,
        )
        result = client.delete("devices/1")
        assert result == {"success": True}

    def test_delete_401_raises_authentication_error(self, activate_responses, client):
        activate_responses.add(
            responses.DELETE,
            f"{BASE_URL}/api/devices/1",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(AuthenticationError):
            client.delete("devices/1")

    def test_delete_500_raises_api_error(self, activate_responses, client):
        activate_responses.add(
            responses.DELETE,
            f"{BASE_URL}/api/devices/1",
            json={"error": "server error"},
            status=500,
        )
        with pytest.raises(APIError):
            client.delete("devices/1")
