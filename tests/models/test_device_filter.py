"""Tests for the DeviceFilter model."""
import pytest

from npycentral.models.device_filter import DeviceFilter
from tests.factories import make_device_filter_data


# ========================================================================
# FROM_DICT TESTS
# ========================================================================

class TestDeviceFilterFromDict:
    """Verify DeviceFilter.from_dict parses dictionaries correctly."""

    def test_from_dict_with_all_fields(self):
        data = make_device_filter_data()
        filt = DeviceFilter.from_dict(data)

        assert filt.filterId == "83"
        assert filt.filterName == "Domain Controllers"
        assert filt.description == "All domain controllers"

    def test_from_dict_missing_fields_default_to_empty_strings(self):
        filt = DeviceFilter.from_dict({})

        assert filt.filterId == ""
        assert filt.filterName == ""

    def test_description_is_none_when_not_provided(self):
        data = make_device_filter_data()
        del data["description"]
        filt = DeviceFilter.from_dict(data)

        assert filt.description is None

    def test_from_dict_with_custom_values(self):
        data = make_device_filter_data(
            filter_id="99",
            filter_name="Servers Only",
            description="Windows servers",
        )
        filt = DeviceFilter.from_dict(data)

        assert filt.filterId == "99"
        assert filt.filterName == "Servers Only"
        assert filt.description == "Windows servers"

    def test_from_dict_description_explicit_none(self):
        data = make_device_filter_data()
        data["description"] = None
        filt = DeviceFilter.from_dict(data)

        assert filt.description is None
