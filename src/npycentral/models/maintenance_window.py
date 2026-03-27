from dataclasses import dataclass
from typing import Optional
from datetime import datetime


_MAINTENANCE_WINDOW_KNOWN_FIELDS = {
    'windowId', 'windowName', 'startTime', 'endTime',
    'recurrence', 'isActive', 'affectedDeviceCount',
}


@dataclass
class MaintenanceWindow:
    """Represents a maintenance window configured on a device in N-Central."""
    windowId: Optional[int] = None
    windowName: Optional[str] = None
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    recurrence: Optional[str] = None
    isActive: Optional[bool] = None
    affectedDeviceCount: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'MaintenanceWindow':
        """Create a MaintenanceWindow from an API response dict, ignoring unknown fields."""
        filtered = {k: v for k, v in data.items() if k in _MAINTENANCE_WINDOW_KNOWN_FIELDS}
        return cls(**filtered)

    @property
    def start_datetime(self) -> Optional[datetime]:
        """Parse startTime as a datetime object."""
        if not self.startTime:
            return None
        try:
            return datetime.fromisoformat(self.startTime.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    @property
    def end_datetime(self) -> Optional[datetime]:
        """Parse endTime as a datetime object."""
        if not self.endTime:
            return None
        try:
            return datetime.fromisoformat(self.endTime.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
