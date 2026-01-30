from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class Customer:
    customerId: int
    customerName: str
    orgUnitType: str
    parentId: int
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
    county: Optional[str] = None
    isSystem: bool = False
    isServiceOrg: bool = False
    _client: Optional[Any] = field(default=None, repr=False)
    _psa_customer_id: Optional[int] = field(default=None, repr=False)

    @classmethod
    def from_dict(cls, data: dict, client: Optional[Any] = None) -> 'Customer':
        """
        Create a Customer instance from a dictionary.

        Args:
            data: Dictionary containing customer data from API
            client: Optional NCentralClient reference for lazy-loading PSA ID
        """
        customer_data = data.copy()

        # Handle string IDs from API (convert to int)
        if 'customerId' in customer_data:
            customer_data['customerId'] = int(customer_data['customerId'])
        if 'parentId' in customer_data:
            customer_data['parentId'] = int(customer_data['parentId'])

        # Add client reference
        customer_data['_client'] = client

        # Filter to only known fields
        known_fields = {
            'customerId', 'customerName', 'orgUnitType', 'parentId',
            'externalId', 'externalId2', 'contactFirstName', 'contactLastName',
            'phone', 'contactTitle', 'contactEmail', 'contactPhone',
            'contactPhoneExt', 'contactDepartment', 'street1', 'street2',
            'city', 'stateProv', 'country', 'postalCode', 'county',
            'isSystem', 'isServiceOrg', '_client', '_psa_customer_id'
        }
        filtered_data = {k: v for k, v in customer_data.items() if k in known_fields}

        return cls(**filtered_data)

    def load_psa_customer_id(self, force_refresh: bool = False) -> Optional[int]:
        """
        Lazy-load the PSA customer ID from the API.

        This method fetches the PSA (ConnectWise/Autotask) customer ID mapping
        on-demand without requiring a separate API call manually.

        Args:
            force_refresh: Force fetch from API even if already loaded

        Returns:
            int or None: The PSA customer ID, or None if no mapping exists

        Raises:
            RuntimeError: If customer was not initialized with a client reference

        Example:
            >>> customer = nc.get_customer_obj(237)
            >>> psa_id = customer.load_psa_customer_id()
            >>> print(f"CW ID: {psa_id}")
        """
        if not self._client:
            raise RuntimeError(
                "Cannot load PSA customer ID: Customer not initialized with client reference. "
                "Use nc.get_customer_obj() or pass client parameter to Customer.from_dict()"
            )

        if self._psa_customer_id is None or force_refresh:
            self._psa_customer_id = self._client.get_psa_customer_id(self.customerId)

        return self._psa_customer_id

    @property
    def psa_customer_id(self) -> Optional[int]:
        """
        Get the cached PSA customer ID, loading it if not already cached.

        Returns:
            int or None: The PSA customer ID, or None if no mapping exists

        Raises:
            RuntimeError: If customer was not initialized with a client reference

        Example:
            >>> customer = nc.get_customer_obj(237)
            >>> print(customer.psa_customer_id)  # Lazy loads on first access
        """
        if self._psa_customer_id is None and self._client:
            self.load_psa_customer_id()
        return self._psa_customer_id

    @property
    def has_psa_mapping(self) -> bool:
        """
        Check if PSA customer ID has been loaded.

        Returns:
            bool: True if PSA ID is loaded (even if None), False if not yet fetched
        """
        return self._psa_customer_id is not None

    @property
    def full_contact_name(self) -> str:
        """Get the full contact name."""
        parts = [self.contactFirstName, self.contactLastName]
        return " ".join(p for p in parts if p).strip()

    @property
    def full_address(self) -> str:
        """Get the formatted full address."""
        lines = []
        if self.street1:
            lines.append(self.street1)
        if self.street2:
            lines.append(self.street2)

        city_line = []
        if self.city:
            city_line.append(self.city)
        if self.stateProv:
            city_line.append(self.stateProv)
        if self.postalCode:
            city_line.append(self.postalCode)
        if city_line:
            lines.append(", ".join(city_line))

        if self.country:
            lines.append(self.country)

        return "\n".join(lines)