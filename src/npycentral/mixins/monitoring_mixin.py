"""Device monitoring, active issues, and maintenance window methods."""
import logging
from typing import List, Optional

from ..models import ActiveIssue, ServiceMonitoringStatus, ServiceMonitoringCollection
from ..models.maintenance_window import MaintenanceWindow
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)

# Map severity string to notificationState values
_SEVERITY_MAP = {
    "WARNING": [3, 4],
    "CRITICAL": [5],
    "FAILED": [6],
    "DISCONNECTED": [7],
    "DISABLED": [8],
}


class MonitoringMixin:
    """Device monitoring, active issues, and maintenance window methods."""

    # ========================================================================
    # ACTIVE ISSUES
    # ========================================================================

    def get_active_issues(
        self,
        org_unit_id: Optional[int] = None,
        customer_id: Optional[int] = None,
        customer_name: Optional[str] = None,
        site_id: Optional[int] = None,
        so_id: Optional[int] = None,
        severity: Optional[str] = None,
        pagesize: int = 50,
    ) -> List[ActiveIssue]:
        """
        Get active issues for an organization unit, customer, site, or service org.

        N-Central orgUnitId equals customerId for customers and siteId for sites,
        so any of those IDs can be used to scope the query.

        Args:
            org_unit_id: Organization unit ID (takes priority over other ID args)
            customer_id: Customer ID — used directly as org_unit_id
            customer_name: Customer name — resolved to customer_id automatically
            site_id: Site ID — used directly as org_unit_id
            so_id: Service org ID — fetches issues across all customers in the SO (expensive)
            severity: Filter by severity string: "WARNING", "CRITICAL", "FAILED", "DISCONNECTED"
            pagesize: Results per page

        Returns:
            list: List of ActiveIssue objects

        Raises:
            ValueError: If no scope argument is provided
            NotFoundError: If customer_name is provided but not found
            APIError: If the API request fails

        Example:
            # By customer ID
            issues = nc.get_active_issues(customer_id=237)

            # By customer name, only critical
            issues = nc.get_active_issues(customer_name="Acme Corp", severity="CRITICAL")

            # By site
            issues = nc.get_active_issues(site_id=99)
        """
        # Resolve to org_unit_id
        if org_unit_id is not None:
            resolved_id = org_unit_id
        elif customer_id is not None:
            resolved_id = customer_id
        elif customer_name is not None:
            customer = self._find_customer_by_name(customer_name)
            if customer is None:
                raise NotFoundError(f"Customer not found: {customer_name}")
            resolved_id = customer.customerId
        elif site_id is not None:
            resolved_id = site_id
        elif so_id is not None:
            # Fetch across all customers in the SO — potentially expensive
            logger.warning(
                f"Fetching active issues across all customers in SO {so_id} — this may be slow"
            )
            customers = self._get_cached_customers(so_id, pagesize=pagesize, use_cache=True)
            all_issues = []
            for customer in customers:
                issues = self._fetch_active_issues(customer.customerId, pagesize)
                all_issues.extend(issues)
            return self._filter_by_severity(all_issues, severity)
        else:
            raise ValueError(
                "Must provide one of: org_unit_id, customer_id, customer_name, site_id, so_id"
            )

        issues = self._fetch_active_issues(resolved_id, pagesize)
        return self._filter_by_severity(issues, severity)

    def _fetch_active_issues(self, org_unit_id: int, pagesize: int = 50) -> List[ActiveIssue]:
        """Fetch active issues from the API for a single org unit."""
        logger.debug(f"Fetching active issues for org unit {org_unit_id}")
        issues_data = self.get_all(f"org-units/{org_unit_id}/active-issues", pagesize=pagesize)
        logger.info(f"Found {len(issues_data)} active issues for org unit {org_unit_id}")
        return [ActiveIssue.from_dict(issue) for issue in issues_data]

    def _filter_by_severity(
        self,
        issues: List[ActiveIssue],
        severity: Optional[str]
    ) -> List[ActiveIssue]:
        """Apply optional severity filter to a list of issues."""
        if severity is None:
            return issues
        severity_upper = severity.upper()
        if severity_upper not in _SEVERITY_MAP:
            raise ValueError(
                f"Invalid severity '{severity}'. Valid values: {list(_SEVERITY_MAP.keys())}"
            )
        valid_states = _SEVERITY_MAP[severity_upper]
        return [i for i in issues if i.notificationState in valid_states]

    def get_device_active_issues(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[ActiveIssue]:
        """
        Get active issues for a specific device.

        Note: The N-Central API has no per-device active-issues endpoint. This method
        fetches all active issues for the device's customer and filters client-side,
        so cost scales with the total number of issues across that customer.

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
        all_issues = self._fetch_active_issues(device.customerId)
        device_issues = [issue for issue in all_issues if issue.deviceId == resolved_device_id]
        logger.debug(f"Found {len(device_issues)} active issues for device {resolved_device_id}")
        return device_issues

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
    # SERVICE MONITORING STATUS
    # ========================================================================

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

        device = self.get_device(device_id=resolved_device_id)
        summary['device_name'] = device.longName
        summary['device_id'] = resolved_device_id

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

    # ========================================================================
    # MAINTENANCE WINDOWS
    # ========================================================================

    def get_device_maintenance_windows(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[MaintenanceWindow]:
        """
        Get maintenance windows for a specific device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            list: List of MaintenanceWindow objects

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching maintenance windows for device {resolved_device_id}")
        data = self.get_all(f"devices/{resolved_device_id}/maintenance-windows")
        return [MaintenanceWindow.from_dict(w) for w in data]
