"""Tests for the device_assets module: all dataclasses, properties, and role detection."""
import pytest
from datetime import datetime, timezone

from npycentral.models.device_assets import (
    _from_dict,
    _detect_roles,
    USBDevice,
    OSFeature,
    Memory,
    OSDetailed,
    MediaAccessDevice,
    FolderShare,
    Printer,
    Motherboard,
    PhysicalDrive,
    ProcessorDetailed,
    VideoController,
    Patch,
    SOCustomer,
    ApplicationDetailed,
    Port,
    Service,
    ComputerSystemDetailed,
    LogicalDevice,
    DeviceDetailed,
    CustomerDetailed,
    ExtraData,
    OSBasic,
    ApplicationBasic,
    ComputerSystemBasic,
    NetworkAdapter,
    DeviceBasic,
    ProcessorBasic,
    DeviceAssetsData,
    DeviceAssets,
)
from tests.factories import make_device_assets_data


# ========================================================================
# _from_dict HELPER TESTS
# ========================================================================

class TestFromDict:
    """Verify the _from_dict helper function behaviour."""

    def test_ignores_unknown_keys(self):
        data = {"_index": 0, "caption": "Hub", "manufacturer": "Gen", "status": "OK",
                "totally_unknown_field": "ignored"}
        usb = _from_dict(USBDevice, data)

        assert usb.caption == "Hub"
        assert not hasattr(usb, "totally_unknown_field")

    def test_fills_none_for_missing_optional_fields(self):
        data = {"_index": 0, "capacity": "1024"}
        mem = _from_dict(Memory, data)

        assert mem._index == 0
        assert mem.capacity == "1024"
        assert mem.serialnumber is None
        assert mem.location is None
        assert mem.type is None
        assert mem.partnumber is None
        assert mem.speed is None
        assert mem.manufacturer is None

    def test_raises_type_error_for_missing_required_fields(self):
        data = {"_index": 0}
        with pytest.raises(TypeError, match="USBDevice missing required fields"):
            _from_dict(USBDevice, data)


# ========================================================================
# USBDevice TESTS
# ========================================================================

class TestUSBDevice:

    def test_from_dict(self):
        data = {"_index": 0, "caption": "USB Hub", "manufacturer": "Generic", "status": "OK"}
        usb = USBDevice.from_dict(data)

        assert usb._index == 0
        assert usb.caption == "USB Hub"
        assert usb.manufacturer == "Generic"
        assert usb.status == "OK"


# ========================================================================
# OSFeature TESTS
# ========================================================================

class TestOSFeature:

    def test_from_dict(self):
        data = {"_index": 0, "pkey": "Feature1", "pvalue": "Enabled"}
        feat = OSFeature.from_dict(data)

        assert feat._index == 0
        assert feat.pkey == "Feature1"
        assert feat.pvalue == "Enabled"


# ========================================================================
# Memory TESTS
# ========================================================================

class TestMemory:

    def test_from_dict_with_all_fields(self):
        data = {"_index": 0, "serialnumber": "SN1", "location": "DIMM0",
                "type": "DDR4", "partnumber": "PN1", "speed": "3200",
                "manufacturer": "Samsung", "capacity": "17179869184"}
        mem = Memory.from_dict(data)

        assert mem._index == 0
        assert mem.serialnumber == "SN1"
        assert mem.location == "DIMM0"
        assert mem.type == "DDR4"
        assert mem.capacity == "17179869184"

    def test_from_dict_with_missing_optional_fields(self):
        data = {"_index": 1, "capacity": "8589934592"}
        mem = Memory.from_dict(data)

        assert mem.capacity == "8589934592"
        assert mem.serialnumber is None
        assert mem.location is None
        assert mem.type is None
        assert mem.partnumber is None
        assert mem.speed is None
        assert mem.manufacturer is None


# ========================================================================
# OSDetailed TESTS
# ========================================================================

class TestOSDetailed:

    def test_from_dict(self):
        data = {"licensetype": "OEM", "installdate": "2024-01-15 10:30:00",
                "serialnumber": "XXXXX", "publisher": "Microsoft",
                "csdversion": None, "lastbootuptime": "2025-01-10 08:00:00.000",
                "supportedos": "windows_server_2019", "licensekey": "XXXXX-XXXXX"}
        os_det = OSDetailed.from_dict(data)

        assert os_det.licensetype == "OEM"
        assert os_det.publisher == "Microsoft"

    def test_install_datetime_parses_correctly(self):
        os_det = OSDetailed.from_dict({"installdate": "2024-01-15 10:30:00"})

        dt = os_det.install_datetime
        assert dt == datetime(2024, 1, 15, 10, 30, 0)

    def test_install_datetime_none_when_installdate_is_none(self):
        os_det = OSDetailed.from_dict({"installdate": None})

        assert os_det.install_datetime is None

    def test_last_boot_datetime_parses_correctly(self):
        os_det = OSDetailed.from_dict({"lastbootuptime": "2025-01-10 08:00:00.000"})

        dt = os_det.last_boot_datetime
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 10
        assert dt.hour == 8
        assert dt.minute == 0


# ========================================================================
# MediaAccessDevice TESTS
# ========================================================================

class TestMediaAccessDevice:

    def test_from_dict(self):
        data = {"_index": 0, "mediatype": "DVD", "uniqueid": "DVD01"}
        dev = MediaAccessDevice.from_dict(data)

        assert dev._index == 0
        assert dev.mediatype == "DVD"
        assert dev.uniqueid == "DVD01"


# ========================================================================
# FolderShare TESTS
# ========================================================================

class TestFolderShare:

    def test_from_dict(self):
        data = {"_index": 0, "path": "C:\\Shared", "sharename": "SharedFolder"}
        share = FolderShare.from_dict(data)

        assert share.path == "C:\\Shared"
        assert share.sharename == "SharedFolder"


# ========================================================================
# Printer TESTS
# ========================================================================

class TestPrinter:

    def test_from_dict(self):
        data = {"_index": 0, "path": "\\\\server\\printer1", "port": "USB001",
                "name": "HP LaserJet", "systemdefault": "True"}
        printer = Printer.from_dict(data)

        assert printer.name == "HP LaserJet"
        assert printer.port == "USB001"

    def test_is_default_true(self):
        printer = Printer.from_dict(
            {"_index": 0, "path": "", "port": "", "name": "P1", "systemdefault": "True"})

        assert printer.is_default is True

    def test_is_default_false(self):
        printer = Printer.from_dict(
            {"_index": 0, "path": "", "port": "", "name": "P1", "systemdefault": "False"})

        assert printer.is_default is False


# ========================================================================
# Motherboard TESTS
# ========================================================================

class TestMotherboard:

    def test_from_dict_with_all_fields(self):
        data = {"product": "ProLiant DL380", "serialnumber": "MB123",
                "biosversion": "2.10", "version": "Rev A", "manufacturer": "HP"}
        mb = Motherboard.from_dict(data)

        assert mb.product == "ProLiant DL380"
        assert mb.manufacturer == "HP"

    def test_from_dict_with_missing_fields_all_none(self):
        mb = Motherboard.from_dict({})

        assert mb.product is None
        assert mb.serialnumber is None
        assert mb.biosversion is None
        assert mb.version is None
        assert mb.manufacturer is None


# ========================================================================
# PhysicalDrive TESTS
# ========================================================================

class TestPhysicalDrive:

    def test_from_dict(self):
        data = {"_index": 0, "serialnumber": "HD123", "modelnumber": "Samsung SSD",
                "capacity": "512110190592"}
        drive = PhysicalDrive.from_dict(data)

        assert drive.capacity == "512110190592"

    def test_capacity_gb(self):
        drive = PhysicalDrive.from_dict(
            {"_index": 0, "capacity": "512110190592"})

        expected_gb = 512110190592 / (1024**3)
        assert abs(drive.capacity_gb - expected_gb) < 0.01
        assert abs(drive.capacity_gb - 476.94) < 0.1

    def test_capacity_tb(self):
        drive = PhysicalDrive.from_dict(
            {"_index": 0, "capacity": "512110190592"})

        expected_tb = 512110190592 / (1024**4)
        assert abs(drive.capacity_tb - expected_tb) < 0.001


# ========================================================================
# ProcessorDetailed TESTS
# ========================================================================

class TestProcessorDetailed:

    def test_from_dict(self):
        data = {"maxclockspeed": "3600", "cpuid": "CPU0", "vendor": "GenuineIntel",
                "description": "Intel Xeon E5-2680", "architecture": "x64"}
        proc = ProcessorDetailed.from_dict(data)

        assert proc.maxclockspeed == "3600"
        assert proc.vendor == "GenuineIntel"


# ========================================================================
# VideoController TESTS
# ========================================================================

class TestVideoController:

    def test_from_dict(self):
        data = {"_index": 0, "name": "NVIDIA RTX 3080", "videocontrollerid": "VC01",
                "description": "GPU", "adapterram": "10737418240"}
        vc = VideoController.from_dict(data)

        assert vc.name == "NVIDIA RTX 3080"

    def test_adapter_ram_mb(self):
        vc = VideoController.from_dict(
            {"_index": 0, "name": "GPU", "adapterram": "10737418240"})

        assert vc.adapter_ram_mb == 10737418240 / (1024**2)
        assert vc.adapter_ram_mb == 10240.0

    def test_adapter_ram_mb_none_when_adapterram_is_none(self):
        vc = VideoController.from_dict(
            {"_index": 0, "name": "GPU", "adapterram": None})

        assert vc.adapter_ram_mb is None


# ========================================================================
# Patch TESTS
# ========================================================================

class TestPatch:

    def test_from_dict(self):
        data = {"_index": 0, "installationresult": "Installed",
                "installeddate": "2025-01-10 12:00:00.000",
                "title": "KB5001234", "category": "Security"}
        patch = Patch.from_dict(data)

        assert patch.title == "KB5001234"
        assert patch.category == "Security"

    def test_is_installed_true(self):
        patch = Patch.from_dict(
            {"_index": 0, "installationresult": "Installed",
             "title": "KB1", "category": "Security"})

        assert patch.is_installed is True

    def test_is_installed_false_for_pending(self):
        patch = Patch.from_dict(
            {"_index": 0, "installationresult": "Pending",
             "title": "KB2", "category": "Critical"})

        assert patch.is_installed is False

    def test_installed_datetime_parses_correctly(self):
        patch = Patch.from_dict(
            {"_index": 0, "installationresult": "Installed",
             "installeddate": "2025-01-10 12:00:00.000",
             "title": "KB1", "category": "Security"})

        dt = patch.installed_datetime
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 10
        assert dt.hour == 12

    def test_installed_datetime_none_when_installeddate_is_none(self):
        patch = Patch.from_dict(
            {"_index": 0, "installationresult": "Pending",
             "installeddate": None, "title": "KB2", "category": "Critical"})

        assert patch.installed_datetime is None


# ========================================================================
# SOCustomer TESTS
# ========================================================================

class TestSOCustomer:

    def test_from_dict(self):
        data = {"customerid": "50", "customername": "MSP Corp"}
        cust = SOCustomer.from_dict(data)

        assert cust.customerid == "50"
        assert cust.customername == "MSP Corp"


# ========================================================================
# ApplicationDetailed TESTS
# ========================================================================

class TestApplicationDetailed:

    def test_from_dict(self):
        data = {"_index": 0, "licensetype": "Commercial",
                "installationdate": "2024-06-15 09:00:00.000",
                "displayname": "VS Code", "publisher": "Microsoft",
                "version": "1.85.0", "licensekey": None}
        app = ApplicationDetailed.from_dict(data)

        assert app.displayname == "VS Code"
        assert app.publisher == "Microsoft"
        assert app.version == "1.85.0"

    def test_installation_datetime_parses_correctly(self):
        app = ApplicationDetailed.from_dict(
            {"_index": 0, "installationdate": "2024-06-15 09:00:00.000",
             "displayname": "App", "publisher": "Pub", "version": "1.0"})

        dt = app.installation_datetime
        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 15
        assert dt.hour == 9

    def test_installation_datetime_none_when_installationdate_is_none(self):
        app = ApplicationDetailed.from_dict(
            {"_index": 0, "installationdate": None,
             "displayname": "App", "publisher": "Pub", "version": "1.0"})

        assert app.installation_datetime is None


# ========================================================================
# Port TESTS
# ========================================================================

class TestPort:

    def test_from_dict(self):
        data = {"_index": 0, "port": "80", "servicename": "HTTP"}
        port = Port.from_dict(data)

        assert port.port == "80"
        assert port.servicename == "HTTP"


# ========================================================================
# Service TESTS
# ========================================================================

class TestService:

    def test_from_dict(self):
        data = {"_index": 0, "startuptype": "Auto", "caption": "Windows Update",
                "servicename": "wuauserv", "executablename": "svchost.exe",
                "useraccount": "LocalSystem"}
        svc = Service.from_dict(data)

        assert svc.servicename == "wuauserv"
        assert svc.caption == "Windows Update"

    def test_is_auto_start_true(self):
        svc = Service(_index=0, startuptype="Auto", caption="", servicename="svc",
                      executablename=None, useraccount=None)

        assert svc.is_auto_start is True
        assert svc.is_manual_start is False
        assert svc.is_disabled is False

    def test_is_manual_start_true(self):
        svc = Service(_index=0, startuptype="Manual", caption="", servicename="svc",
                      executablename=None, useraccount=None)

        assert svc.is_manual_start is True
        assert svc.is_auto_start is False

    def test_is_disabled_true(self):
        svc = Service(_index=0, startuptype="Disabled", caption="", servicename="svc",
                      executablename=None, useraccount=None)

        assert svc.is_disabled is True
        assert svc.is_auto_start is False
        assert svc.is_manual_start is False


# ========================================================================
# ComputerSystemDetailed TESTS
# ========================================================================

class TestComputerSystemDetailed:

    def test_from_dict(self):
        data = {"populatedmemory_slots": "2", "totalmemory_slots": "4",
                "systemtype": "x64-based PC",
                "uuid": "550e8400-e29b-41d4-a716-446655440000"}
        cs = ComputerSystemDetailed.from_dict(data)

        assert cs.populatedmemory_slots == "2"
        assert cs.uuid == "550e8400-e29b-41d4-a716-446655440000"


# ========================================================================
# LogicalDevice TESTS
# ========================================================================

class TestLogicalDevice:

    def test_from_dict(self):
        data = {"_index": 0, "maxcapacity": "512110190592", "volumename": "C:"}
        ld = LogicalDevice.from_dict(data)

        assert ld.maxcapacity == "512110190592"
        assert ld.volumename == "C:"

    def test_capacity_gb(self):
        ld = LogicalDevice.from_dict(
            {"_index": 0, "maxcapacity": "512110190592"})

        expected_gb = 512110190592 / (1024**3)
        assert abs(ld.capacity_gb - expected_gb) < 0.01


# ========================================================================
# DeviceDetailed TESTS
# ========================================================================

class TestDeviceDetailed:

    def test_from_dict(self):
        data = {"takecontroluuid": None, "customerid": "237",
                "warrantyexpirydate": None,
                "createdon": "2024-01-01 00:00:00.000 +0000",
                "ncentralassettag": None,
                "lastloggedinuser_stillloggedin": "True",
                "lastloggedinuser_sessiontype": "Console",
                "lastloggedinuser_domain": "DOMAIN",
                "lastloggedinuser": "admin"}
        dev = DeviceDetailed.from_dict(data)

        assert dev.customerid == "237"
        assert dev.lastloggedinuser == "admin"

    def test_is_user_logged_in_true(self):
        dev = DeviceDetailed.from_dict(
            {"customerid": "1", "createdon": "2024-01-01 00:00:00.000 +0000",
             "lastloggedinuser_stillloggedin": "True"})

        assert dev.is_user_logged_in is True

    def test_is_user_logged_in_false_when_none(self):
        dev = DeviceDetailed.from_dict(
            {"customerid": "1", "createdon": "2024-01-01 00:00:00.000 +0000",
             "lastloggedinuser_stillloggedin": None})

        assert dev.is_user_logged_in is False

    def test_created_datetime_parses_correctly(self):
        dev = DeviceDetailed.from_dict(
            {"customerid": "1", "createdon": "2024-01-01 00:00:00.000 +0000"})

        dt = dev.created_datetime
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.tzinfo is not None


# ========================================================================
# CustomerDetailed TESTS
# ========================================================================

class TestCustomerDetailed:

    def test_from_dict(self):
        data = {"customerid": "237", "customername": "Acme Corp"}
        cust = CustomerDetailed.from_dict(data)

        assert cust.customerid == "237"
        assert cust.customername == "Acme Corp"


# ========================================================================
# OSBasic TESTS
# ========================================================================

class TestOSBasic:

    def test_from_dict(self):
        data = {"reportedos": "Windows Server 2019 Standard",
                "osarchitecture": "64-bit", "version": "10.0.17763"}
        os_basic = OSBasic.from_dict(data)

        assert os_basic.reportedos == "Windows Server 2019 Standard"
        assert os_basic.osarchitecture == "64-bit"
        assert os_basic.version == "10.0.17763"


# ========================================================================
# ApplicationBasic TESTS
# ========================================================================

class TestApplicationBasic:

    def test_from_dict(self):
        data = {"_index": 0, "displayname": "Visual Studio Code"}
        app = ApplicationBasic.from_dict(data)

        assert app._index == 0
        assert app.displayname == "Visual Studio Code"


# ========================================================================
# ComputerSystemBasic TESTS
# ========================================================================

class TestComputerSystemBasic:

    def test_from_dict(self):
        data = {"serialnumber": "SYS123", "netbiosname": "SERVER-DC01",
                "model": "ProLiant DL380 Gen10",
                "totalphysicalmemory": "17179869184", "manufacturer": "HPE"}
        cs = ComputerSystemBasic.from_dict(data)

        assert cs.netbiosname == "SERVER-DC01"
        assert cs.manufacturer == "HPE"

    def test_memory_gb(self):
        cs = ComputerSystemBasic.from_dict(
            {"netbiosname": "SRV", "model": "M",
             "totalphysicalmemory": "17179869184", "manufacturer": "HP"})

        assert cs.memory_gb == 17179869184 / (1024**3)
        assert cs.memory_gb == 16.0


# ========================================================================
# NetworkAdapter TESTS
# ========================================================================

class TestNetworkAdapter:

    def test_from_dict(self):
        data = {"_index": 0, "ipaddress": "192.168.1.100",
                "dnsserver": "192.168.1.1", "description": "Intel Ethernet",
                "dhcpserver": "192.168.1.1", "macaddress": "00:11:22:33:44:55",
                "gateway": "192.168.1.1"}
        na = NetworkAdapter.from_dict(data)

        assert na.ipaddress == "192.168.1.100"
        assert na.macaddress == "00:11:22:33:44:55"

    def test_uses_dhcp_true_when_dhcpserver_present(self):
        na = NetworkAdapter.from_dict(
            {"_index": 0, "ipaddress": "10.0.0.1", "description": "Eth",
             "dhcpserver": "10.0.0.254", "macaddress": "AA:BB:CC:DD:EE:FF"})

        assert na.uses_dhcp is True

    def test_uses_dhcp_false_when_dhcpserver_is_none(self):
        na = NetworkAdapter.from_dict(
            {"_index": 0, "ipaddress": "10.0.0.1", "description": "Eth",
             "dhcpserver": None, "macaddress": "AA:BB:CC:DD:EE:FF"})

        assert na.uses_dhcp is False


# ========================================================================
# DeviceBasic TESTS
# ========================================================================

class TestDeviceBasic:

    def test_from_dict(self):
        data = {"longname": "SERVER-DC01", "deleted": "False",
                "lastlogin": "2025-01-15 10:00:00.000 +0000",
                "deviceclass": "Windows - Server", "deviceid": "12345",
                "uri": "https://ncentral.test.example.com/api/devices/12345"}
        dev = DeviceBasic.from_dict(data)

        assert dev.longname == "SERVER-DC01"
        assert dev.deviceid == "12345"

    def test_is_deleted_true(self):
        dev = DeviceBasic.from_dict(
            {"longname": "SRV", "deleted": "True",
             "lastlogin": "2025-01-15 10:00:00.000 +0000",
             "deviceclass": "Server", "deviceid": "1", "uri": "/api/devices/1"})

        assert dev.is_deleted is True

    def test_is_deleted_false(self):
        dev = DeviceBasic.from_dict(
            {"longname": "SRV", "deleted": "False",
             "lastlogin": "2025-01-15 10:00:00.000 +0000",
             "deviceclass": "Server", "deviceid": "1", "uri": "/api/devices/1"})

        assert dev.is_deleted is False

    def test_last_login_datetime_parses_correctly(self):
        dev = DeviceBasic.from_dict(
            {"longname": "SRV", "deleted": "False",
             "lastlogin": "2025-01-15 10:00:00.000 +0000",
             "deviceclass": "Server", "deviceid": "1", "uri": "/api/devices/1"})

        dt = dev.last_login_datetime
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.tzinfo is not None


# ========================================================================
# ProcessorBasic TESTS
# ========================================================================

class TestProcessorBasic:

    def test_from_dict(self):
        data = {"name": "Intel Xeon E5-2680 v4", "numberofcores": "14",
                "numberofcpus": "2"}
        proc = ProcessorBasic.from_dict(data)

        assert proc.name == "Intel Xeon E5-2680 v4"

    def test_total_cores(self):
        proc = ProcessorBasic.from_dict(
            {"name": "Xeon", "numberofcores": "14", "numberofcpus": "2"})

        assert proc.total_cores == 28


# ========================================================================
# ExtraData TESTS
# ========================================================================

class TestExtraData:

    def test_from_dict_parses_nested_structure(self):
        raw = make_device_assets_data()
        extra = ExtraData.from_dict(raw["data"]["_extra"])

        assert len(extra.usbdevice) == 1
        assert extra.usbdevice[0].caption == "USB Hub"
        assert len(extra.osfeatures) == 1
        assert len(extra.memory) == 1
        assert extra.os.licensetype == "OEM"
        assert len(extra.mediaaccessdevice) == 1
        assert len(extra.folderforshare) == 1
        assert len(extra.printer) == 1
        assert extra.motherboard.product == "ProLiant DL380"
        assert len(extra.physicaldrive) == 1
        assert extra.processor.vendor == "GenuineIntel"
        assert len(extra.videocontroller) == 1
        assert len(extra.patch) == 2
        assert extra.socustomer.customername == "MSP Corp"
        assert len(extra.application) == 1
        assert len(extra.port) == 2
        assert len(extra.service) == 3
        assert extra.computersystem.systemtype == "x64-based PC"
        assert len(extra.logicaldevice) == 1
        assert extra.device.customerid == "237"
        assert extra.customer.customername == "Acme Corp"


# ========================================================================
# DeviceAssetsData TESTS
# ========================================================================

class TestDeviceAssetsData:

    def test_from_dict_parses_data_section(self):
        raw = make_device_assets_data()
        dad = DeviceAssetsData.from_dict(raw["data"])

        assert dad.os.reportedos == "Windows Server 2019 Standard"
        assert len(dad.application) == 1
        assert dad.computersystem.netbiosname == "SERVER-DC01"
        assert len(dad.networkadapter) == 1
        assert dad.device.longname == "SERVER-DC01"
        assert dad.processor.name == "Intel Xeon E5-2680 v4"


# ========================================================================
# DeviceAssets TOP-LEVEL TESTS
# ========================================================================

class TestDeviceAssets:

    def test_from_dict_full_response(self):
        raw = make_device_assets_data()
        assets = DeviceAssets.from_dict(raw)

        assert assets._links == {"self": {"href": "/api/devices/12345/assets"}}
        assert isinstance(assets.data, DeviceAssetsData)

    def test_device_name(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.device_name == "SERVER-DC01"

    def test_device_id(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.device_id == "12345"

    def test_ip_address(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.ip_address == "192.168.1.100"

    def test_ip_address_empty_when_no_network_adapters(self):
        raw = make_device_assets_data()
        raw["data"]["networkadapter"]["list"] = []
        assets = DeviceAssets.from_dict(raw)

        assert assets.ip_address == ""

    def test_manufacturer(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.manufacturer == "HPE"

    def test_model(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.model == "ProLiant DL380 Gen10"

    def test_operating_system(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.operating_system == "Windows Server 2019 Standard"

    def test_total_memory_gb(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.total_memory_gb == 16.0

    def test_processor_name(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.processor_name == "Intel Xeon E5-2680 v4"

    def test_total_cores(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())

        assert assets.total_cores == 28

    def test_get_installed_applications_raises_attribute_error(self):
        """ApplicationDetailed does not have an is_installed property.
        This documents a known issue: get_installed_applications will raise
        AttributeError at runtime."""
        assets = DeviceAssets.from_dict(make_device_assets_data())

        with pytest.raises(AttributeError):
            assets.get_installed_applications()

    def test_get_auto_start_services(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())
        auto_services = assets.get_auto_start_services()

        assert len(auto_services) == 1
        assert auto_services[0].servicename == "wuauserv"

    def test_get_installed_patches(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())
        installed = assets.get_installed_patches()

        assert len(installed) == 1
        assert installed[0].title == "KB5001234"

    def test_get_pending_patches(self):
        assets = DeviceAssets.from_dict(make_device_assets_data())
        pending = assets.get_pending_patches()

        assert len(pending) == 1
        assert pending[0].title == "KB5005678"


# ========================================================================
# _detect_roles TESTS
# ========================================================================

class TestDetectRoles:

    def _make_service(self, name, startup="Auto"):
        return Service(_index=0, startuptype=startup, caption=name,
                       servicename=name, executablename=None, useraccount=None)

    def test_domain_controller_detected(self):
        services = [self._make_service("ntds"), self._make_service("kdc")]
        roles = _detect_roles(services)

        assert "Domain Controller" in roles

    def test_sql_server_detected_by_prefix(self):
        services = [self._make_service("mssql$SQLEXPRESS")]
        roles = _detect_roles(services)

        assert "SQL Server" in roles

    def test_exchange_server_detected_by_prefix(self):
        services = [self._make_service("msexchangetransport")]
        roles = _detect_roles(services)

        assert "Exchange Server" in roles

    def test_no_roles_for_unrelated_services(self):
        services = [self._make_service("wuauserv"),
                    self._make_service("Spooler")]
        roles = _detect_roles(services)

        assert roles == []

    def test_multiple_roles_detected(self):
        services = [
            self._make_service("ntds"),
            self._make_service("kdc"),
            self._make_service("dns"),
        ]
        roles = _detect_roles(services)

        assert "Domain Controller" in roles
        assert "DNS Server" in roles
        assert len(roles) == 2

    def test_empty_services_returns_no_roles(self):
        roles = _detect_roles([])

        assert roles == []
