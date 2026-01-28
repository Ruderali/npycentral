from dataclasses import dataclass
from typing import Optional, List


@dataclass
class CustomProperty:
    propertyId: int
    propertyName: str
    propertyType: str  # e.g., "ENUMERATED", "TEXT", "DATE", "URL"
    value: Optional[str]
    enumeratedValueList: Optional[List[str]] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomProperty':
        """Create a CustomProperty instance from a dictionary."""
        return cls(
            propertyId=data.get("propertyId"),
            propertyName=data.get("propertyName"),
            propertyType=data.get("propertyType"),
            value=data.get("value"),
            enumeratedValueList=data.get("enumeratedValueList")
        )