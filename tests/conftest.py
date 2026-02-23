"""Shared fixtures for npycentral test suite."""
import pytest
import responses
from npycentral import NCentralClient

BASE_URL = "https://ncentral.test.example.com"
TEST_JWT = "test-jwt-token-value"
FAKE_ACCESS_TOKEN = "fake-access-token-12345"
FAKE_REFRESH_TOKEN = "fake-refresh-token-67890"

AUTH_RESPONSE = {
    "tokens": {
        "access": {
            "token": FAKE_ACCESS_TOKEN,
            "expirySeconds": 3600,
        },
        "refresh": {
            "token": FAKE_REFRESH_TOKEN,
            "expirySeconds": 86400,
        },
    }
}


@pytest.fixture
def activate_responses():
    """Activate responses mocking for every test with auth pre-registered."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(
            responses.POST,
            f"{BASE_URL}/api/auth/authenticate",
            json=AUTH_RESPONSE,
            status=200,
        )
        yield rsps


@pytest.fixture
def client():
    """Return a fresh NCentralClient. Auth is mocked by activate_responses."""
    return NCentralClient(
        base_url=BASE_URL,
        jwt=TEST_JWT,
        base_so_id="50",
        default_timezone="UTC",
        ui_port=8443,
        token_ttl=3600,
    )
