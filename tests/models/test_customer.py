"""Tests for the Customer model."""
import pytest
from unittest.mock import MagicMock

from npycentral.models.customer import Customer
from tests.factories import make_customer_data


# ========================================================================
# FROM_DICT TESTS
# ========================================================================

class TestCustomerFromDict:
    """Verify Customer.from_dict parses dictionaries correctly."""

    def test_from_dict_creates_customer_with_all_fields(self):
        data = make_customer_data()
        customer = Customer.from_dict(data)

        assert customer.customerId == 237
        assert customer.customerName == "Acme Corp"
        assert customer.orgUnitType == "customer"
        assert customer.parentId == 50
        assert customer.externalId == ""
        assert customer.externalId2 == ""
        assert customer.contactFirstName == "John"
        assert customer.contactLastName == "Doe"
        assert customer.phone == "555-1234"
        assert customer.contactTitle == "IT Manager"
        assert customer.contactEmail == "john@acme.com"
        assert customer.contactPhone == "555-5678"
        assert customer.contactPhoneExt == ""
        assert customer.contactDepartment == "IT"
        assert customer.street1 == "123 Main St"
        assert customer.street2 == ""
        assert customer.city == "Springfield"
        assert customer.stateProv == "IL"
        assert customer.country == "US"
        assert customer.postalCode == "62701"
        assert customer.county is None
        assert customer.isSystem is False
        assert customer.isServiceOrg is False
        assert customer._client is None

    def test_from_dict_converts_string_ids_to_int(self):
        data = make_customer_data()
        data["customerId"] = "237"
        data["parentId"] = "50"
        customer = Customer.from_dict(data)

        assert customer.customerId == 237
        assert isinstance(customer.customerId, int)
        assert customer.parentId == 50
        assert isinstance(customer.parentId, int)

    def test_from_dict_filters_unknown_fields(self):
        data = make_customer_data()
        data["unknownField"] = "should be ignored"
        data["anotherExtra"] = 999

        # Should not raise
        customer = Customer.from_dict(data)

        assert customer.customerId == 237
        assert not hasattr(customer, "unknownField")

    def test_from_dict_passes_client_reference(self):
        data = make_customer_data()
        mock_client = MagicMock()
        customer = Customer.from_dict(data, client=mock_client)

        assert customer._client is mock_client


# ========================================================================
# LOAD_PSA_CUSTOMER_ID TESTS
# ========================================================================

class TestCustomerLoadPsaCustomerId:
    """Verify load_psa_customer_id lazy-loading, caching, and force_refresh."""

    def test_raises_runtime_error_without_client(self):
        customer = Customer.from_dict(make_customer_data())

        with pytest.raises(RuntimeError, match="Cannot load PSA customer ID"):
            customer.load_psa_customer_id()

    def test_calls_client_get_psa_customer_id(self):
        mock_client = MagicMock()
        mock_client.get_psa_customer_id.return_value = 21215
        customer = Customer.from_dict(make_customer_data(), client=mock_client)

        result = customer.load_psa_customer_id()

        mock_client.get_psa_customer_id.assert_called_once_with(237)
        assert result == 21215

    def test_caches_result_on_second_call(self):
        mock_client = MagicMock()
        mock_client.get_psa_customer_id.return_value = 21215
        customer = Customer.from_dict(make_customer_data(), client=mock_client)

        customer.load_psa_customer_id()
        customer.load_psa_customer_id()

        mock_client.get_psa_customer_id.assert_called_once()

    def test_force_refresh_re_calls_api(self):
        mock_client = MagicMock()
        mock_client.get_psa_customer_id.side_effect = [21215, 99999]
        customer = Customer.from_dict(make_customer_data(), client=mock_client)

        first = customer.load_psa_customer_id()
        second = customer.load_psa_customer_id(force_refresh=True)

        assert mock_client.get_psa_customer_id.call_count == 2
        assert first == 21215
        assert second == 99999


# ========================================================================
# PSA_CUSTOMER_ID PROPERTY TESTS
# ========================================================================

class TestCustomerPsaCustomerIdProperty:
    """Verify psa_customer_id property lazy-loads and handles missing client."""

    def test_lazy_loads_on_first_access(self):
        mock_client = MagicMock()
        mock_client.get_psa_customer_id.return_value = 21215
        customer = Customer.from_dict(make_customer_data(), client=mock_client)

        result = customer.psa_customer_id

        mock_client.get_psa_customer_id.assert_called_once_with(237)
        assert result == 21215

    def test_returns_none_without_client(self):
        customer = Customer.from_dict(make_customer_data())

        result = customer.psa_customer_id

        assert result is None


# ========================================================================
# HAS_PSA_MAPPING TESTS
# ========================================================================

class TestCustomerHasPsaMapping:
    """Verify has_psa_mapping property before and after loading."""

    def test_false_initially(self):
        customer = Customer.from_dict(make_customer_data())

        assert customer.has_psa_mapping is False

    def test_true_after_load(self):
        mock_client = MagicMock()
        mock_client.get_psa_customer_id.return_value = 21215
        customer = Customer.from_dict(make_customer_data(), client=mock_client)

        customer.load_psa_customer_id()

        assert customer.has_psa_mapping is True


# ========================================================================
# FULL_CONTACT_NAME TESTS
# ========================================================================

class TestCustomerFullContactName:
    """Verify full_contact_name concatenation."""

    def test_full_contact_name(self):
        customer = Customer.from_dict(make_customer_data(
            contactFirstName="John",
            contactLastName="Doe",
        ))

        assert customer.full_contact_name == "John Doe"

    def test_full_contact_name_empty(self):
        customer = Customer.from_dict(make_customer_data(
            contactFirstName="",
            contactLastName="",
        ))

        assert customer.full_contact_name == ""


# ========================================================================
# FULL_ADDRESS TESTS
# ========================================================================

class TestCustomerFullAddress:
    """Verify full_address formatting and graceful missing-field handling."""

    def test_full_address_with_all_fields(self):
        customer = Customer.from_dict(make_customer_data())
        address = customer.full_address

        lines = address.split("\n")
        assert lines[0] == "123 Main St"
        assert "Springfield" in lines[1]
        assert "IL" in lines[1]
        assert "62701" in lines[1]
        assert lines[2] == "US"

    def test_full_address_missing_fields_skipped(self):
        customer = Customer.from_dict(make_customer_data(
            street1="",
            street2="",
            city="",
            stateProv="",
            postalCode="",
            country=None,
        ))

        assert customer.full_address == ""
