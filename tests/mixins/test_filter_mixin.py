"""Tests for FilterMixin methods."""
import pytest
import responses

from npycentral.models.device_filter import DeviceFilter
from tests.conftest import BASE_URL
from tests.factories import make_device_filter_data, make_paginated_response


class TestGetFilters:
    """Verify get_filters() fetches and parses device filters."""

    def test_returns_list_of_device_filter_objects(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83"),
                make_device_filter_data(filter_id="84", filter_name="Servers"),
            ]),
            status=200,
        )
        result = client.get_filters()
        assert len(result) == 2
        assert all(isinstance(f, DeviceFilter) for f in result)
        assert result[0].filterId == "83"
        assert result[1].filterId == "84"
        assert result[1].filterName == "Servers"

    def test_passes_view_scope_all_param(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([make_device_filter_data()]),
            status=200,
        )
        client.get_filters()
        get_calls = [
            c for c in activate_responses.calls if c.request.method == "GET"
        ]
        assert len(get_calls) == 1
        assert "viewScope=ALL" in get_calls[0].request.url

    def test_empty_response_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([]),
            status=200,
        )
        result = client.get_filters()
        assert result == []


class TestGetFilterById:
    """Verify get_filter_by_id() finds a filter from the full list."""

    def test_found_returns_matching_filter(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83"),
                make_device_filter_data(filter_id="84", filter_name="Servers"),
            ]),
            status=200,
        )
        result = client.get_filter_by_id("83")
        assert result is not None
        assert result.filterId == "83"
        assert result.filterName == "Domain Controllers"

    def test_not_found_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83"),
            ]),
            status=200,
        )
        result = client.get_filter_by_id("999")
        assert result is None


class TestGetFilterByName:
    """Verify get_filter_by_name() finds a filter by name."""

    def test_found_returns_matching_filter(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83", filter_name="Domain Controllers"),
                make_device_filter_data(filter_id="84", filter_name="Servers"),
            ]),
            status=200,
        )
        result = client.get_filter_by_name("Servers")
        assert result is not None
        assert result.filterId == "84"
        assert result.filterName == "Servers"

    def test_not_found_returns_none(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83"),
            ]),
            status=200,
        )
        result = client.get_filter_by_name("Nonexistent Filter")
        assert result is None
