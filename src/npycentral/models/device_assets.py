from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


# ============================================================================
# USB Device
# ============================================================================
@dataclass
class USBDevice:
    _index: int
    caption: str
    manufacturer: str
    status: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'USBDevice':
        return cls(**data)


# ============================================================================
# OS Features
# ============================================================================
@dataclass
class OSFeature:
    _index: int
    pkey: str
    pvalue: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OSFeature':
        return cls(**data)


# ============================================================================
# Memory
# ============================================================================
@dataclass
class Memory:
    _index: int
    serialnumber: str
    location: str
    type: str
    partnumber: str
    speed: Optional[str]
    manufacturer: str
    capacity: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Memory':
        return cls(**data)


# ============================================================================
# Operating System (Detailed)
# ============================================================================
@dataclass
class OSDetailed:
    licensetype: str
    installdate: str
    serialnumber: str
    publisher: str
    csdversion: Optional[str]
    lastbootuptime: str
    supportedos: str
    licensekey: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OSDetailed':
        return cls(**data)
    
    @property
    def install_datetime(self) -> datetime:
        """Parse installdate as datetime object."""
        return datetime.strptime(self.installdate, '%Y-%m-%d %H:%M:%S')
    
    @property
    def last_boot_datetime(self) -> datetime:
        """Parse lastbootuptime as datetime object."""
        return datetime.strptime(self.lastbootuptime, '%Y-%m-%d %H:%M:%S.%f')


# ============================================================================
# Media Access Device
# ============================================================================
@dataclass
class MediaAccessDevice:
    _index: int
    mediatype: str
    uniqueid: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MediaAccessDevice':
        return cls(**data)


# ============================================================================
# Folder Share
# ============================================================================
@dataclass
class FolderShare:
    _index: int
    path: str
    sharename: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FolderShare':
        return cls(**data)


# ============================================================================
# Printer
# ============================================================================
@dataclass
class Printer:
    _index: int
    path: str
    port: str
    name: str
    systemdefault: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Printer':
        return cls(**data)
    
    @property
    def is_default(self) -> bool:
        """Check if this is the system default printer."""
        return self.systemdefault.lower() == 'true'


# ============================================================================
# Motherboard
# ============================================================================
@dataclass
class Motherboard:
    product: str
    serialnumber: str
    biosversion: str
    version: str
    manufacturer: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Motherboard':
        return cls(**data)


# ============================================================================
# Physical Drive
# ============================================================================
@dataclass
class PhysicalDrive:
    _index: int
    serialnumber: str
    modelnumber: str
    capacity: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhysicalDrive':
        return cls(**data)
    
    @property
    def capacity_gb(self) -> float:
        """Convert capacity from bytes to GB."""
        return int(self.capacity) / (1024**3)
    
    @property
    def capacity_tb(self) -> float:
        """Convert capacity from bytes to TB."""
        return int(self.capacity) / (1024**4)


# ============================================================================
# Processor (Detailed)
# ============================================================================
@dataclass
class ProcessorDetailed:
    maxclockspeed: str
    cpuid: str
    vendor: Optional[str]
    description: str
    architecture: Optional[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessorDetailed':
        return cls(**data)


# ============================================================================
# Video Controller
# ============================================================================
@dataclass
class VideoController:
    _index: int
    name: str
    videocontrollerid: str
    description: str
    adapterram: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VideoController':
        return cls(**data)
    
    @property
    def adapter_ram_mb(self) -> float:
        """Convert adapter RAM from bytes to MB."""
        return int(self.adapterram) / (1024**2)


# ============================================================================
# Patch
# ============================================================================
@dataclass
class Patch:
    _index: int
    installationresult: str
    installeddate: Optional[str]
    title: str
    category: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Patch':
        return cls(**data)
    
    @property
    def is_installed(self) -> bool:
        """Check if patch is installed."""
        return self.installationresult == 'Installed'
    
    @property
    def installed_datetime(self) -> Optional[datetime]:
        """Parse installeddate as datetime object."""
        if self.installeddate is None:
            return None
        return datetime.strptime(self.installeddate, '%Y-%m-%d %H:%M:%S.%f')


# ============================================================================
# SO Customer
# ============================================================================
@dataclass
class SOCustomer:
    customerid: str
    customername: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SOCustomer':
        return cls(**data)


# ============================================================================
# Application (Detailed)
# ============================================================================
@dataclass
class ApplicationDetailed:
    _index: int
    licensetype: Optional[str]
    installationdate: Optional[str]
    displayname: str
    publisher: str
    version: str
    licensekey: Optional[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ApplicationDetailed':
        return cls(**data)
    
    @property
    def installation_datetime(self) -> Optional[datetime]:
        """Parse installationdate as datetime object."""
        if self.installationdate is None:
            return None
        return datetime.strptime(self.installationdate, '%Y-%m-%d %H:%M:%S.%f')


# ============================================================================
# Port
# ============================================================================
@dataclass
class Port:
    _index: int
    port: str
    servicename: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Port':
        return cls(**data)


# ============================================================================
# Service
# ============================================================================
@dataclass
class Service:
    _index: int
    startuptype: str
    caption: str
    servicename: str
    executablename: str
    useraccount: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Service':
        return cls(**data)
    
    @property
    def is_auto_start(self) -> bool:
        """Check if service starts automatically."""
        return self.startuptype == 'Auto'
    
    @property
    def is_manual_start(self) -> bool:
        """Check if service starts manually."""
        return self.startuptype == 'Manual'
    
    @property
    def is_disabled(self) -> bool:
        """Check if service is disabled."""
        return self.startuptype == 'Disabled'


# ============================================================================
# Computer System (Detailed)
# ============================================================================
@dataclass
class ComputerSystemDetailed:
    populatedmemory_slots: str
    totalmemory_slots: str
    systemtype: str
    uuid: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComputerSystemDetailed':
        return cls(**data)


# ============================================================================
# Logical Device
# ============================================================================
@dataclass
class LogicalDevice:
    _index: int
    maxcapacity: str
    volumename: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LogicalDevice':
        return cls(**data)
    
    @property
    def capacity_gb(self) -> float:
        """Convert capacity from bytes to GB."""
        return int(self.maxcapacity) / (1024**3)
    
    @property
    def capacity_tb(self) -> float:
        """Convert capacity from bytes to TB."""
        return int(self.maxcapacity) / (1024**4)


# ============================================================================
# Device (Detailed)
# ============================================================================
@dataclass
class DeviceDetailed:
    takecontroluuid: str
    lastloggedinuser_stillloggedin: str
    lastloggedinuser_sessiontype: str
    customerid: str
    warrantyexpirydate: str
    lastloggedinuser_domain: str
    createdon: str
    lastloggedinuser: str
    ncentralassettag: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceDetailed':
        return cls(**data)
    
    @property
    def is_user_logged_in(self) -> bool:
        """Check if user is still logged in."""
        return self.lastloggedinuser_stillloggedin.lower() == 'true'
    
    @property
    def created_datetime(self) -> datetime:
        """Parse createdon as datetime object."""
        return datetime.strptime(self.createdon, '%Y-%m-%d %H:%M:%S.%f %z')


# ============================================================================
# Customer (Detailed)
# ============================================================================
@dataclass
class CustomerDetailed:
    customerid: str
    customername: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CustomerDetailed':
        return cls(**data)


# ============================================================================
# Extra Data (Container for detailed hardware/software info)
# ============================================================================
@dataclass
class ExtraData:
    usbdevice: List[USBDevice]
    osfeatures: List[OSFeature]
    memory: List[Memory]
    os: OSDetailed
    mediaaccessdevice: List[MediaAccessDevice]
    folderforshare: List[FolderShare]
    printer: List[Printer]
    motherboard: Motherboard
    physicaldrive: List[PhysicalDrive]
    processor: ProcessorDetailed
    videocontroller: List[VideoController]
    patch: List[Patch]
    socustomer: SOCustomer
    application: List[ApplicationDetailed]
    port: List[Port]
    service: List[Service]
    computersystem: ComputerSystemDetailed
    logicaldevice: List[LogicalDevice]
    device: DeviceDetailed
    customer: CustomerDetailed
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ExtraData':
        return cls(
            usbdevice=[USBDevice.from_dict(item) for item in data.get('usbdevice', {}).get('list', [])],
            osfeatures=[OSFeature.from_dict(item) for item in data.get('osfeatures', {}).get('list', [])],
            memory=[Memory.from_dict(item) for item in data.get('memory', {}).get('list', [])],
            os=OSDetailed.from_dict(data.get('os', {})),
            mediaaccessdevice=[MediaAccessDevice.from_dict(item) for item in data.get('mediaaccessdevice', {}).get('list', [])],
            folderforshare=[FolderShare.from_dict(item) for item in data.get('folderforshare', {}).get('list', [])],
            printer=[Printer.from_dict(item) for item in data.get('printer', {}).get('list', [])],
            motherboard=Motherboard.from_dict(data.get('motherboard', {})),
            physicaldrive=[PhysicalDrive.from_dict(item) for item in data.get('physicaldrive', {}).get('list', [])],
            processor=ProcessorDetailed.from_dict(data.get('processor', {})),
            videocontroller=[VideoController.from_dict(item) for item in data.get('videocontroller', {}).get('list', [])],
            patch=[Patch.from_dict(item) for item in data.get('patch', {}).get('list', [])],
            socustomer=SOCustomer.from_dict(data.get('socustomer', {})),
            application=[ApplicationDetailed.from_dict(item) for item in data.get('application', {}).get('list', [])],
            port=[Port.from_dict(item) for item in data.get('port', {}).get('list', [])],
            service=[Service.from_dict(item) for item in data.get('service', {}).get('list', [])],
            computersystem=ComputerSystemDetailed.from_dict(data.get('computersystem', {})),
            logicaldevice=[LogicalDevice.from_dict(item) for item in data.get('logicaldevice', {}).get('list', [])],
            device=DeviceDetailed.from_dict(data.get('device', {})),
            customer=CustomerDetailed.from_dict(data.get('customer', {}))
        )


# ============================================================================
# OS (Basic Info)
# ============================================================================
@dataclass
class OSBasic:
    reportedos: str
    osarchitecture: str
    version: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OSBasic':
        return cls(**data)


# ============================================================================
# Application (Basic Info)
# ============================================================================
@dataclass
class ApplicationBasic:
    _index: int
    displayname: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ApplicationBasic':
        return cls(**data)


# ============================================================================
# Computer System (Basic Info)
# ============================================================================
@dataclass
class ComputerSystemBasic:
    serialnumber: str
    netbiosname: str
    model: str
    totalphysicalmemory: str
    manufacturer: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ComputerSystemBasic':
        return cls(**data)
    
    @property
    def memory_gb(self) -> float:
        """Convert total physical memory from bytes to GB."""
        return int(self.totalphysicalmemory) / (1024**3)


# ============================================================================
# Network Adapter
# ============================================================================
@dataclass
class NetworkAdapter:
    _index: int
    ipaddress: str
    dnsserver: str
    description: str
    dhcpserver: Optional[str]
    macaddress: str
    gateway: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'NetworkAdapter':
        return cls(**data)
    
    @property
    def uses_dhcp(self) -> bool:
        """Check if adapter uses DHCP."""
        return self.dhcpserver is not None


# ============================================================================
# Device (Basic Info)
# ============================================================================
@dataclass
class DeviceBasic:
    longname: str
    deleted: str
    lastlogin: str
    deviceclass: str
    deviceid: str
    uri: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceBasic':
        return cls(**data)
    
    @property
    def is_deleted(self) -> bool:
        """Check if device is deleted."""
        return self.deleted.lower() == 'true'
    
    @property
    def last_login_datetime(self) -> datetime:
        """Parse lastlogin as datetime object."""
        return datetime.strptime(self.lastlogin, '%Y-%m-%d %H:%M:%S.%f %z')


# ============================================================================
# Processor (Basic Info)
# ============================================================================
@dataclass
class ProcessorBasic:
    name: str
    numberofcores: str
    numberofcpus: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ProcessorBasic':
        return cls(**data)
    
    @property
    def total_cores(self) -> int:
        """Calculate total number of cores."""
        return int(self.numberofcores) * int(self.numberofcpus)


# ============================================================================
# Main Device Assets Data
# ============================================================================
@dataclass
class DeviceAssetsData:
    _extra: ExtraData
    os: OSBasic
    application: List[ApplicationBasic]
    computersystem: ComputerSystemBasic
    networkadapter: List[NetworkAdapter]
    device: DeviceBasic
    processor: ProcessorBasic
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceAssetsData':
        return cls(
            _extra=ExtraData.from_dict(data.get('_extra', {})),
            os=OSBasic.from_dict(data.get('os', {})),
            application=[ApplicationBasic.from_dict(item) for item in data.get('application', {}).get('list', [])],
            computersystem=ComputerSystemBasic.from_dict(data.get('computersystem', {})),
            networkadapter=[NetworkAdapter.from_dict(item) for item in data.get('networkadapter', {}).get('list', [])],
            device=DeviceBasic.from_dict(data.get('device', {})),
            processor=ProcessorBasic.from_dict(data.get('processor', {}))
        )


# ============================================================================
# Top-Level Device Assets Response
# ============================================================================
@dataclass
class DeviceAssets:
    """N-Central device assets from /devices/{id}/assets endpoint."""
    data: DeviceAssetsData
    _links: dict
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DeviceAssets':
        """
        Create a DeviceAssets instance from the API response dictionary.
        
        Args:
            data: Dictionary containing device assets data from N-Central API
            
        Returns:
            DeviceAssets: Parsed device assets object
        """
        return cls(
            data=DeviceAssetsData.from_dict(data.get('data', {})),
            _links=data.get('_links', {})
        )
    
    # Convenience properties for commonly accessed data
    
    @property
    def device_name(self) -> str:
        """Get the device's long name."""
        return self.data.device.longname
    
    @property
    def device_id(self) -> str:
        """Get the device ID."""
        return self.data.device.deviceid
    
    @property
    def ip_address(self) -> str:
        """Get the primary IP address."""
        if self.data.networkadapter:
            return self.data.networkadapter[0].ipaddress
        return ""
    
    @property
    def manufacturer(self) -> str:
        """Get the device manufacturer."""
        return self.data.computersystem.manufacturer
    
    @property
    def model(self) -> str:
        """Get the device model."""
        return self.data.computersystem.model
    
    @property
    def operating_system(self) -> str:
        """Get the operating system."""
        return self.data.os.reportedos
    
    @property
    def total_memory_gb(self) -> float:
        """Get total physical memory in GB."""
        return self.data.computersystem.memory_gb
    
    @property
    def processor_name(self) -> str:
        """Get the processor name."""
        return self.data.processor.name
    
    @property
    def total_cores(self) -> int:
        """Get total number of processor cores."""
        return self.data.processor.total_cores
    
    def get_installed_applications(self) -> List[ApplicationDetailed]:
        """Get list of installed applications."""
        return [app for app in self.data._extra.application if app.is_installed]
    
    def get_auto_start_services(self) -> List[Service]:
        """Get list of services that start automatically."""
        return [svc for svc in self.data._extra.service if svc.is_auto_start]
    
    def get_installed_patches(self) -> List[Patch]:
        """Get list of installed patches."""
        return [patch for patch in self.data._extra.patch if patch.is_installed]
    
    def get_pending_patches(self) -> List[Patch]:
        """Get list of patches not yet installed."""
        return [patch for patch in self.data._extra.patch if not patch.is_installed]