"""Tests for CustomerMixin methods."""
import pytest
import responses

from npycentral.models.customer import Customer
from npycentral.models.service_organization import ServiceOrganization
from npycentral.exceptions import NotFoundError
from tests.conftest import BASE_URL
from tests.factories import (
    make_customer_data,
    make_paginated_response,
    make_service_organization_data,
)


# ========================================================================
# CACHE MANAGEMENT TESTS
# ========================================================================


class TestCustomerCache:
    """Verify customer cache lifecycle methods."""

    def test_init_customer_cache_creates_attribute(self, client):
        assert not hasattr(client, "_customer_cache")
        client._init_customer_cache()
        assert hasattr(client, "_customer_cache")

    def test_set_customer_cache_ttl_changes_ttl(self, client):
        client._init_customer_cache()
        client.set_customer_cache_ttl(600)
        assert client._customer_cache_ttl == 600

    def test_clear_customer_cache_all_clears_cache(self, activate_responses, client):
        client._init_customer_cache()
        client._customer_cache["customers_50"] = ["fake"]
        client.clear_customer_cache()
        assert len(client._customer_cache) == 0

    def test_clear_customer_cache_specific_so_id_pops_key(self, activate_responses, client):
        client._init_customer_cache()
        client._customer_cache["customers_50"] = ["fake_50"]
        client._customer_cache["customers_60"] = ["fake_60"]
        client.clear_customer_cache(so_id=50)
        assert "customers_50" not in client._customer_cache
        assert "customers_60" in client._customer_cache

    def test_clear_customer_cache_when_not_initialized_does_nothing(self, client):
        # Should not raise even if _customer_cache doesn't exist
        client.clear_customer_cache()

    def test_cache_miss_then_hit_only_one_api_call(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237),
            ]),
            status=200,
        )
        # First call: cache miss, fetches from API
        result1 = client.get_customers(use_cache=True)
        # Second call: cache hit, no new API call
        result2 = client.get_customers(use_cache=True)

        assert len(result1) == 1
        assert len(result2) == 1

        # Count GET customer-list calls (exclude auth POST)
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/customers" in c.request.url
        ]
        assert len(get_calls) == 1

    def test_cache_bypass_always_fetches_fresh(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([make_customer_data(customer_id=237)]),
            status=200,
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([make_customer_data(customer_id=237)]),
            status=200,
        )
        client.get_customers(use_cache=False)
        client.get_customers(use_cache=False)

        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/customers" in c.request.url
        ]
        assert len(get_calls) == 2


# ========================================================================
# CORE CUSTOMER METHODS
# ========================================================================


class TestGetCustomers:
    """Verify get_customers() fetches and parses customer list."""

    def test_returns_customer_objects(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237),
                make_customer_data(customer_id=238, customer_name="Beta Inc"),
            ]),
            status=200,
        )
        result = client.get_customers()
        assert len(result) == 2
        assert all(isinstance(c, Customer) for c in result)
        assert result[0].customerId == 237
        assert result[1].customerName == "Beta Inc"

    def test_uses_base_so_id_default(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([make_customer_data()]),
            status=200,
        )
        client.get_customers()
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/customers" in c.request.url
        ]
        assert len(get_calls) == 1
        assert "/api/service-orgs/50/customers" in get_calls[0].request.url
        assert "soId=" not in get_calls[0].request.url

    def test_with_custom_so_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/99/customers",
            json=make_paginated_response([make_customer_data()]),
            status=200,
        )
        client.get_customers(so_id=99)
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/customers" in c.request.url
        ]
        assert "/api/service-orgs/99/customers" in get_calls[0].request.url

    def test_so_id_none_uses_flat_endpoint(self, activate_responses, client):
        """With no base_so_id, fall back to the unscoped /api/customers endpoint."""
        client.base_so_id = None
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/customers",
            json=make_paginated_response([make_customer_data()]),
            status=200,
        )
        client.get_customers()
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/customers" in c.request.url
        ]
        assert len(get_calls) == 1
        assert "/api/customers" in get_calls[0].request.url

    def test_scoped_fetch_stamps_so_id(self, activate_responses, client):
        """The API omits soId on customer payloads, so it is stamped from the scope."""
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/99/customers",
            json=make_paginated_response([make_customer_data(customer_id=237)]),
            status=200,
        )
        result = client.get_customers(so_id=99)
        assert result[0].soId == 99


class TestGetCustomer:
    """Verify get_customer() retrieves a single customer by ID or name."""

    def test_by_id_returns_customer(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/customers/237",
            json=make_customer_data(customer_id=237),
            status=200,
        )
        result = client.get_customer(customer_id=237)
        assert isinstance(result, Customer)
        assert result.customerId == 237

    def test_by_name_returns_customer(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237, customer_name="Acme Corp"),
                make_customer_data(customer_id=238, customer_name="Beta Inc"),
            ]),
            status=200,
        )
        result = client.get_customer(customer_name="Beta Inc")
        assert result.customerId == 238
        assert result.customerName == "Beta Inc"

    def test_neither_raises_value_error(self, client):
        with pytest.raises(ValueError, match="Must provide either customer_id or customer_name"):
            client.get_customer()

    def test_name_not_found_raises_not_found_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237, customer_name="Acme Corp"),
            ]),
            status=200,
        )
        with pytest.raises(NotFoundError, match="Customer not found"):
            client.get_customer(customer_name="Nonexistent Corp")

    def test_by_id_from_cache(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237, customer_name="Acme Corp"),
                make_customer_data(customer_id=238, customer_name="Beta Inc"),
            ]),
            status=200,
        )
        # Populate cache
        client.get_customers(use_cache=True)
        call_count_before = len(activate_responses.calls)

        # Should find in cache without making another API call
        result = client.get_customer(customer_id=237, use_cache=True)
        assert result.customerId == 237
        assert len(activate_responses.calls) == call_count_before


class TestFindCustomersByName:
    """Verify find_customers_by_name() returns partial matches."""

    def test_partial_match_found(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237, customer_name="Acme Corp"),
                make_customer_data(customer_id=238, customer_name="Beta Inc"),
            ]),
            status=200,
        )
        result = client.find_customers_by_name("Acme")
        assert len(result) == 1
        assert result[0].customerName == "Acme Corp"

    def test_no_matches_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json=make_paginated_response([
                make_customer_data(customer_id=237, customer_name="Acme Corp"),
            ]),
            status=200,
        )
        result = client.find_customers_by_name("Nonexistent")
        assert result == []


class TestCreateCustomer:
    """Verify create_customer() posts to correct endpoint."""

    def test_creates_customer_under_default_so(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/service-orgs/50/customers",
            json={"customerId": 300, "customerName": "New Corp"},
            status=200,
        )
        result = client.create_customer({"customerName": "New Corp"})
        assert result["customerId"] == 300

        post_calls = [
            c for c in activate_responses.calls
            if c.request.method == "POST" and "/service-orgs/" in c.request.url
        ]
        assert len(post_calls) == 1
        assert "/service-orgs/50/customers" in post_calls[0].request.url


class TestCreateSite:
    """Verify create_site() posts to correct endpoint."""

    def test_creates_site_under_customer(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/customers/237/sites",
            json={"siteId": 501, "siteName": "Branch Office"},
            status=200,
        )
        result = client.create_site(237, {"siteName": "Branch Office"})
        assert result["siteId"] == 501

        post_calls = [
            c for c in activate_responses.calls
            if c.request.method == "POST" and "/customers/237/sites" in c.request.url
        ]
        assert len(post_calls) == 1


class TestGetServiceOrgs:
    """Verify get_service_orgs() fetches and parses service organizations."""

    def test_returns_service_organization_objects(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/service-orgs",
            json=make_paginated_response([
                make_service_organization_data(so_id="50", so_name="MSP Corp"),
            ]),
            status=200,
        )
        result = client.get_service_orgs()
        assert len(result) == 1
        assert isinstance(result[0], ServiceOrganization)
        assert result[0].soId == "50"
        assert result[0].soName == "MSP Corp"


# ========================================================================
# PSA INTEGRATION TESTS
# ========================================================================


class TestGetPsaCustomerId:
    """Verify get_psa_customer_id() retrieves PSA mapping."""

    def test_found_returns_psa_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/standard-psa/customer-mapping/237",
            json=[{"psaCustomerId": 21215, "customerId": 237}],
            status=200,
        )
        result = client.get_psa_customer_id(237)
        assert result == 21215

    def test_empty_list_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/standard-psa/customer-mapping/237",
            json=[],
            status=200,
        )
        result = client.get_psa_customer_id(237)
        assert result is None

    def test_404_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/standard-psa/customer-mapping/237",
            json={"error": "not found"},
            status=404,
        )
        result = client.get_psa_customer_id(237)
        assert result is None


class TestGetPsaCustomerMapping:
    """Verify get_psa_customer_mapping() retrieves full mapping dict."""

    def test_found_returns_dict(self, activate_responses, client):
        mapping = {
            "contactId": -1,
            "customerId": 237,
            "psaCustomerId": 21215,
            "locationId": 10,
            "siteId": 500,
        }
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/standard-psa/customer-mapping/237",
            json=[mapping],
            status=200,
        )
        result = client.get_psa_customer_mapping(237)
        assert result is not None
        assert result["psaCustomerId"] == 21215
        assert result["customerId"] == 237
