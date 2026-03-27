from dataclasses import dataclass
from typing import Optional


# Fields returned by GET /api/sites and GET /api/customers/{id}/sites
_SITE_KNOWN_FIELDS = {
    'siteId', 'siteName', 'orgUnitType', 'parentId',
    'externalId', 'externalId2',
    'contactFirstName', 'contactLastName', 'phone', 'contactTitle',
    'contactEmail', 'contactPhone', 'contactPhoneExt', 'contactDepartment',
    'street1', 'street2', 'city', 'stateProv', 'country', 'postalCode',
    'isSystem', 'isServiceOrg',
}


@dataclass
class Site:
    """Represents a site (sub-level beneath a customer) in N-Central.

    Note: The API does not return customerId or customerName directly.
    The site's parent customer is identified by parentId (which equals
    the customer's orgUnitId / customerId).
    """
    siteId: int
    siteName: str
    parentId: int                       # customer's orgUnitId
    orgUnitType: str = ""
    externalId: str = ""
    externalId2: str = ""
    contactFirstName: str = ""
    contactLastName: str = ""
    phone: str = ""
    contactTitle: str = ""
    contactEmail: str = ""
    contactPhone: str = ""
    contactPhoneExt: str = ""
    contactDepartment: str = ""
    street1: str = ""
    street2: str = ""
    city: str = ""
    stateProv: str = ""
    country: Optional[str] = None
    postalCode: str = ""
    isSystem: bool = False
    isServiceOrg: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> 'Site':
        """Create a Site instance from an API response dict, ignoring unknown fields."""
        filtered = {k: v for k, v in data.items() if k in _SITE_KNOWN_FIELDS}
        if 'siteId' in filtered:
            filtered['siteId'] = int(filtered['siteId'])
        if 'parentId' in filtered and filtered['parentId'] is not None:
            filtered['parentId'] = int(filtered['parentId'])
        return cls(**filtered)

    @property
    def customerId(self) -> int:
        """Alias for parentId — the site's parent customer orgUnitId."""
        return self.parentId

    @property
    def full_contact_name(self) -> str:
        """Get the full contact name."""
        parts = [self.contactFirstName, self.contactLastName]
        return " ".join(p for p in parts if p).strip()
