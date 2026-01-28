from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceOrganization:
    soId: str
    soName: str
    orgUnitType: str
    parentId: str
    externalId: Optional[str]
    externalId2: Optional[str]
    contactFirstName: str
    contactLastName: str
    phone: str
    contactTitle: str
    contactEmail: str
    contactPhone: str
    contactPhoneExt: str
    contactDepartment: str
    street1: str
    street2: str
    city: str
    stateProv: str
    country: str
    postalCode: str
    isSystem: bool
    isServiceOrg: bool
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceOrganization':
        """Create a ServiceOrganization instance from a dictionary."""
        return cls(**data)