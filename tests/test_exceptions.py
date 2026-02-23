"""Tests for the npycentral exception hierarchy."""
import pytest

from npycentral.exceptions import (
    NCentralError,
    AuthenticationError,
    APIError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    TaskError,
    CacheError,
)


# ========================================================================
# INHERITANCE TESTS
# ========================================================================

class TestExceptionInheritance:
    """Verify that every exception inherits from the correct parent."""

    def test_ncentral_error_inherits_from_exception(self):
        assert issubclass(NCentralError, Exception)

    def test_authentication_error_inherits_from_ncentral_error(self):
        assert issubclass(AuthenticationError, NCentralError)

    def test_api_error_inherits_from_ncentral_error(self):
        assert issubclass(APIError, NCentralError)

    def test_not_found_error_inherits_from_api_error(self):
        assert issubclass(NotFoundError, APIError)

    def test_rate_limit_error_inherits_from_api_error(self):
        assert issubclass(RateLimitError, APIError)

    def test_validation_error_inherits_from_ncentral_error(self):
        assert issubclass(ValidationError, NCentralError)

    def test_task_error_inherits_from_ncentral_error(self):
        assert issubclass(TaskError, NCentralError)

    def test_cache_error_inherits_from_ncentral_error(self):
        assert issubclass(CacheError, NCentralError)


# ========================================================================
# APIError ATTRIBUTE TESTS
# ========================================================================

class TestAPIErrorAttributes:
    """Verify that APIError stores status_code and response correctly."""

    def test_api_error_stores_message(self):
        err = APIError("something broke")
        assert str(err) == "something broke"

    def test_api_error_defaults_status_code_to_none(self):
        err = APIError("fail")
        assert err.status_code is None

    def test_api_error_defaults_response_to_none(self):
        err = APIError("fail")
        assert err.response is None

    def test_api_error_stores_status_code(self):
        err = APIError("fail", status_code=500)
        assert err.status_code == 500

    def test_api_error_stores_response(self):
        body = {"error": "internal"}
        err = APIError("fail", response=body)
        assert err.response == {"error": "internal"}

    def test_api_error_stores_all_fields(self):
        body = {"detail": "not found"}
        err = APIError("missing", status_code=404, response=body)
        assert str(err) == "missing"
        assert err.status_code == 404
        assert err.response == body


# ========================================================================
# APIError SUBCLASS ATTRIBUTE PROPAGATION
# ========================================================================

class TestAPIErrorSubclassAttributes:
    """Verify that NotFoundError and RateLimitError inherit status_code/response."""

    def test_not_found_error_stores_status_code_and_response(self):
        body = {"message": "no such device"}
        err = NotFoundError("gone", status_code=404, response=body)
        assert err.status_code == 404
        assert err.response == body

    def test_rate_limit_error_stores_status_code_and_response(self):
        body = {"retryAfter": 30}
        err = RateLimitError("slow down", status_code=429, response=body)
        assert err.status_code == 429
        assert err.response == body


# ========================================================================
# CATCHABILITY TESTS
# ========================================================================

class TestExceptionCatchability:
    """Verify that exceptions can be caught as their parent types."""

    def test_api_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise APIError("boom", status_code=500)

    def test_not_found_error_caught_as_api_error(self):
        with pytest.raises(APIError):
            raise NotFoundError("missing", status_code=404)

    def test_not_found_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise NotFoundError("missing", status_code=404)

    def test_rate_limit_error_caught_as_api_error(self):
        with pytest.raises(APIError):
            raise RateLimitError("throttled", status_code=429)

    def test_authentication_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise AuthenticationError("bad creds")

    def test_validation_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise ValidationError("bad input")

    def test_task_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise TaskError("task failed")

    def test_cache_error_caught_as_ncentral_error(self):
        with pytest.raises(NCentralError):
            raise CacheError("cache miss")
