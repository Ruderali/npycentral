"""Device-related API methods with lazy-loaded caching."""
import logging
from typing import List, Optional, Union
from cachetools import TTLCache

from ..models import (
    Device,
    ActiveIssue,
    DeviceAssets,
    ServiceMonitoringStatus,
    ServiceMonitoringCollection
)
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class DeviceMixin:
    """Device-related API methods with lazy-loaded caching."""

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
        """Initialize device cache if not already present."""
        if not hasattr(self, '_device_cache'):
            # Cache key format: "devices_{filter_id}" or "devices_None" for all devices
            # TTL of 300 seconds (5 minutes) by default
            self._device_cache = TTLCache(maxsize=50, ttl=300)
            self._device_cache_ttl = 300  # Can be overridden
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
        pagesize: int = 50,
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

    # ========================================================================
    # CORE DEVICE METHODS
    # ========================================================================

    def get_devices(
        self,
        filter_id: Optional[int] = None,
        filter_name: Optional[str] = None,
        pagesize: int = 50,
        use_cache: bool = False,
        max_pages: Optional[int] = None
    ) -> List[Device]:
        """
        Get all devices with optional filtering and caching.

        Args:
            filter_id: Optional filter ID (takes priority over filter_name)
            filter_name: Optional filter name (resolved to ID automatically)
            pagesize: Results per page
            use_cache: Whether to use cache (default: False for backwards compatibility)
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            list: List of Device objects

        Raises:
            NotFoundError: If filter_name provided but not found
            APIError: If the API request fails

        Example:
            # Get all devices
            devices = nc.get_devices()

            # Get devices by filter name
            dcs = nc.get_devices(filter_name="Domain Controllers")

            # Get devices by filter ID
            dcs = nc.get_devices(filter_id=83)

            # Get first page only
            dcs = nc.get_devices(max_pages=1)
        """
        resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
        return self._get_cached_devices(resolved_filter_id, pagesize, use_cache, max_pages)

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
            # Get by ID
            device = nc.get_device(device_id=12345)

            # Get by name
            device = nc.get_device(device_name="DC01")

            # Get by name with filter
            device = nc.get_device(device_name="DC01", filter_name="Domain Controllers")
        """
        if device_id is None and device_name is None:
            raise ValueError("Must provide either device_id or device_name")

        # If device_name provided, use name lookup
        if device_name is not None and device_id is None:
            resolved_filter_id = self._resolve_filter_id(filter_id, filter_name)
            device = self._find_device_by_name(device_name, resolved_filter_id, use_cache)
            if device is None:
                raise NotFoundError(f"Device not found: {device_name}")
            return device

        # device_id provided - use ID lookup
        if use_cache:
            self._init_device_cache()
            # Check all cached device lists for this device
            for cache_key, devices in self._device_cache.items():
                for device in devices:
                    if device.deviceId == device_id:
                        logger.debug(f"Found device {device_id} in cache ({cache_key})")
                        return device

        # Not in cache or cache disabled, fetch from API
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
        devices = self._get_cached_devices(resolved_filter_id, use_cache=use_cache)
        matches = [device for device in devices if device.siteId == site_id]
        logger.debug(f"Found {len(matches)} devices for site {site_id}")
        return matches

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

        Raises:
            NotFoundError: If device is not found
            APIError: If the API request fails
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

        Raises:
            NotFoundError: If device is not found
            APIError: If the API request fails
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

        Raises:
            NotFoundError: If device is not found
            APIError: If the API request fails
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

    def get_active_issues_url(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        language: str = "en"
    ) -> str:
        """
        Generate URL to active issues view.

        Args:
            username: N-Central username (optional)
            password: N-Central password (optional)
            language: Language code (default: "en")

        Returns:
            str: Deep-link URL to active issues
        """
        if self.ui_port:
            url = f"{self.base_url}:{self.ui_port}/deepLinkAction.do?method=activeissues"
        else:
            url = f"{self.base_url}/deepLinkAction.do?method=activeissues"

        url += f"&language={language}"

        if username:
            url += f"&username={username}"
        if password:
            url += f"&password={password}"

        return url

    # ========================================================================
    # DEVICE MONITORING AND ISSUES
    # ========================================================================

    def get_active_issues(self, org_unit_id: int, pagesize: int = 50) -> List[ActiveIssue]:
        """
        Get active issues for an organization unit.

        Args:
            org_unit_id: Organization unit ID
            pagesize: Results per page

        Returns:
            list: List of ActiveIssue objects

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Fetching active issues for org unit {org_unit_id}")
        issues_data = self.get_all(f"org-units/{org_unit_id}/active-issues", pagesize=pagesize)
        logger.info(f"Found {len(issues_data)} active issues")
        return [ActiveIssue.from_dict(issue) for issue in issues_data]

    def get_device_active_issues(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[ActiveIssue]:
        """
        Get active issues for a specific device.

        Args:
            device_id: Device ID to check (takes priority)
            device_name: Device name to check

        Returns:
            list: List of active issues for the device

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching active issues for device {resolved_device_id}")
        device = self.get_device(device_id=resolved_device_id)
        all_issues = self.get_active_issues(device.customerId)
        device_issues = [issue for issue in all_issues if issue.deviceId == resolved_device_id]
        logger.debug(f"Found {len(device_issues)} active issues for device {resolved_device_id}")
        return device_issues

    def get_device_assets(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> DeviceAssets:
        """
        Get detailed hardware/software assets for a device.

        Fetches comprehensive inventory including hardware specs, installed software,
        services, patches, shares, and system configuration.

        Args:
            device_id: Device ID to get assets for (takes priority)
            device_name: Device name to get assets for

        Returns:
            DeviceAssets: Complete device asset inventory

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails

        Example:
            # By ID
            assets = nc.get_device_assets(device_id=12345)

            # By name
            assets = nc.get_device_assets(device_name="DC01")

            print(f"Device: {assets.device_name}")
            print(f"Memory: {assets.total_memory_gb:.2f} GB")
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching device assets for device {resolved_device_id}")
        response = self.get(f"devices/{resolved_device_id}/assets")
        return DeviceAssets.from_dict(response)

    def get_device_hardware_summary(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> dict:
        """
        Get a concise hardware summary for a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            dict: Hardware summary with key specs

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Getting hardware summary for device {resolved_device_id}")
        assets = self.get_device_assets(device_id=resolved_device_id)

        return {
            "device_name": assets.device_name,
            "manufacturer": assets.manufacturer,
            "model": assets.model,
            "operating_system": assets.operating_system,
            "processor": assets.processor_name,
            "total_cores": assets.total_cores,
            "memory_gb": assets.total_memory_gb,
            "ip_address": assets.ip_address,
            "physical_drives": [
                {
                    "model": drive.modelnumber,
                    "capacity_gb": drive.capacity_gb,
                    "serial": drive.serialnumber
                }
                for drive in assets.data._extra.physicaldrive
            ]
        }

    def get_device_software_inventory(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> dict:
        """
        Get installed software and patch status for a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            dict: Software inventory with applications and patches

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Getting software inventory for device {resolved_device_id}")
        assets = self.get_device_assets(device_id=resolved_device_id)

        installed_apps = assets.get_installed_applications()
        installed_patches = assets.get_installed_patches()
        pending_patches = assets.get_pending_patches()

        return {
            "device_name": assets.device_name,
            "os": assets.operating_system,
            "applications": [
                {
                    "name": app.displayname,
                    "version": app.version,
                    "publisher": app.publisher,
                    "installed_date": app.installation_datetime
                }
                for app in installed_apps
            ],
            "patches": {
                "installed_count": len(installed_patches),
                "pending_count": len(pending_patches),
                "pending_titles": [p.title for p in pending_patches]
            }
        }

    def get_device_service_monitoring_status(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> ServiceMonitoringCollection:
        """
        Get service monitoring status for a device.

        Returns typed ServiceMonitoringCollection with helper methods.

        Args:
            device_id: Device ID to check (takes priority)
            device_name: Device name to check

        Returns:
            ServiceMonitoringCollection: Collection of monitoring statuses

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching service monitoring status for device {resolved_device_id}")
        response = self.get(f"devices/{resolved_device_id}/service-monitor-status")
        if isinstance(response, dict) and "data" in response:
            data = response.get("data", [])
        else:
            data = response if isinstance(response, list) else []

        return ServiceMonitoringCollection.from_list(data)

    def get_device_disk_status(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[ServiceMonitoringStatus]:
        """
        Get disk monitoring status for all volumes on a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            list: List of disk monitoring statuses

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails

        Example:
            disks = nc.get_device_disk_status(device_name="DC01")
            for disk in disks:
                print(f"{disk.volume_letter}: {disk.stateStatus}")
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching disk status for device {resolved_device_id}")
        monitoring = self.get_device_service_monitoring_status(device_id=resolved_device_id)
        return monitoring.get_disk_monitors()

    def get_device_monitoring_summary(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> dict:
        """
        Get summary of all monitoring statuses for a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            dict: Summary with counts and issues

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Getting monitoring summary for device {resolved_device_id}")
        monitoring = self.get_device_service_monitoring_status(device_id=resolved_device_id)
        summary = monitoring.summary()

        # Add device info
        device = self.get_device(device_id=resolved_device_id)
        summary['device_name'] = device.longName
        summary['device_id'] = resolved_device_id

        # Add issue details
        issues = monitoring.get_issues()
        summary['issues'] = [
            {
                'module': issue.moduleName,
                'status': issue.stateStatus,
                'ident': issue.taskIdent,
                'last_scan': issue.last_scan_datetime
            }
            for issue in issues
        ]

        return summary

    def check_device_disk_health(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> dict:
        """
        Check disk health status for a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            dict: Disk health report

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Checking disk health for device {resolved_device_id}")
        device = self.get_device(device_id=resolved_device_id)
        disks = self.get_device_disk_status(device_id=resolved_device_id)

        healthy = all(disk.is_normal for disk in disks)
        warnings = [disk for disk in disks if disk.is_warning]
        failures = [disk for disk in disks if disk.is_failed]

        logger.info(f"Device {resolved_device_id} disk health: {len(warnings)} warnings, {len(failures)} failures")
        return {
            'device_name': device.longName,
            'device_id': resolved_device_id,
            'healthy': healthy,
            'disk_count': len(disks),
            'volumes': [
                {
                    'volume': disk.volume_letter,
                    'status': disk.stateStatus,
                    'last_scan': disk.last_scan_datetime
                }
                for disk in disks
            ],
            'warnings': [
                {
                    'volume': disk.volume_letter,
                    'status': disk.stateStatus,
                    'last_scan': disk.last_scan_datetime
                }
                for disk in warnings
            ],
            'failures': [
                {
                    'volume': disk.volume_letter,
                    'status': disk.stateStatus,
                    'last_scan': disk.last_scan_datetime
                }
                for disk in failures
            ]
        }
