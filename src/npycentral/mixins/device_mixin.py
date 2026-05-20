"""Core device discovery, caching, and lifecycle methods."""
import logging
from typing import List, Optional, Union
from cachetools import TTLCache

from ..models import Device
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class DeviceMixin:
    """Core device discovery, caching, and lifecycle methods."""

    # ========================================================================
    # HELPER METHODS FOR RESOLVING NAMES TO IDS
    # ========================================================================

    def _resolve_filter_id(
        self,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None
    ) -> Optional[int]:
        """
        Resolve filter_name to filter_id if provided.

        Args:
            filter_id: Direct filter ID (takes priority)
            filter_name: Filter name to look up

        Returns:
            Resolved filter ID or None

        Raises:
            NotFoundError: If filter_name provided but not found
        """
        if filter_id is not None:
            return filter_id
        if filter_name is not None:
            device_filter = self.get_filter_by_name(filter_name)
            if device_filter is None:
                raise NotFoundError(f"Filter not found: {filter_name}")
            return int(device_filter.filterId)
        return None

    def _resolve_device_id(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None
    ) -> int:
        """
        Resolve device_name to device_id if provided.

        Args:
            device_id: Direct device ID (takes priority)
            device_name: Device name to look up
            filter_id: Optional filter ID for name lookup
            filter_name: Optional filter name for name lookup

        Returns:
            Resolved device ID

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device_name provided but not found
        """
        if device_id is not None:
            return device_id
        if device_name is not None:
            resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
            device = self._find_device_by_name(device_name, resolved_filter_id)
            if device is None:
                raise NotFoundError(f"Device not found: {device_name}")
            return device.deviceId
        raise ValueError("Must provide either device_id or device_name")

    def _find_device_by_name(
        self,
        device_name: str,
        filter_id: Optional[int] = None,
        use_cache: bool = True
    ) -> Optional[Device]:
        """
        Internal method to find a device by name.

        Args:
            device_name: Device name to search for (case-insensitive, partial match)
            filter_id: Optional filter ID to narrow search
            use_cache: Use cached device list if available

        Returns:
            Device or None: First matching device, or None if not found
        """
        logger.debug(f"Searching for device by name: '{device_name}'")
        devices = self._get_cached_devices(filter_id, use_cache=use_cache)
        device_name_lower = device_name.lower()

        # Try exact match first
        for device in devices:
            if device.longName.lower() == device_name_lower:
                logger.debug(f"Found exact match: {device.longName}")
                return device

        # Fall back to partial match
        for device in devices:
            if device_name_lower in device.longName.lower():
                logger.debug(f"Found partial match: {device.longName}")
                return device

        logger.debug(f"No device found matching '{device_name}'")
        return None

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def _init_device_cache(self):
        """Initialize device cache if not already present.

        Warning: TTLCache is not thread-safe. This is fine for the common pattern of
        populating the cache single-threaded then fanning out reads, but if you share
        a client across threads in a long-running parallel workload (longer than the
        TTL), threads can race on a cache miss. In that case either call
        get_devices() with use_cache=False, or wrap cache access in a lock.
        """
        if not hasattr(self, '_device_cache'):
            self._device_cache = TTLCache(maxsize=50, ttl=300)
            self._device_cache_ttl = 300
            logger.debug("Initialized device cache with TTL=300s")

    def set_device_cache_ttl(self, ttl_seconds: int):
        """
        Set the TTL for device cache.

        Args:
            ttl_seconds: Cache time-to-live in seconds
        """
        logger.info(f"Setting device cache TTL to {ttl_seconds}s")
        self._device_cache_ttl = ttl_seconds
        if hasattr(self, '_device_cache'):
            self._device_cache = TTLCache(maxsize=50, ttl=ttl_seconds)

    def clear_device_cache(self, filter_id: Optional[int] = None):
        """
        Clear device cache for a specific filter or all caches.

        Args:
            filter_id: Specific filter to clear, or None to clear all
        """
        if not hasattr(self, '_device_cache'):
            return

        if filter_id is None:
            logger.info("Clearing all device cache")
            self._device_cache.clear()
        else:
            cache_key = f"devices_{filter_id}"
            self._device_cache.pop(cache_key, None)
            logger.debug(f"Cleared device cache for filter {filter_id}")

    def _get_cached_devices(
        self,
        filter_id: Optional[int] = None,
        pagesize: int = 1000,
        use_cache: bool = True,
        max_pages: Optional[int] = None
    ) -> List[Device]:
        """
        Get devices with caching support (lazy-loaded).

        Args:
            filter_id: Optional filter ID
            pagesize: Results per page
            use_cache: Whether to use cache
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            list: Cached or fresh device list

        Raises:
            APIError: If the API request fails
        """
        if not use_cache:
            return self._fetch_devices_fresh(filter_id, pagesize, max_pages)

        self._init_device_cache()
        cache_key = f"devices_{filter_id}"

        if cache_key not in self._device_cache:
            logger.debug(f"Cache miss for {cache_key}, fetching from API")
            self._device_cache[cache_key] = self._fetch_devices_fresh(filter_id, pagesize, max_pages)
        else:
            logger.debug(f"Cache hit for {cache_key}")

        return self._device_cache[cache_key]

    def _fetch_devices_fresh(
        self,
        filter_id: Optional[int] = None,
        pagesize: int = 50,
        max_pages: Optional[int] = None
    ) -> List[Device]:
        """
        Fetch devices fresh from API without caching.

        Args:
            filter_id: Optional filter ID
            pagesize: Results per page
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            list: List of Device objects

        Raises:
            APIError: If the API request fails
        """
        params = {"filterId": filter_id} if filter_id else None
        logger.debug(f"Fetching devices (filter_id={filter_id}, pagesize={pagesize}, max_pages={max_pages})")
        devices_data = self.get_all("devices", params=params, pagesize=pagesize, max_pages=max_pages)
        logger.info(f"Fetched {len(devices_data)} devices")
        return [Device.from_dict(device, timezone=self.default_timezone, client=self)
                for device in devices_data]

    def _fetch_devices_for_org_unit(
        self,
        org_unit_id: int,
        pagesize: int = 50,
        max_pages: Optional[int] = None
    ) -> List[Device]:
        """
        Fetch devices scoped to a specific org unit (customer or site) from the API.

        Uses GET /api/org-units/{orgUnitId}/devices which is server-side scoped,
        avoiding the need to fetch all devices and filter client-side.

        Args:
            org_unit_id: Org unit ID (customerId or siteId — both are org units)
            pagesize: Results per page
            max_pages: Maximum pages to fetch

        Returns:
            list: List of Device objects for that org unit
        """
        logger.debug(f"Fetching devices for org unit {org_unit_id}")
        devices_data = self.get_all(
            f"org-units/{org_unit_id}/devices",
            pagesize=pagesize,
            max_pages=max_pages
        )
        logger.info(f"Fetched {len(devices_data)} devices for org unit {org_unit_id}")
        return [Device.from_dict(device, timezone=self.default_timezone, client=self)
                for device in devices_data]

    def _get_cached_devices_for_org_unit(
        self,
        org_unit_id: int,
        pagesize: int = 50,
        use_cache: bool = True,
        max_pages: Optional[int] = None
    ) -> List[Device]:
        """
        Get devices scoped to an org unit, with caching support.

        Cache key: "devices_orgunit_{org_unit_id}"
        """
        if not use_cache:
            return self._fetch_devices_for_org_unit(org_unit_id, pagesize, max_pages)

        self._init_device_cache()
        cache_key = f"devices_orgunit_{org_unit_id}"

        if cache_key not in self._device_cache:
            logger.debug(f"Cache miss for {cache_key}, fetching from API")
            self._device_cache[cache_key] = self._fetch_devices_for_org_unit(
                org_unit_id, pagesize, max_pages
            )
        else:
            logger.debug(f"Cache hit for {cache_key}")

        return self._device_cache[cache_key]

    # ========================================================================
    # CORE DEVICE METHODS
    # ========================================================================

    def get_devices(
        self,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        site_id: Optional[int] = None,
        device_class: Optional[str] = None,
        os_type: Optional[str] = None,
        pagesize: int = 50,
        use_cache: bool = False,
        max_pages: Optional[int] = None,
    ) -> List[Device]:
        """
        Get devices with optional server-side filter and client-side attribute filters.

        The N-Central REST API only supports server-side filtering by filterId.
        All other parameters (customer_id, site_id, device_class, os_type) are
        applied as client-side filters on the fetched device list.

        Args:
            filter_id: N-Central filter ID (server-side, takes priority over filter_name)
            filter_name: N-Central filter name (resolved to ID automatically)
            customer_id: Only return devices belonging to this customer (client-side)
            customer_name: Resolve customer by name, then filter (client-side)
            site_id: Only return devices at this site (client-side)
            device_class: Filter by device class label, e.g. "Server", "Workstation" (client-side,
                          case-insensitive substring match on deviceClass or deviceClassLabel)
            os_type: Filter by OS, e.g. "Windows", "Linux", "Mac" (client-side,
                     case-insensitive substring match on supportedOs or supportedOsLabel)
            pagesize: Results per page for the initial API fetch
            use_cache: Whether to use the device cache (default: False)
            max_pages: Maximum pages to fetch from the API (None for all)

        Returns:
            list: List of Device objects matching all specified filters

        Raises:
            NotFoundError: If filter_name or customer_name provided but not found
            APIError: If the API request fails

        Example:
            # All servers for a customer
            servers = nc.get_devices(customer_name="Acme Corp", device_class="Server")

            # Windows devices at a specific site
            devices = nc.get_devices(site_id=99, os_type="Windows")

            # Scoped fetch using an N-Central filter
            dcs = nc.get_devices(filter_name="Domain Controllers")
        """
        # Resolve customer_name → customer_id if needed
        if customer_name is not None and customer_id is None:
            customer = self._find_customer_by_name(customer_name)
            if customer is None:
                raise NotFoundError(f"Customer not found: {customer_name}")
            customer_id = customer.customerId

        resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)

        # --- Fetch strategy ---
        # When no filter_id is set and a customer/site scope is given, use the
        # org-units/{id}/devices endpoint for a server-side scoped fetch.
        # This avoids pulling all devices across the whole environment.
        #
        # When filter_id is set, use GET /devices?filterId=... (N-Central filter
        # takes precedence) and apply any customer/site scope client-side afterward.
        if resolved_filter_id is None and (customer_id is not None or site_id is not None):
            # site_id is more specific than customer_id — prefer it when both given
            org_unit_id = site_id if site_id is not None else customer_id
            devices = self._get_cached_devices_for_org_unit(
                org_unit_id, pagesize, use_cache, max_pages
            )
            # If both were provided, ensure devices match the customer too
            if site_id is not None and customer_id is not None:
                devices = [d for d in devices if d.customerId == customer_id]
        else:
            devices = self._get_cached_devices(resolved_filter_id, pagesize, use_cache, max_pages)
            # Apply any customer/site scope as client-side filters
            if customer_id is not None:
                devices = [d for d in devices if d.customerId == customer_id]
            if site_id is not None:
                devices = [d for d in devices if d.siteId == site_id]

        # Apply remaining client-side attribute filters
        if device_class is not None:
            dc_lower = device_class.lower()
            devices = [
                d for d in devices
                if dc_lower in d.deviceClass.lower() or dc_lower in d.deviceClassLabel.lower()
            ]
        if os_type is not None:
            os_lower = os_type.lower()
            devices = [
                d for d in devices
                if os_lower in d.supportedOs.lower() or os_lower in d.supportedOsLabel.lower()
            ]

        return devices

    def get_device(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Device:
        """
        Get a specific device by ID or name.

        Args:
            device_id: Device ID to fetch (takes priority over device_name)
            device_name: Device name to search for (case-insensitive, partial match)
            filter_id: Optional filter ID to narrow name search
            filter_name: Optional filter name to narrow name search
            use_cache: Whether to use cache (default: True for name lookups)

        Returns:
            Device: Device object with client reference for lazy-loading assets

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device is not found
            APIError: If the API request fails

        Example:
            device = nc.get_device(device_id=12345)
            device = nc.get_device(device_name="DC01")
        """
        if device_id is None and device_name is None:
            raise ValueError("Must provide either device_id or device_name")

        if device_name is not None and device_id is None:
            resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
            device = self._find_device_by_name(device_name, resolved_filter_id, use_cache)
            if device is None:
                raise NotFoundError(f"Device not found: {device_name}")
            return device

        if use_cache:
            self._init_device_cache()
            for cache_key, devices in self._device_cache.items():
                for device in devices:
                    if device.deviceId == device_id:
                        logger.debug(f"Found device {device_id} in cache ({cache_key})")
                        return device

        logger.debug(f"Fetching device {device_id} from API")
        response = self.get(f"devices/{device_id}")
        device_data = response.get("data", response) if isinstance(response, dict) else response
        return Device.from_dict(device_data, timezone=self.default_timezone, client=self)

    def find_devices_by_name(
        self,
        device_name: str,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Device]:
        """
        Find all devices matching a name pattern.

        Args:
            device_name: Device name to search for (case-insensitive, partial match)
            filter_id: Optional filter ID to narrow search (takes priority)
            filter_name: Optional filter name to narrow search
            use_cache: Use cached device list if available (default: True)

        Returns:
            list: All matching devices

        Raises:
            NotFoundError: If filter_name provided but not found
            APIError: If the API request fails
        """
        logger.debug(f"Finding all devices matching: '{device_name}'")
        resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
        devices = self._get_cached_devices(resolved_filter_id, use_cache=use_cache)
        device_name_lower = device_name.lower()

        matches = [device for device in devices
                   if device_name_lower in device.longName.lower()]
        logger.debug(f"Found {len(matches)} devices matching '{device_name}'")
        return matches

    def find_devices_by_customer(
        self,
        customer_id: int,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Device]:
        """
        Find all devices for a specific customer.

        Args:
            customer_id: Customer ID to filter by
            filter_id: Optional filter ID to narrow search (takes priority)
            filter_name: Optional filter name to narrow search
            use_cache: Use cached device list if available (default: True)

        Returns:
            list: All devices for the customer

        Raises:
            NotFoundError: If filter_name provided but not found
            APIError: If the API request fails
        """
        logger.debug(f"Finding devices for customer {customer_id}")
        resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
        if resolved_filter_id is None:
            return self._get_cached_devices_for_org_unit(customer_id, use_cache=use_cache)
        devices = self._get_cached_devices(resolved_filter_id, use_cache=use_cache)
        matches = [device for device in devices if device.customerId == customer_id]
        logger.debug(f"Found {len(matches)} devices for customer {customer_id}")
        return matches

    def find_devices_by_site(
        self,
        site_id: int,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Device]:
        """
        Find all devices for a specific site.

        Args:
            site_id: Site ID to filter by
            filter_id: Optional filter ID to narrow search (takes priority)
            filter_name: Optional filter name to narrow search
            use_cache: Use cached device list if available (default: True)

        Returns:
            list: All devices for the site

        Raises:
            NotFoundError: If filter_name provided but not found
            APIError: If the API request fails
        """
        logger.debug(f"Finding devices for site {site_id}")
        resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
        if resolved_filter_id is None:
            return self._get_cached_devices_for_org_unit(site_id, use_cache=use_cache)
        devices = self._get_cached_devices(resolved_filter_id, use_cache=use_cache)
        matches = [device for device in devices if device.siteId == site_id]
        logger.debug(f"Found {len(matches)} devices for site {site_id}")
        return matches

    # ========================================================================
    # DEVICE COUNT HELPERS
    # ========================================================================

    def get_customer_device_count(self, customer_id: int) -> int:
        """
        Get the total device count for a customer without fetching all device objects.

        Uses the org-units/{orgUnitId}/devices endpoint with a single-item page,
        reading the totalItems field from the pagination metadata.

        Args:
            customer_id: Customer ID (equals orgUnitId in N-Central)

        Returns:
            int: Total number of devices for the customer

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Fetching device count for customer {customer_id}")
        response = self.get(
            f"org-units/{customer_id}/devices",
            params={"pageSize": 1, "pageNumber": 1}
        )
        count = self._extract_total_items(response)
        logger.debug(f"Customer {customer_id} has {count} devices")
        return count

    def get_filter_device_count(self, filter_id: int) -> int:
        """
        Get the total device count matching a filter without fetching all device objects.

        Args:
            filter_id: N-Central filter ID

        Returns:
            int: Total number of devices matching the filter

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Fetching device count for filter {filter_id}")
        response = self.get(
            "devices",
            params={"filterId": filter_id, "pageSize": 1, "pageNumber": 1}
        )
        count = self._extract_total_items(response)
        logger.debug(f"Filter {filter_id} matches {count} devices")
        return count

    def _extract_total_items(self, response: dict) -> int:
        """Extract total item count from a paginated API response."""
        if not isinstance(response, dict):
            return 0
        # N-Central pagination metadata may use different key names
        for key in ("totalItems", "totalCount", "total", "count"):
            if key in response:
                return int(response[key])
        # Fallback: count items in data if pagination key not found
        data = response.get("data", [])
        return len(data) if isinstance(data, list) else 0

    # ========================================================================
    # DEEP LINK URL METHODS
    # ========================================================================

    def get_device_overview_url(
        self,
        device: Union[int, Device],
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> str:
        """
        Generate a device overview page URL.

        Args:
            device: Device ID or Device object
            username: N-Central username (optional)
            password: N-Central password (optional)

        Returns:
            str: Deep-link URL to device overview
        """
        if isinstance(device, int):
            device = self.get_device(device_id=device)
        return device.get_overview_url(self.base_url, self.ui_port, username, password)

    def get_device_details_url(
        self,
        device: Union[int, Device],
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> str:
        """
        Generate a device details page URL.

        Args:
            device: Device ID or Device object
            username: N-Central username (optional)
            password: N-Central password (optional)

        Returns:
            str: Deep-link URL to device details
        """
        if isinstance(device, int):
            device = self.get_device(device_id=device)
        return device.get_details_url(self.base_url, self.ui_port, username, password)

    def get_device_remote_control_url(
        self,
        device: Union[int, Device],
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> str:
        """
        Generate a remote control deep-link URL for a device.

        Args:
            device: Device ID or Device object
            username: N-Central username (optional)
            password: N-Central password (optional)

        Returns:
            str: Deep-link URL for remote control
        """
        if isinstance(device, int):
            device = self.get_device(device_id=device)
        return device.get_remote_control_url(self.base_url, self.ui_port, username, password)

    def get_dashboard_url(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        language: str = "en"
    ) -> str:
        """
        Generate URL to default N-Central dashboard.

        Args:
            username: N-Central username (optional)
            password: N-Central password (optional)
            language: Language code (default: "en")

        Returns:
            str: Deep-link URL to dashboard
        """
        if self.ui_port:
            url = f"{self.base_url}:{self.ui_port}/deepLinkAction.do?method=defaultDashboard"
        else:
            url = f"{self.base_url}/deepLinkAction.do?method=defaultDashboard"

        url += f"&language={language}"

        if username:
            url += f"&username={username}"
        if password:
            url += f"&password={password}"

        return url

    # ========================================================================
    # DEVICE LIFECYCLE
    # ========================================================================

    def delete_device(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None,
        remove_agents: bool = False
    ) -> bool:
        """
        Delete a device from N-Central.

        Args:
            device_id: Device ID to delete (takes priority over device_name)
            device_name: Device name to delete (resolved via cache)
            remove_agents: If True, also remove agents from the device

        Returns:
            bool: True on success

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device_name provided but not found
            APIError: If the API request fails

        Example:
            nc.delete_device(device_id=12345)
            nc.delete_device(device_name="DC01", remove_agents=True)
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.info(f"Deleting device {resolved_device_id} (remove_agents={remove_agents})")
        params = {"removeAgents": "true"} if remove_agents else None
        self.delete(f"devices/{resolved_device_id}", params=params)
        self.clear_device_cache()
        return True
