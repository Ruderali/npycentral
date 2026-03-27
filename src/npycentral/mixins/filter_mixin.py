"""Device filter-related API methods."""
import logging
from typing import List, Optional
from cachetools import TTLCache

from ..models.device_filter import DeviceFilter

logger = logging.getLogger(__name__)


class FilterMixin:
    """Device filter-related API methods."""

    def _init_filter_cache(self):
        """Initialize filter cache if not already present."""
        if not hasattr(self, '_filter_cache'):
            self._filter_cache = TTLCache(maxsize=10, ttl=300)
            logger.debug("Initialized filter cache with TTL=300s")

    def clear_filter_cache(self):
        """Clear the filter cache."""
        if hasattr(self, '_filter_cache'):
            self._filter_cache.clear()
            logger.debug("Cleared filter cache")

    def get_filters(
        self,
        view_scope: str = "ALL",
        pagesize: int = 50,
        use_cache: bool = True,
    ) -> List[DeviceFilter]:
        """
        Get all device filters.

        Args:
            view_scope: Filter scope - "ALL" or "OWN_AND_USED" (default: "ALL")
            pagesize: Number of results per page (default: 50)
            use_cache: Whether to cache results (default: True — filters are static reference data)

        Returns:
            list: List of DeviceFilter objects

        Raises:
            APIError: If the API request fails
        """
        params = {"viewScope": view_scope}

        if not use_cache:
            logger.debug(f"Fetching device filters (scope: {view_scope}, no cache)")
            filters_data = self.get_all("device-filters", params=params, pagesize=pagesize)
            return [DeviceFilter.from_dict(f) for f in filters_data]

        self._init_filter_cache()
        cache_key = f"filters_{view_scope}"
        if cache_key not in self._filter_cache:
            logger.debug(f"Cache miss for {cache_key}, fetching from API")
            filters_data = self.get_all("device-filters", params=params, pagesize=pagesize)
            self._filter_cache[cache_key] = [DeviceFilter.from_dict(f) for f in filters_data]
        else:
            logger.debug(f"Cache hit for {cache_key}")
        return self._filter_cache[cache_key]

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
