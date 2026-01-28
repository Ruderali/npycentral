"""Customer and organization-related API methods."""
import logging
from typing import List, Optional, Dict, Any

from ..models.service_organization import ServiceOrganization

logger = logging.getLogger(__name__)


class CustomerMixin:
    """Customer and organization-related API methods."""

    def get_customers(
        self,
        so_id: Optional[int] = None,
        pagesize: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all customers, optionally filtered by service organization.

        Args:
            so_id: Service organization ID to filter by (default: uses base_so_id)
            pagesize: Number of results per page (default: 50)

        Returns:
            list: List of customer dictionaries

        Raises:
            APIError: If the API request fails
        """
        if so_id is None and self.base_so_id is not None:
            so_id = int(self.base_so_id)

        params = {"soId": so_id} if so_id else None
        logger.debug(f"Fetching customers (SO ID: {so_id})")
        return self.get_all("customers", params=params, pagesize=pagesize)

    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Get a specific customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            dict: Customer details

        Raises:
            NotFoundError: If customer is not found
            APIError: If the API request fails
        """
        logger.debug(f"Fetching customer {customer_id}")
        return self.get(f"customers/{customer_id}")

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
