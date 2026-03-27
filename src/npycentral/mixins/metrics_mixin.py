"""Device performance metrics, assets, and scheduled task methods."""
import logging
from typing import List, Optional

from ..models import DeviceAssets
from ..models.appliance_task import ApplianceTask, CpuUsage, DiskUsage, MemoryUsage
from ..models.scheduled_task import ScheduledTask
from ..exceptions import NotFoundError

logger = logging.getLogger(__name__)


class MetricsMixin:
    """Device performance metrics, assets, and scheduled task methods."""

    # ========================================================================
    # DEVICE ASSETS
    # ========================================================================

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
            assets = nc.get_device_assets(device_id=12345)
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

    # ========================================================================
    # APPLIANCE TASKS AND PERFORMANCE METRICS
    # ========================================================================

    def get_appliance_task(self, task_id: int) -> ApplianceTask:
        """
        Get detailed scan data for an appliance task.

        Calls GET /api/appliance-tasks/{taskId} and returns a generic
        ApplianceTask containing all reported metrics via serviceDetails.

        Args:
            task_id: The task ID (from ServiceMonitoringStatus.taskId)

        Returns:
            ApplianceTask: Parsed task data with service details

        Raises:
            NotFoundError: If task not found
            APIError: If the API request fails
        """
        logger.debug(f"Fetching appliance task {task_id}")
        response = self.get(f"appliance-tasks/{task_id}")
        return ApplianceTask.from_dict(response)

    def get_device_disk_usage(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[DiskUsage]:
        """
        Get disk usage metrics (total, used, free, %) for all monitored volumes.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            list: List of DiskUsage objects, one per monitored volume

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails

        Example:
            disks = nc.get_device_disk_usage(device_name="DC01")
            for disk in disks:
                print(f"{disk.volume}: {disk.free_gb:.1f} GB free ({disk.usage_percent}% used)")
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching disk usage for device {resolved_device_id}")
        monitoring = self.get_device_service_monitoring_status(device_id=resolved_device_id)
        disk_monitors = monitoring.get_disk_monitors()

        results = []
        for monitor in disk_monitors:
            task = self.get_appliance_task(monitor.taskId)
            results.append(DiskUsage(
                volume=monitor.volume_letter or "Unknown",
                total_kb=task.get_detail_value("disk_total") or 0,
                used_kb=task.get_detail_value("disk_used") or 0,
                free_kb=task.get_detail_value("disk_free") or 0,
                usage_percent=task.get_detail_value("disk_usage") or 0,
                state=task.state,
                scan_time=task.scanTime,
            ))

        logger.info(f"Retrieved disk usage for {len(results)} volumes on device {resolved_device_id}")
        return results

    def get_device_cpu_usage(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> CpuUsage:
        """
        Get CPU usage metrics including top 5 processes for a device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            CpuUsage: CPU usage percentage and top processes

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device or CPU monitor not found
            APIError: If the API request fails

        Example:
            cpu = nc.get_device_cpu_usage(device_name="DC01")
            print(f"CPU: {cpu.usage_percent}%")
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching CPU usage for device {resolved_device_id}")
        monitoring = self.get_device_service_monitoring_status(device_id=resolved_device_id)
        cpu_monitors = monitoring.get_cpu_monitors()

        if not cpu_monitors:
            raise NotFoundError(f"No CPU monitor found for device {resolved_device_id}")

        task = self.get_appliance_task(cpu_monitors[0].taskId)
        logger.info(f"Retrieved CPU usage for device {resolved_device_id}")
        return CpuUsage.from_appliance_task(task)

    def get_device_memory_usage(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> MemoryUsage:
        """
        Get memory usage metrics (physical + virtual) including top 5 processes.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            MemoryUsage: Physical and virtual memory metrics with top processes

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device or memory monitor not found
            APIError: If the API request fails

        Example:
            mem = nc.get_device_memory_usage(device_name="DC01")
            print(f"Physical: {mem.physical_used_gb:.1f}/{mem.physical_total_gb:.1f} GB")
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching memory usage for device {resolved_device_id}")
        monitoring = self.get_device_service_monitoring_status(device_id=resolved_device_id)
        mem_monitors = monitoring.get_memory_monitors()

        if not mem_monitors:
            raise NotFoundError(f"No memory monitor found for device {resolved_device_id}")

        task = self.get_appliance_task(mem_monitors[0].taskId)
        logger.info(f"Retrieved memory usage for device {resolved_device_id}")
        return MemoryUsage.from_appliance_task(task)

    # ========================================================================
    # SCHEDULED TASKS
    # ========================================================================

    def get_device_scheduled_tasks(
        self,
        device_id: Optional[int] = None,
        device_name: Optional[str] = None
    ) -> List[ScheduledTask]:
        """
        Get scheduled tasks for a specific device.

        Args:
            device_id: Device ID (takes priority)
            device_name: Device name

        Returns:
            list: List of ScheduledTask objects

        Raises:
            ValueError: If neither device_id nor device_name provided
            NotFoundError: If device not found
            APIError: If the API request fails
        """
        resolved_device_id = self._resolve_device_id(device_id, device_name)
        logger.debug(f"Fetching scheduled tasks for device {resolved_device_id}")
        data = self.get_all(f"devices/{resolved_device_id}/scheduled-tasks")
        return [ScheduledTask.from_dict(t) for t in data]
