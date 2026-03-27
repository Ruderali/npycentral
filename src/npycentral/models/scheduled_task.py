from dataclasses import dataclass
from typing import Optional


_SCHEDULED_TASK_KNOWN_FIELDS = {
    'taskId', 'taskName', 'taskType', 'status',
    'scheduledTime', 'lastRunTime', 'nextRunTime',
}


@dataclass
class ScheduledTask:
    """Represents a scheduled task on a device in N-Central."""
    taskId: Optional[int] = None
    taskName: Optional[str] = None
    taskType: Optional[str] = None
    status: Optional[str] = None
    scheduledTime: Optional[str] = None
    lastRunTime: Optional[str] = None
    nextRunTime: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledTask':
        """Create a ScheduledTask from an API response dict, ignoring unknown fields."""
        filtered = {k: v for k, v in data.items() if k in _SCHEDULED_TASK_KNOWN_FIELDS}
        if 'taskId' in filtered and filtered['taskId'] is not None:
            filtered['taskId'] = int(filtered['taskId'])
        return cls(**filtered)
