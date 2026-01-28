"""Device filter-related API methods."""
import logging
from typing import List, Optional

from ..models.device_filter import DeviceFilter

logger = logging.getLogger(__name__)


class FilterMixin:
    """Device filter-related API methods."""

    def get_filters(
        self,
        view_scope: str = "ALL",
        pagesize: int = 50
    ) -> List[DeviceFilter]:
        """
        Get all device filters.

        Args:
            view_scope: Filter scope - "ALL" or "OWN_AND_USED" (default: "ALL")
            pagesize: Number of results per page (default: 50)

        Returns:
            list: List of DeviceFilter objects

        Raises:
            APIError: If the API request fails
        """
        params = {"viewScope": view_scope}
        logger.debug(f"Fetching device filters (scope: {view_scope})")
        filters_data = self.get_all("device-filters", params=params, pagesize=pagesize)
        return [DeviceFilter.from_dict(f) for f in filters_data]

    def get_filter_by_id(self, filter_id: str) -> Optional[DeviceFilter]:
        """
        Get a specific filter by ID.

        Args:
            filter_id: The filter ID to find

        Returns:
            DeviceFilter if found, None otherwise

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Searching for filter with ID: {filter_id}")
        filters = self.get_filters()
        for f in filters:
            if f.filterId == filter_id:
                return f
        return None

    def get_filter_by_name(self, filter_name: str) -> Optional[DeviceFilter]:
        """
        Get a specific filter by name.

        Args:
            filter_name: The filter name to find (case-sensitive)

        Returns:
            DeviceFilter if found, None otherwise

        Raises:
            APIError: If the API request fails
        """
        logger.debug(f"Searching for filter with name: {filter_name}")
        filters = self.get_filters()
        for f in filters:
            if f.filterName == filter_name:
                return f
        return None
