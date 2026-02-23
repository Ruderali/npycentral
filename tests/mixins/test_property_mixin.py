"""Tests for PropertyMixin methods."""
import json

import pytest
import responses

from npycentral.models.custom_property import CustomProperty
from tests.conftest import BASE_URL
from tests.factories import make_custom_property_data


class TestGetDeviceCustomProperties:
    """Verify get_device_custom_properties() fetches and parses properties."""

    def test_dict_response_returns_list_of_custom_property(self, activate_responses, client):
        prop1 = make_custom_property_data(property_id=1, property_name="Prop1")
        prop2 = make_custom_property_data(property_id=2, property_name="Prop2")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties",
            json={"data": [prop1, prop2]},
            status=200,
        )
        result = client.get_device_custom_properties(12345)
        assert len(result) == 2
        assert all(isinstance(p, CustomProperty) for p in result)
        assert result[0].propertyName == "Prop1"
        assert result[1].propertyName == "Prop2"

    def test_list_response_returns_list_of_custom_property(self, activate_responses, client):
        prop1 = make_custom_property_data(property_id=1, property_name="PropA")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties",
            json=[prop1],
            status=200,
        )
        result = client.get_device_custom_properties(12345)
        assert len(result) == 1
        assert result[0].propertyName == "PropA"

    def test_empty_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties",
            json={"data": []},
            status=200,
        )
        result = client.get_device_custom_properties(12345)
        assert result == []


class TestGetDeviceCustomProperty:
    """Verify get_device_custom_property() fetches a single property by ID."""

    def test_found_returns_custom_property(self, activate_responses, client):
        prop = make_custom_property_data(property_id=1, property_name="TicketId")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties/1",
            json={"data": prop},
            status=200,
        )
        result = client.get_device_custom_property(12345, 1)
        assert result is not None
        assert isinstance(result, CustomProperty)
        assert result.propertyId == 1
        assert result.propertyName == "TicketId"

    def test_empty_response_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties/1",
            json={"data": None},
            status=200,
        )
        result = client.get_device_custom_property(12345, 1)
        assert result is None


class TestGetDeviceCustomPropertyByName:
    """Verify get_device_custom_property_by_name() searches by property name."""

    def test_found_returns_matching_property(self, activate_responses, client):
        prop1 = make_custom_property_data(property_id=1, property_name="Location")
        prop2 = make_custom_property_data(property_id=2, property_name="TicketId")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties",
            json={"data": [prop1, prop2]},
            status=200,
        )
        result = client.get_device_custom_property_by_name(12345, "TicketId")
        assert result is not None
        assert result.propertyId == 2
        assert result.propertyName == "TicketId"

    def test_not_found_returns_none(self, activate_responses, client):
        prop1 = make_custom_property_data(property_id=1, property_name="Location")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/custom-properties",
            json={"data": [prop1]},
            status=200,
        )
        result = client.get_device_custom_property_by_name(12345, "Nonexistent")
        assert result is None


class TestUpdateDeviceCustomProperty:
    """Verify update_device_custom_property() sends PUT and parses response."""

    def test_success_returns_updated_property(self, activate_responses, client):
        updated_prop = make_custom_property_data(
            property_id=1, property_name="Location", value="new_value"
        )
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/12345/custom-properties/1",
            json={"data": updated_prop},
            status=200,
        )
        result = client.update_device_custom_property(12345, 1, "new_value")
        assert result is not None
        assert isinstance(result, CustomProperty)
        assert result.value == "new_value"

        # Verify the PUT payload
        put_calls = [
            c for c in activate_responses.calls if c.request.method == "PUT"
        ]
        assert len(put_calls) == 1
        body = json.loads(put_calls[0].request.body)
        assert body == {"value": "new_value"}

    def test_empty_response_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.PUT,
            f"{BASE_URL}/api/devices/12345/custom-properties/1",
            json={"data": None},
            status=200,
        )
        result = client.update_device_custom_property(12345, 1, "new_value")
        assert result is None
