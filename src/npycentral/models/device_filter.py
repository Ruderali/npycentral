from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceFilter:
    """Represents a device filter in N-Central."""

    filterId: str
    filterName: str
    description: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceFilter':
        """Create a DeviceFilter instance from a dictionary."""
        return cls(
            filterId=data.get("filterId", ""),
            filterName=data.get("filterName", ""),
            description=data.get("description"),
        )
