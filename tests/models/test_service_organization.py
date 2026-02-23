"""Tests for the ServiceOrganization model."""
import pytest

from npycentral.models.service_organization import ServiceOrganization
from tests.factories import make_service_organization_data


# ========================================================================
# FROM_DICT TESTS
# ========================================================================

class TestServiceOrganizationFromDict:
    """Verify ServiceOrganization.from_dict parses dictionaries correctly."""

    def test_from_dict_with_all_fields(self):
        data = make_service_organization_data()
        so = ServiceOrganization.from_dict(data)

        assert so.soId == "50"
        assert so.soName == "MSP Corp"
        assert so.orgUnitType == "service_org"
        assert so.parentId == "1"
        assert so.externalId is None
        assert so.externalId2 is None
        assert so.contactFirstName == "Admin"
        assert so.contactLastName == "User"
        assert so.phone == "555-0000"
        assert so.contactTitle == "Admin"
        assert so.contactEmail == "admin@msp.com"
        assert so.contactPhone == "555-0001"
        assert so.contactPhoneExt == ""
        assert so.contactDepartment == "Operations"
        assert so.street1 == "456 Service Rd"
        assert so.street2 == ""
        assert so.city == "Techville"
        assert so.stateProv == "CA"
        assert so.country == "US"
        assert so.postalCode == "90210"
        assert so.isSystem is False
        assert so.isServiceOrg is True

    def test_from_dict_with_custom_so_id_and_name(self):
        data = make_service_organization_data(so_id="100", so_name="Other MSP")
        so = ServiceOrganization.from_dict(data)

        assert so.soId == "100"
        assert so.soName == "Other MSP"

    def test_from_dict_raises_type_error_on_missing_required_field(self):
        data = make_service_organization_data()
        del data["soName"]

        with pytest.raises(TypeError):
            ServiceOrganization.from_dict(data)

    def test_from_dict_raises_type_error_on_empty_dict(self):
        with pytest.raises(TypeError):
            ServiceOrganization.from_dict({})
