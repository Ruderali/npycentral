"""Customer and organization-related API methods with lazy-loaded caching."""
import logging
from typing import List, Optional, Dict, Any
from cachetools import TTLCache

from ..models.service_organization import ServiceOrganization
from ..models.customer import Customer
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class CustomerMixin:
    """Customer and organization-related API methods with lazy-loaded caching."""

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def _init_customer_cache(self):
        """Initialize customer cache if not already present."""
        if not hasattr(self, '_customer_cache'):
            self._customer_cache = TTLCache(maxsize=50, ttl=300)
            self._customer_cache_ttl = 300
            logger.debug("Initialized customer cache with TTL=300s")

    def set_customer_cache_ttl(self, ttl_seconds: int):
        """
        Set the TTL for customer cache.

        Args:
            ttl_seconds: Cache time-to-live in seconds
        """
        logger.info(f"Setting customer cache TTL to {ttl_seconds}s")
        self._customer_cache_ttl = ttl_seconds
        if hasattr(self, '_customer_cache'):
            self._customer_cache = TTLCache(maxsize=50, ttl=ttl_seconds)

    def clear_customer_cache(self, so_id: Optional[int] = None):
        """
        Clear customer cache for a specific SO or all caches.

        Args:
            so_id: Specific service org to clear, or None to clear all
        """
        if not hasattr(self, '_customer_cache'):
            return

        if so_id is None:
            logger.info("Clearing all customer cache")
            self._customer_cache.clear()
        else:
            cache_key = f"customers_{so_id}"
            self._customer_cache.pop(cache_key, None)
            logger.debug(f"Cleared customer cache for SO {so_id}")

    def _get_cached_customers(
        self,
        so_id: Optional[int] = None,
        pagesize: int = 50,
        use_cache: bool = True
    ) -> List[Customer]:
        """
        Get customers with caching support (lazy-loaded).

        Args:
            so_id: Optional service organization ID
            pagesize: Results per page
            use_cache: Whether to use cache

        Returns:
            list: Cached or fresh customer list as Customer objects
        """
        if not use_cache:
            return self._fetch_customers_fresh(so_id, pagesize)

        self._init_customer_cache()
        cache_key = f"customers_{so_id}"

        if cache_key not in self._customer_cache:
            logger.debug(f"Cache miss for {cache_key}, fetching from API")
            self._customer_cache[cache_key] = self._fetch_customers_fresh(so_id, pagesize)
        else:
            logger.debug(f"Cache hit for {cache_key}")

        return self._customer_cache[cache_key]

    def _fetch_customers_fresh(
        self,
        so_id: Optional[int] = None,
        pagesize: int = 50
    ) -> List[Customer]:
        """
        Fetch customers fresh from API without caching.

        Args:
            so_id: Optional service organization ID
            pagesize: Results per page

        Returns:
            list: List of Customer objects
        """
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)

        params = {"soId": so_id} if so_id else None
        logger.debug(f"Fetching customers (SO ID: {so_id}, pagesize={pagesize})")
        customers_data = self.get_all("customers", params=params, pagesize=pagesize)
        logger.info(f"Fetched {len(customers_data)} customers")
        return [Customer.from_dict(c, client=self) for c in customers_data]

    # ========================================================================
    # CORE CUSTOMER METHODS
    # ========================================================================

    def get_customers(
        self,
        so_id: Optional[int] = None,
        pagesize: int = 50,
        use_cache: bool = False
    ) -> List[Customer]:
        """
        Get all customers, optionally filtered by service organization.

        Args:
            so_id: Service organization ID to filter by (default: uses base_so_id)
            pagesize: Number of results per page (default: 50)
            use_cache: Whether to use cache (default: False)

        Returns:
            list: List of Customer objects

        Raises:
            APIError: If the API request fails

        Example:
            # Get all customers
            customers = nc.get_customers()

            # Get with caching enabled
            customers = nc.get_customers(use_cache=True)

            for c in customers:
                print(f"{c.customerName}: PSA ID = {c.psa_customer_id}")
        """
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)
        return self._get_cached_customers(so_id, pagesize, use_cache)

    def get_customer(
        self,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        so_id: Optional[int] = None,
        use_cache: bool = True
    ) -> Customer:
        """
        Get a specific customer by ID or name.

        Args:
            customer_id: Customer ID to fetch (takes priority over customer_name)
            customer_name: Customer name to search for (case-insensitive, partial match)
            so_id: Optional SO ID to narrow name search
            use_cache: Whether to use cache for lookups (default: True)

        Returns:
            Customer: Customer object with client reference for lazy-loading PSA ID

        Raises:
            ValueError: If neither customer_id nor customer_name provided
            NotFoundError: If customer is not found
            APIError: If the API request fails

        Example:
            # Get by ID
            customer = nc.get_customer(customer_id=237)

            # Get by name
            customer = nc.get_customer(customer_name="Xpress Freight")

            # Access PSA ID (lazy-loaded)
            print(customer.psa_customer_id)
        """
        if customer_id is None and customer_name is None:
            raise ValueError("Must provide either customer_id or customer_name")

        # If customer_name provided, use name lookup
        if customer_name is not None and customer_id is None:
            customer = self._find_customer_by_name(customer_name, so_id, use_cache)
            if customer is None:
                raise NotFoundError(f"Customer not found: {customer_name}")
            return customer

        # customer_id provided - check cache first
        if use_cache:
            self._init_customer_cache()
            for cache_key, customers in self._customer_cache.items():
                for customer in customers:
                    if customer.customerId == customer_id:
                        logger.debug(f"Found customer {customer_id} in cache ({cache_key})")
                        return customer

        # Not in cache, fetch from API
        logger.debug(f"Fetching customer {customer_id} from API")
        response = self.get(f"customers/{customer_id}")
        return Customer.from_dict(response, client=self)

    def create_customer(
        self,
        customer_data: Dict[str, Any],
        so_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new customer under a service organization.

        Args:
            customer_data: Customer data dictionary
            so_id: Service organization ID (default: uses base_so_id)

        Returns:
            dict: Created customer details

        Raises:
            APIError: If the API request fails
        """
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)

        logger.info(f"Creating customer under SO {so_id}")
        return self.post(f"service-orgs/{so_id}/customers", customer_data)

    def create_site(
        self,
        customer_id: int,
        site_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new site under a customer.

        Args:
            customer_id: Customer ID
            site_data: Site data dictionary

        Returns:
            dict: Created site details

        Raises:
            APIError: If the API request fails
        """
        logger.info(f"Creating site under customer {customer_id}")
        return self.post(f"customers/{customer_id}/sites", site_data)

    def get_service_orgs(self, pagesize: int = 50) -> List[ServiceOrganization]:
        """
        Get all service organizations.

        Args:
            pagesize: Number of results per page (default: 50)

        Returns:
            list: List of ServiceOrganization objects

        Raises:
            APIError: If the API request fails
        """
        logger.debug("Fetching service organizations")
        orgs_data = self.get_all("service-orgs", pagesize=pagesize)
        return [ServiceOrganization.from_dict(org) for org in orgs_data]

    def _find_customer_by_name(
        self,
        customer_name: str,
        so_id: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[Customer]:
        """
        Internal method to find a customer by name.

        Args:
            customer_name: Customer name to search for (case-insensitive, partial match)
            so_id: Optional SO ID to narrow search
            use_cache: Use cached customer list if available

        Returns:
            Customer or None: First matching customer, or None if not found
        """
        logger.debug(f"Searching for customer by name: '{customer_name}'")
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)

        customers = self._get_cached_customers(so_id, use_cache=use_cache)
        customer_name_lower = customer_name.lower()

        # Try exact match first
        for customer in customers:
            if customer.customerName.lower() == customer_name_lower:
                logger.debug(f"Found exact match: {customer.customerName}")
                return customer

        # Fall back to partial match
        for customer in customers:
            if customer_name_lower in customer.customerName.lower():
                logger.debug(f"Found partial match: {customer.customerName}")
                return customer

        logger.debug(f"No customer found matching '{customer_name}'")
        return None

    def find_customers_by_name(
        self,
        customer_name: str,
        so_id: Optional[int] = None,
        use_cache: bool = True
    ) -> List[Customer]:
        """
        Find all customers matching a name pattern.

        Args:
            customer_name: Customer name to search for (case-insensitive, partial match)
            so_id: Optional SO ID to narrow search
            use_cache: Use cached customer list if available (default: True)

        Returns:
            list: All matching customers

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Finding all customers matching: '{customer_name}'")
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)

        customers = self._get_cached_customers(so_id, use_cache=use_cache)
        customer_name_lower = customer_name.lower()

        matches = [c for c in customers if customer_name_lower in c.customerName.lower()]
        logger.debug(f"Found {len(matches)} customers matching '{customer_name}'")
        return matches

    # ========================================================================
    # PSA INTEGRATION
    # ========================================================================

    def get_psa_customer_id(self, customer_id: int) -> Optional[int]:
        """
        Get the PSA (ConnectWise/Autotask) customer ID for an N-Central customer.

        Args:
            customer_id: N-Central customer ID

        Returns:
            int or None: PSA customer ID, or None if no mapping exists

        Raises:
            APIError: If the API request fails

        Example:
            >>> psa_id = nc.get_psa_customer_id(237)
            >>> print(f"ConnectWise ID: {psa_id}")
        """
        logger.debug(f"Fetching PSA customer mapping for NC customer {customer_id}")
        try:
            response = self.get(f"standard-psa/customer-mapping/{customer_id}")
            if response and isinstance(response, list) and len(response) > 0:
                psa_id = response[0].get("psaCustomerId")
                logger.debug(f"Found PSA mapping: NC {customer_id} -> PSA {psa_id}")
                return psa_id
            logger.debug(f"No PSA mapping found for customer {customer_id}")
            return None
        except NotFoundError:
            logger.debug(f"No PSA mapping found for customer {customer_id}")
            return None

    def get_psa_customer_mapping(self, customer_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the full PSA customer mapping details for an N-Central customer.

        Args:
            customer_id: N-Central customer ID

        Returns:
            dict or None: Full PSA mapping with contactId, locationId, siteId, etc.

        Raises:
            APIError: If the API request fails

        Example:
            >>> mapping = nc.get_psa_customer_mapping(237)
            >>> print(mapping)
            {'contactId': -1, 'customerId': 237, 'psaCustomerId': 21215, ...}
        """
        logger.debug(f"Fetching full PSA customer mapping for NC customer {customer_id}")
        try:
            response = self.get(f"standard-psa/customer-mapping/{customer_id}")
            if response and isinstance(response, list) and len(response) > 0:
                return response[0]
            return None
        except NotFoundError:
            return None
