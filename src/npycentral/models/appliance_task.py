from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ApplianceTaskThreshold:
    """Threshold definition for an appliance task metric."""
    state: str
    lowValue: int
    highValue: int

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplianceTaskThreshold':
        return cls(**data)


@dataclass
class ApplianceTaskServiceDetail:
    """Individual metric/detail from an appliance task scan."""
    scanDetailId: int
    detailName: str
    description: str
    detailValue: str
    state: str
    monitoringType: str
    thresholds: list[ApplianceTaskThreshold]

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplianceTaskServiceDetail':
        detail_data = data.copy()
        detail_data['thresholds'] = [
            ApplianceTaskThreshold.from_dict(t) for t in data.get('thresholds', [])
        ]
        return cls(**detail_data)

    @property
    def numeric_value(self) -> Optional[float]:
        """Parse detailValue as a float, or None if not numeric."""
        try:
            return float(self.detailValue)
        except (ValueError, TypeError):
            return None

    def __str__(self) -> str:
        return f"{self.detailName}: {self.detailValue} ({self.description})"


@dataclass
class ApplianceTask:
    """Represents the response from GET /api/appliance-tasks/{taskId}.

    This is a generic container for any appliance task's scan data,
    including all reported metrics via serviceDetails.
    """
    scanTime: str
    state: str
    errorMessage: str
    serviceDetails: list[ApplianceTaskServiceDetail]

    @classmethod
    def from_dict(cls, data: dict) -> 'ApplianceTask':
        task_data = data.copy()
        task_data['serviceDetails'] = [
            ApplianceTaskServiceDetail.from_dict(d)
            for d in data.get('serviceDetails', [])
        ]
        return cls(**task_data)

    def get_detail(self, detail_name: str) -> Optional[ApplianceTaskServiceDetail]:
        """Get a service detail by its detailName."""
        for detail in self.serviceDetails:
            if detail.detailName == detail_name:
                return detail
        return None

    def get_detail_value(self, detail_name: str) -> Optional[float]:
        """Get the numeric value of a service detail by name."""
        detail = self.get_detail(detail_name)
        if detail:
            return detail.numeric_value
        return None

    def __str__(self) -> str:
        details = ", ".join(str(d) for d in self.serviceDetails)
        return f"[{self.state}] scanned {self.scanTime} — {details}"


@dataclass
class DiskUsage:
    """Parsed disk usage metrics for a single volume.

    Values from the API are in KB despite descriptions saying "(GB)".
    Convenience properties convert to MB/GB.
    """
    volume: str
    total_kb: float
    used_kb: float
    free_kb: float
    usage_percent: float
    state: str
    scan_time: str

    @property
    def total_gb(self) -> float:
        return self.total_kb / 1024 / 1024

    @property
    def used_gb(self) -> float:
        return self.used_kb / 1024 / 1024

    @property
    def free_gb(self) -> float:
        return self.free_kb / 1024 / 1024

    @property
    def total_mb(self) -> float:
        return self.total_kb / 1024

    @property
    def used_mb(self) -> float:
        return self.used_kb / 1024

    @property
    def free_mb(self) -> float:
        return self.free_kb / 1024

    def __str__(self) -> str:
        return (
            f"{self.volume} [{self.state}] "
            f"{self.used_gb:.1f}/{self.total_gb:.1f} GB "
            f"({self.usage_percent:.0f}% used, {self.free_gb:.1f} GB free) "
            f"@ {self.scan_time}"
        )


# ============================================================================
# CPU Usage
# ============================================================================

@dataclass
class TopCpuProcess:
    """A top-5 CPU process from the CPU appliance task."""
    name: str
    pid: int
    user: str
    cpu_usage_percent: float

    def __str__(self) -> str:
        return f"{self.name} (PID {self.pid}) {self.cpu_usage_percent}% — {self.user}"


@dataclass
class CpuUsage:
    """Parsed CPU usage metrics from the CPU appliance task.

    Detail names: cpu_usage, top5_cpu_process{1-5}, top5_pid_process{1-5},
    top5_user_process{1-5}, top5_cpu_usage{1-5}.
    """
    usage_percent: float
    top_processes: List[TopCpuProcess]
    state: str
    scan_time: str

    @classmethod
    def from_appliance_task(cls, task: 'ApplianceTask') -> 'CpuUsage':
        """Build CpuUsage from a CPU ApplianceTask."""
        processes = []
        for i in range(1, 6):
            name = task.get_detail(f"top5_cpu_process{i}")
            if not name or not name.detailValue:
                break
            processes.append(TopCpuProcess(
                name=name.detailValue,
                pid=int(task.get_detail_value(f"top5_pid_process{i}") or 0),
                user=(task.get_detail(f"top5_user_process{i}") or name).detailValue
                     if task.get_detail(f"top5_user_process{i}") else "",
                cpu_usage_percent=task.get_detail_value(f"top5_cpu_usage{i}") or 0,
            ))

        return cls(
            usage_percent=task.get_detail_value("cpu_usage") or 0,
            top_processes=processes,
            state=task.state,
            scan_time=task.scanTime,
        )

    def __str__(self) -> str:
        return f"CPU [{self.state}] {self.usage_percent:.0f}% — {len(self.top_processes)} top processes @ {self.scan_time}"


# ============================================================================
# Memory Usage
# ============================================================================

@dataclass
class TopMemoryProcess:
    """A top-5 memory process from the Memory appliance task."""
    name: str
    pid: int
    user: str
    physical_kb: float
    virtual_kb: float

    @property
    def physical_mb(self) -> float:
        return self.physical_kb / 1024

    @property
    def virtual_mb(self) -> float:
        return self.virtual_kb / 1024

    def __str__(self) -> str:
        return f"{self.name} (PID {self.pid}) {self.physical_mb:.0f} MB phys — {self.user}"


@dataclass
class MemoryUsage:
    """Parsed memory usage metrics from the Memory appliance task.

    Values from the API are in KB despite descriptions saying "(GB)"/"(MB)".
    Convenience properties convert to MB/GB.

    Detail names: memory_physicaltotal, memory_physicalused, memory_physicalfree,
    memory_physicalusage, memory_virtualtotal, memory_virtualused, memory_virtualfree,
    memory_virtualusage, memory_process{1-5}, memory_process_pid{1-5},
    memory_process_user{1-5}, memory_physical{1-5}, memory_virtual{1-5}.
    """
    physical_total_kb: float
    physical_used_kb: float
    physical_free_kb: float
    physical_usage_percent: float
    virtual_total_kb: float
    virtual_used_kb: float
    virtual_free_kb: float
    virtual_usage_percent: float
    top_processes: List[TopMemoryProcess]
    state: str
    scan_time: str

    # Physical convenience properties
    @property
    def physical_total_gb(self) -> float:
        return self.physical_total_kb / 1024 / 1024

    @property
    def physical_used_gb(self) -> float:
        return self.physical_used_kb / 1024 / 1024

    @property
    def physical_free_gb(self) -> float:
        return self.physical_free_kb / 1024 / 1024

    @property
    def physical_total_mb(self) -> float:
        return self.physical_total_kb / 1024

    @property
    def physical_used_mb(self) -> float:
        return self.physical_used_kb / 1024

    @property
    def physical_free_mb(self) -> float:
        return self.physical_free_kb / 1024

    # Virtual convenience properties
    @property
    def virtual_total_gb(self) -> float:
        return self.virtual_total_kb / 1024 / 1024

    @property
    def virtual_used_gb(self) -> float:
        return self.virtual_used_kb / 1024 / 1024

    @property
    def virtual_free_gb(self) -> float:
        return self.virtual_free_kb / 1024 / 1024

    @property
    def virtual_total_mb(self) -> float:
        return self.virtual_total_kb / 1024

    @property
    def virtual_used_mb(self) -> float:
        return self.virtual_used_kb / 1024

    @property
    def virtual_free_mb(self) -> float:
        return self.virtual_free_kb / 1024

    @classmethod
    def from_appliance_task(cls, task: 'ApplianceTask') -> 'MemoryUsage':
        """Build MemoryUsage from a Memory ApplianceTask."""
        processes = []
        for i in range(1, 6):
            name = task.get_detail(f"memory_process{i}")
            if not name or not name.detailValue:
                break
            processes.append(TopMemoryProcess(
                name=name.detailValue,
                pid=int(task.get_detail_value(f"memory_process_pid{i}") or 0),
                user=(task.get_detail(f"memory_process_user{i}") or name).detailValue
                     if task.get_detail(f"memory_process_user{i}") else "",
                physical_kb=task.get_detail_value(f"memory_physical{i}") or 0,
                virtual_kb=task.get_detail_value(f"memory_virtual{i}") or 0,
            ))

        return cls(
            physical_total_kb=task.get_detail_value("memory_physicaltotal") or 0,
            physical_used_kb=task.get_detail_value("memory_physicalused") or 0,
            physical_free_kb=task.get_detail_value("memory_physicalfree") or 0,
            physical_usage_percent=task.get_detail_value("memory_physicalusage") or 0,
            virtual_total_kb=task.get_detail_value("memory_virtualtotal") or 0,
            virtual_used_kb=task.get_detail_value("memory_virtualused") or 0,
            virtual_free_kb=task.get_detail_value("memory_virtualfree") or 0,
            virtual_usage_percent=task.get_detail_value("memory_virtualusage") or 0,
            top_processes=processes,
            state=task.state,
            scan_time=task.scanTime,
        )

    def __str__(self) -> str:
        return (
            f"Memory [{self.state}] "
            f"Physical: {self.physical_used_gb:.1f}/{self.physical_total_gb:.1f} GB "
            f"({self.physical_usage_percent:.0f}%), "
            f"Virtual: {self.virtual_used_gb:.1f}/{self.virtual_total_gb:.1f} GB "
            f"({self.virtual_usage_percent:.0f}%) "
            f"@ {self.scan_time}"
        )
