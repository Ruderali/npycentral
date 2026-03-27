from dataclasses import dataclass
from typing import List


@dataclass
class DeviceClass:
    """Represents an N-Central device class."""
    deviceClassId: int
    deviceClassName: str


# Known N-Central device class values.
# deviceClassName matches the deviceClassLabel field on Device objects.
# deviceClassId values are internal N-Central constants.
DEVICE_CLASSES: List[DeviceClass] = [
    DeviceClass(deviceClassId=101, deviceClassName="Server"),
    DeviceClass(deviceClassId=102, deviceClassName="Workstation"),
    DeviceClass(deviceClassId=103, deviceClassName="Laptop"),
    DeviceClass(deviceClassId=104, deviceClassName="Network Device"),
    DeviceClass(deviceClassId=105, deviceClassName="Printer"),
    DeviceClass(deviceClassId=106, deviceClassName="Mobile Device"),
    DeviceClass(deviceClassId=107, deviceClassName="Virtual Machine"),
    DeviceClass(deviceClassId=108, deviceClassName="NAS Device"),
    DeviceClass(deviceClassId=109, deviceClassName="Other"),
]
