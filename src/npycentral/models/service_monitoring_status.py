from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ServiceMonitoringStatus:
    """Represents a service monitor in N-Central."""
    taskId: int
    serviceId: int
    timeToStale: int
    taskNote: str
    taskIdent: Optional[str]
    stateStatus: str  # "Normal", "Warning", "Failed"
    lastUpdate: Optional[str]
    lastDataId: Optional[int]
    createdOn: Optional[str]
    moduleName: str  # e.g., "Disk", "CPU", "Memory", "Connectivity"
    serviceItemId: int
    lastScanTime: str
    isManagedTask: bool
    transitionTime: str
    applianceId: int
    applianceName: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceMonitoringStatus':
        """Create a ServiceMonitoringStatus instance from a dictionary."""
        return cls(**data)
    
    @property
    def last_scan_datetime(self) -> Optional[datetime]:
        """Parse lastScanTime as a datetime object."""
        if not self.lastScanTime:
            return None
        try:
            return datetime.strptime(self.lastScanTime, '%Y-%m-%d %H:%M:%S.%f %z')
        except (ValueError, AttributeError):
            return None
    
    @property
    def transition_datetime(self) -> Optional[datetime]:
        """Parse transitionTime as a datetime object."""
        if not self.transitionTime:
            return None
        try:
            return datetime.strptime(self.transitionTime, '%Y-%m-%d %H:%M:%S.%f')
        except (ValueError, AttributeError):
            return None
    
    @property
    def is_normal(self) -> bool:
        """Check if status is Normal."""
        return self.stateStatus == "Normal"
    
    @property
    def is_warning(self) -> bool:
        """Check if status is Warning."""
        return self.stateStatus == "Warning"
    
    @property
    def is_failed(self) -> bool:
        """Check if status is Failed."""
        return self.stateStatus == "Failed"
    
    @property
    def is_disk_monitor(self) -> bool:
        """Check if this is a disk monitoring task."""
        return self.moduleName == "Disk"
    
    @property
    def is_memory_monitor(self) -> bool:
        """Check if this is a memory monitoring task."""
        return self.moduleName == "Memory"
    
    @property
    def is_cpu_monitor(self) -> bool:
        """Check if this is a CPU monitoring task."""
        return self.moduleName == "CPU"
    
    @property
    def volume_letter(self) -> Optional[str]:
        """
        Get the volume letter if this is a disk monitor.
        Returns "C:", "D:", etc. or None if not a disk monitor.
        """
        if self.is_disk_monitor and self.taskIdent:
            return self.taskIdent
        return None
    
    def __str__(self) -> str:
        """String representation showing key monitoring details."""
        ident = f" ({self.taskIdent})" if self.taskIdent else ""
        return f"[{self.stateStatus}] {self.moduleName}{ident} - Last: {self.last_scan_datetime}"


@dataclass
class ServiceMonitoringCollection:
    """Collection of service monitoring statuses with helper methods."""
    statuses: list[ServiceMonitoringStatus]
    
    @classmethod
    def from_list(cls, data: list[dict]) -> 'ServiceMonitoringCollection':
        """Create collection from list of dicts."""
        statuses = [ServiceMonitoringStatus.from_dict(item) for item in data]
        return cls(statuses=statuses)
    
    def get_disk_monitors(self) -> list[ServiceMonitoringStatus]:
        """Get all disk monitoring statuses."""
        return [s for s in self.statuses if s.is_disk_monitor]
    
    def get_memory_monitors(self) -> list[ServiceMonitoringStatus]:
        """Get all memory monitoring statuses."""
        return [s for s in self.statuses if s.is_memory_monitor]
    
    def get_cpu_monitors(self) -> list[ServiceMonitoringStatus]:
        """Get all CPU monitoring statuses."""
        return [s for s in self.statuses if s.is_cpu_monitor]
    
    def get_by_module(self, module_name: str) -> list[ServiceMonitoringStatus]:
        """Get all monitors for a specific module."""
        return [s for s in self.statuses if s.moduleName == module_name]
    
    def get_failed(self) -> list[ServiceMonitoringStatus]:
        """Get all failed monitors."""
        return [s for s in self.statuses if s.is_failed]
    
    def get_warnings(self) -> list[ServiceMonitoringStatus]:
        """Get all warning monitors."""
        return [s for s in self.statuses if s.is_warning]
    
    def get_issues(self) -> list[ServiceMonitoringStatus]:
        """Get all monitors with warnings or failures."""
        return [s for s in self.statuses if s.is_warning or s.is_failed]
    
    def get_disk_by_volume(self, volume: str) -> Optional[ServiceMonitoringStatus]:
        """
        Get disk monitor for specific volume.
        
        Args:
            volume: Volume letter like "C:" or "D:"
            
        Returns:
            ServiceMonitoringStatus or None if not found
        """
        for s in self.get_disk_monitors():
            if s.volume_letter == volume:
                return s
        return None
    
    def summary(self) -> dict:
        """Get summary statistics."""
        return {
            "total": len(self.statuses),
            "normal": len([s for s in self.statuses if s.is_normal]),
            "warning": len([s for s in self.statuses if s.is_warning]),
            "failed": len([s for s in self.statuses if s.is_failed]),
            "disk_monitors": len(self.get_disk_monitors()),
            "memory_monitors": len(self.get_memory_monitors()),
            "cpu_monitors": len(self.get_cpu_monitors())
        }