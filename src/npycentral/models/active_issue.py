from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class IssueExtra:
    """Extended information about an active issue."""
    numberOfAcknowledgedNotification: Optional[int]
    avdUpdateServerEnabled: bool
    licenseMode: str
    psaIntegrationDisabled: bool
    avdProtectionEnabled: bool
    remoteControllable: bool
    reactiveSupported: bool
    partOfNotification: bool
    remoteControlState: Optional[str]
    acknowledgedBy: str
    avdVersion: str
    deviceName: str
    ticketCreationInProgress: Optional[bool]
    transitionTime: str
    integrationStatuses: Optional[dict]
    lwtEdrStatus: str
    patchManagementEnabled: bool
    backupManagerProfile: str
    mspBackupProfile: str
    securityManagerProfile: str
    notificationAcknowledgmentInProgress: bool
    taskIdent: str
    microsoftPatchManagementEnabled: bool
    deviceClassValue: Optional[str]
    backupManagerVersion: str
    securityManagerVersion: str
    remoteControlConnected: Optional[bool]
    monitoringDisabled: bool
    numberOfActiveNotification: int
    psaIntegrationExists: bool
    lwtEdrEnabled: bool
    mspBackupVersion: str
    thirdPartyPatchManagementEnabled: bool
    probe: bool
    reactiveEnabled: bool
    netPathEnabled: bool
    deviceClassLabel: Optional[str]
    mspBackupEnabled: bool
    port: str
    diskEncryptionEnabled: bool
    customerTree: List[str]
    securityManagerEnabled: bool
    psaTicketDetails: str
    soCustomerID: int
    maintenanceWindowEnabled: bool
    backupManagerEnabled: bool
    patchManagementProfile: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IssueExtra':
        """Create an IssueExtra instance from a dictionary."""
        return cls(**data)
    
    @property
    def transition_datetime(self) -> Optional[datetime]:
        """Parse transitionTime as a datetime object."""
        if not self.transitionTime:
            return None
        try:
            return datetime.fromisoformat(self.transitionTime.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


@dataclass
class ActiveIssue:
    """Represents an active issue/alert on a device."""
    orgUnitId: int
    deviceId: int
    notificationState: int
    serviceId: int
    serviceName: str
    serviceType: str
    taskId: int
    serviceItemId: int
    _extra: Optional[IssueExtra] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ActiveIssue':
        """Create an ActiveIssue instance from a dictionary."""
        extra_data = data.pop('_extra', None)
        extra = IssueExtra.from_dict(extra_data) if extra_data else None
        
        return cls(
            orgUnitId=data.get('orgUnitId'),
            deviceId=data.get('deviceId'),
            notificationState=data.get('notificationState'),
            serviceId=data.get('serviceId'),
            serviceName=data.get('serviceName'),
            serviceType=data.get('serviceType'),
            taskId=data.get('taskId'),
            serviceItemId=data.get('serviceItemId'),
            _extra=extra
        )
    
    @property
    def remote_control_available(self) -> bool:
        """Check if remote control is available for this device."""
        if not self._extra:
            return False
        return self._extra.remoteControllable and self._extra.remoteControlState is not None
    
    @property
    def remote_control_connected(self) -> bool:
        """Check if remote control is currently connected."""
        if not self._extra:
            return False
        return (self._extra.remoteControllable and 
                self._extra.remoteControlState == "connected")
    
    @property
    def remote_control_state(self) -> Optional[str]:
        """Get the remote control state (safe accessor for _extra.remoteControlState)."""
        return self._extra.remoteControlState if self._extra else None
    
    @property
    def device_name(self) -> Optional[str]:
        """Get device name from extra data."""
        return self._extra.deviceName if self._extra else None
    
    @property
    def customer_tree(self) -> List[str]:
        """Get customer hierarchy tree."""
        return self._extra.customerTree if self._extra else []
    
    @property
    def transition_datetime(self) -> Optional[datetime]:
        """Get the transition time as a datetime object."""
        return self._extra.transition_datetime if self._extra else None
    
    def __str__(self) -> str:
        """String representation showing key issue details."""
        state_labels = {
            1: "OK",
            2: "NORMAL",
            3: "WARNING",
            4: "WARNING",
            5: "CRITICAL",
            6: "FAILED"
        }
        state = state_labels.get(self.notificationState, f"STATE_{self.notificationState}")
        return f"[{state}] {self.serviceName} on {self.device_name or f'Device {self.deviceId}'}"