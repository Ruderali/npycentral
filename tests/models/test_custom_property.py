"""Tests for the CustomProperty model."""
import pytest

from npycentral.models.custom_property import CustomProperty
from tests.factories import make_custom_property_data


# ========================================================================
# FROM_DICT TESTS
# ========================================================================

class TestCustomPropertyFromDict:
    """Verify CustomProperty.from_dict parses dictionaries correctly."""

    def test_from_dict_with_all_fields(self):
        data = make_custom_property_data(
            property_id=42,
            property_name="Location",
            property_type="TEXT",
            value="Building A",
        )
        prop = CustomProperty.from_dict(data)

        assert prop.propertyId == 42
        assert prop.propertyName == "Location"
        assert prop.propertyType == "TEXT"
        assert prop.value == "Building A"

    def test_enumerated_value_list_none_by_default(self):
        data = make_custom_property_data()
        prop = CustomProperty.from_dict(data)

        assert prop.enumeratedValueList is None

    def test_enumerated_value_list_with_values(self):
        data = make_custom_property_data(
            property_type="ENUMERATED",
            value="Option A",
            enumerated_value_list=["Option A", "Option B", "Option C"],
        )
        prop = CustomProperty.from_dict(data)

        assert prop.enumeratedValueList == ["Option A", "Option B", "Option C"]
        assert prop.propertyType == "ENUMERATED"

    def test_from_dict_value_can_be_none(self):
        data = make_custom_property_data(value=None)
        # Factory sets value directly, but from_dict uses data.get
        data["value"] = None
        prop = CustomProperty.from_dict(data)

        assert prop.value is None

    def test_from_dict_preserves_property_types(self):
        for ptype in ("ENUMERATED", "TEXT", "DATE", "URL"):
            data = make_custom_property_data(property_type=ptype)
            prop = CustomProperty.from_dict(data)
            assert prop.propertyType == ptype
