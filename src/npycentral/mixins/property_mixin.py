"""Custom properties API methods."""
import logging
from typing import List, Optional

from ..models.custom_property import CustomProperty

logger = logging.getLogger(__name__)


class PropertyMixin:
    """Custom properties API methods."""

    def get_device_custom_properties(self, device_id: int) -> List[CustomProperty]:
        """
        Get all custom properties for a device.

        Args:
            device_id: Device ID

        Returns:
            list: List of CustomProperty objects

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Fetching custom properties for device {device_id}")
        response = self.get(f"devices/{device_id}/custom-properties")
        if isinstance(response, dict) and "data" in response:
            properties_data = response.get("data", [])
        else:
            properties_data = response if isinstance(response, list) else []

        return [CustomProperty.from_dict(prop) for prop in properties_data]

    def get_device_custom_property(
        self,
        device_id: int,
        property_id: int
    ) -> Optional[CustomProperty]:
        """
        Get a specific custom property for a device.

        Args:
            device_id: Device ID
            property_id: Property ID

        Returns:
            CustomProperty or None: The custom property if found

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Fetching custom property {property_id} for device {device_id}")
        response = self.get(f"devices/{device_id}/custom-properties/{property_id}")
        if isinstance(response, dict) and "data" in response:
            prop_data = response.get("data")
        else:
            prop_data = response if response else None

        return CustomProperty.from_dict(prop_data) if prop_data else None

    def get_device_custom_property_by_name(
        self,
        device_id: int,
        property_name: str
    ) -> Optional[CustomProperty]:
        """
        Get a custom property by name for a device.

        Args:
            device_id: Device ID
            property_name: Property name to search for

        Returns:
            CustomProperty or None: The custom property if found

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Searching for custom property '{property_name}' on device {device_id}")
        properties = self.get_device_custom_properties(device_id)
        for prop in properties:
            if prop.propertyName == property_name:
                return prop
        return None

    def update_device_custom_property(
        self,
        device_id: int,
        property_id: int,
        value: str
    ) -> Optional[CustomProperty]:
        """
        Update a custom property value for a device.

        Args:
            device_id: Device ID
            property_id: Property ID
            value: New property value

        Returns:
            CustomProperty or None: Updated custom property

        Raises:
            APIError: If the API request fails
        """
        logger.info(f"Updating custom property {property_id} on device {device_id}")
        response = self.put(
            f"devices/{device_id}/custom-properties/{property_id}",
            {"value": value}
        )
        if isinstance(response, dict) and "data" in response:
            prop_data = response.get("data")
        else:
            prop_data = response

        return CustomProperty.from_dict(prop_data) if prop_data else None
