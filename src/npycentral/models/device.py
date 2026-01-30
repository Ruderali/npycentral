from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime
from zoneinfo import ZoneInfo
from .device_assets import DeviceAssets


@dataclass
class Device:
    deviceId: int
    uri: str
    remoteControlUri: Optional[str]
    sourceUri: Optional[str]
    longName: str
    deviceClass: str
    description: str
    isProbe: bool
    osId: str
    supportedOs: str
    discoveredName: str
    deviceClassLabel: str
    supportedOsLabel: str
    lastLoggedInUser: str
    stillLoggedIn: Optional[bool]
    licenseMode: str
    orgUnitId: int
    soId: int
    soName: str
    customerId: int
    customerName: str
    siteId: Optional[int]
    siteName: Optional[str]
    applianceId: int
    lastApplianceCheckinTime: Optional[str]
    timezone: ZoneInfo = ZoneInfo("UTC")  # Default to UTC if not provided
    assets: Optional[DeviceAssets] = None
    _client: Optional[Any] = None  # Store client reference for lazy loading
    
    @classmethod
    def from_dict(cls, data: dict, timezone: ZoneInfo = ZoneInfo("UTC"), 
                  client: Optional[Any] = None) -> 'Device':
        """
        Create a Device instance from a dictionary.
        
        Args:
            data: Dictionary containing device data
            timezone: ZoneInfo object for datetime operations (defaults to UTC)
            client: Optional NCentralClient reference for lazy-loading assets
        """
        # Add timezone and client to the data dict
        device_data = data.copy()
        device_data['timezone'] = timezone
        device_data['_client'] = client
        return cls(**device_data)
    
    @property
    def last_checkin_datetime(self) -> Optional[datetime]:
        """
        Parse the lastApplianceCheckinTime as a datetime object in the configured timezone.
        The API returns UTC timestamps, which are then converted to the instance's timezone.

        Returns:
            datetime: Timezone-aware datetime object, or None if lastApplianceCheckinTime is null
        """
        if self.lastApplianceCheckinTime is None:
            return None

        # Parse the timestamp - handle both 'Z' suffix and missing timezone
        dt = datetime.fromisoformat(self.lastApplianceCheckinTime.replace('Z', '+00:00'))

        # If the datetime is naive (no timezone info), treat it as UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        # Convert to the configured timezone
        return dt.astimezone(self.timezone)
    
    def load_assets(self, force_refresh: bool = False) -> DeviceAssets:
        """
        Lazy-load device assets from the API.
        
        This method allows you to fetch detailed device asset information (hardware,
        software, network adapters, etc.) on-demand without having to make a separate
        API call manually.
        
        Args:
            force_refresh: Force fetch from API even if assets are already loaded
            
        Returns:
            DeviceAssets: The loaded device assets
            
        Raises:
            RuntimeError: If device was not initialized with a client reference
            
        Example:
            >>> device = nc.get_device(12345)
            >>> assets = device.load_assets()
            >>> print(assets.manufacturer)
            >>> print(assets.model)
            >>> print(assets.total_memory_gb)
        """
        if not self._client:
            raise RuntimeError(
                "Cannot load assets: Device not initialized with client reference. "
                "Use nc.get_device() or pass client parameter to Device.from_dict()"
            )
        
        if self.assets is None or force_refresh:
            self.assets = self._client.get_device_assets(self.deviceId)
        
        return self.assets
    
    @property
    def has_assets(self) -> bool:
        """
        Check if device assets are currently loaded.
        
        Returns:
            bool: True if assets are loaded, False otherwise
            
        Example:
            >>> device = nc.get_device(12345)
            >>> print(device.has_assets)  # False
            >>> device.load_assets()
            >>> print(device.has_assets)  # True
        """
        return self.assets is not None
    
    def get_deep_link_url(self, base_url: str, method: str, 
                         ui_port: int = None,
                         username: str = None, password: str = None, 
                         language: str = "en") -> str:
        """
        Generate a deep-link URL for various N-Central device pages.
        
        Available methods:
        - deviceDetails: Device Properties Page
        - deviceService: Device Status Page  
        - deviceRC: Device Remote Control
        
        Args:
            base_url: N-Central server URL
            method: Deep link method (deviceDetails, deviceService, deviceRC)
            ui_port: N-Central UI port (if None, no port is appended to URL)
            username: N-Central username (optional)
            password: N-Central password (optional)
            language: Language code (default: "en")
            
        Returns:
            str: Deep-link URL
        """
        # Only add port if specified
        if ui_port:
            url = f"{base_url}:{ui_port}/deepLinkAction.do?method={method}"
        else:
            url = f"{base_url}/deepLinkAction.do?method={method}"
            
        url += f"&customerID={self.customerId}"
        url += f"&deviceID={self.deviceId}"
        url += f"&language={language}"
        
        if username:
            url += f"&username={username}"
        if password:
            url += f"&password={password}"
        
        return url
    
    def get_remote_control_url(self, base_url: str, ui_port: int = None,
                               username: str = None, password: str = None, 
                               language: str = "en") -> str:
        """
        Generate a deep-link URL for remote control access.
        Convenience method that calls get_deep_link_url with method='deviceRC'.
        """
        return self.get_deep_link_url(base_url, "deviceRC", ui_port, username, password, language)
    
    def get_overview_url(self, base_url: str, ui_port: int = None,
                         username: str = None, password: str = None,
                         language: str = "en") -> str:
        """Generate URL to device overview page."""
        return self.get_deep_link_url(base_url, "deviceOverview", ui_port, username, password, language)

    def get_details_url(self, base_url: str, ui_port: int = None,
                       username: str = None, password: str = None, 
                       language: str = "en") -> str:
        """Generate URL to device properties/details page."""
        return self.get_deep_link_url(base_url, "deviceDetails", ui_port, username, password, language)
    
    def get_status_url(self, base_url: str, ui_port: int = None,
                      username: str = None, password: str = None, 
                      language: str = "en") -> str:
        """Generate URL to device status/service monitoring page."""
        return self.get_deep_link_url(base_url, "deviceService", ui_port, username, password, language)