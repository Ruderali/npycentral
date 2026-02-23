"""Factories for building realistic N-Central API response data."""
from typing import Optional


def make_device_data(
    device_id: int = 12345,
    long_name: str = "SERVER-DC01",
    customer_id: int = 237,
    customer_name: str = "Acme Corp",
    site_id: int = 500,
    site_name: str = "Main Office",
    so_id: int = 50,
    so_name: str = "MSP Service Org",
    **overrides,
) -> dict:
    """Build a dict matching the N-Central GET /devices response shape."""
    data = {
        "deviceId": device_id,
        "uri": f"https://ncentral.test.example.com/api/devices/{device_id}",
        "remoteControlUri": None,
        "sourceUri": None,
        "longName": long_name,
        "deviceClass": "Windows - Server",
        "description": "",
        "isProbe": False,
        "osId": "700000004",
        "supportedOs": "windows_server_2019",
        "discoveredName": long_name,
        "deviceClassLabel": "Windows - Server",
        "supportedOsLabel": "Windows Server 2019",
        "lastLoggedInUser": "DOMAIN\\admin",
        "stillLoggedIn": True,
        "licenseMode": "Professional",
        "orgUnitId": customer_id,
        "soId": so_id,
        "soName": so_name,
        "customerId": customer_id,
        "customerName": customer_name,
        "siteId": site_id,
        "siteName": site_name,
        "applianceId": 999,
        "lastApplianceCheckinTime": "2025-01-15T10:30:00Z",
    }
    data.update(overrides)
    return data


def make_customer_data(
    customer_id: int = 237,
    customer_name: str = "Acme Corp",
    parent_id: int = 50,
    org_unit_type: str = "customer",
    **overrides,
) -> dict:
    data = {
        "customerId": customer_id,
        "customerName": customer_name,
        "orgUnitType": org_unit_type,
        "parentId": parent_id,
        "externalId": "",
        "externalId2": "",
        "contactFirstName": "John",
        "contactLastName": "Doe",
        "phone": "555-1234",
        "contactTitle": "IT Manager",
        "contactEmail": "john@acme.com",
        "contactPhone": "555-5678",
        "contactPhoneExt": "",
        "contactDepartment": "IT",
        "street1": "123 Main St",
        "street2": "",
        "city": "Springfield",
        "stateProv": "IL",
        "country": "US",
        "postalCode": "62701",
        "county": None,
        "isSystem": False,
        "isServiceOrg": False,
    }
    data.update(overrides)
    return data


def make_device_filter_data(
    filter_id: str = "83",
    filter_name: str = "Domain Controllers",
    description: str = "All domain controllers",
) -> dict:
    return {
        "filterId": filter_id,
        "filterName": filter_name,
        "description": description,
    }


def make_custom_property_data(
    property_id: int = 1,
    property_name: str = "CustomProp1",
    property_type: str = "TEXT",
    value: str = "some value",
    enumerated_value_list: Optional[list] = None,
) -> dict:
    return {
        "propertyId": property_id,
        "propertyName": property_name,
        "propertyType": property_type,
        "value": value,
        "enumeratedValueList": enumerated_value_list,
    }


def make_service_organization_data(
    so_id: str = "50",
    so_name: str = "MSP Corp",
) -> dict:
    return {
        "soId": so_id,
        "soName": so_name,
        "orgUnitType": "service_org",
        "parentId": "1",
        "externalId": None,
        "externalId2": None,
        "contactFirstName": "Admin",
        "contactLastName": "User",
        "phone": "555-0000",
        "contactTitle": "Admin",
        "contactEmail": "admin@msp.com",
        "contactPhone": "555-0001",
        "contactPhoneExt": "",
        "contactDepartment": "Operations",
        "street1": "456 Service Rd",
        "street2": "",
        "city": "Techville",
        "stateProv": "CA",
        "country": "US",
        "postalCode": "90210",
        "isSystem": False,
        "isServiceOrg": True,
    }


def make_active_issue_data(
    org_unit_id: int = 237,
    device_id: int = 12345,
    service_name: str = "Disk - C:",
    with_extra: bool = True,
) -> dict:
    data = {
        "orgUnitId": org_unit_id,
        "deviceId": device_id,
        "notificationState": 5,
        "serviceId": 100,
        "serviceName": service_name,
        "serviceType": "monitoring",
        "taskId": 5001,
        "serviceItemId": 200,
    }
    if with_extra:
        data["_extra"] = {
            "numberOfAcknowledgedNotification": 0,
            "avdUpdateServerEnabled": False,
            "licenseMode": "Professional",
            "psaIntegrationDisabled": False,
            "avdProtectionEnabled": False,
            "remoteControllable": True,
            "reactiveSupported": True,
            "partOfNotification": True,
            "remoteControlState": "connected",
            "acknowledgedBy": "",
            "avdVersion": "",
            "deviceName": "SERVER-DC01",
            "ticketCreationInProgress": False,
            "transitionTime": "2025-01-15T10:30:00Z",
            "integrationStatuses": None,
            "lwtEdrStatus": "",
            "patchManagementEnabled": True,
            "backupManagerProfile": "",
            "mspBackupProfile": "",
            "securityManagerProfile": "",
            "notificationAcknowledgmentInProgress": False,
            "taskIdent": "C:",
            "microsoftPatchManagementEnabled": True,
            "deviceClassValue": None,
            "backupManagerVersion": "",
            "securityManagerVersion": "",
            "remoteControlConnected": True,
            "monitoringDisabled": False,
            "numberOfActiveNotification": 1,
            "psaIntegrationExists": True,
            "lwtEdrEnabled": False,
            "mspBackupVersion": "",
            "thirdPartyPatchManagementEnabled": False,
            "probe": False,
            "reactiveEnabled": False,
            "netPathEnabled": False,
            "deviceClassLabel": "Windows - Server",
            "mspBackupEnabled": False,
            "port": "",
            "diskEncryptionEnabled": False,
            "customerTree": ["MSP Corp", "Acme Corp"],
            "securityManagerEnabled": False,
            "psaTicketDetails": "",
            "soCustomerID": 50,
            "maintenanceWindowEnabled": False,
            "backupManagerEnabled": False,
            "patchManagementProfile": "",
        }
    return data


def make_service_monitoring_status_data(
    task_id: int = 5001,
    module_name: str = "Disk",
    state_status: str = "Normal",
    task_ident: str = "C:",
) -> dict:
    return {
        "taskId": task_id,
        "serviceId": 100,
        "timeToStale": 3600,
        "taskNote": "",
        "taskIdent": task_ident,
        "stateStatus": state_status,
        "lastUpdate": "2025-01-15T10:00:00Z",
        "lastDataId": 1,
        "createdOn": "2024-06-01T00:00:00Z",
        "moduleName": module_name,
        "serviceItemId": 200,
        "lastScanTime": "2025-01-15 10:00:00.000 +0000",
        "isManagedTask": True,
        "transitionTime": "2025-01-15 09:00:00.000",
        "applianceId": 999,
        "applianceName": "PROBE-01",
    }


def make_appliance_task_data(detail_pairs: Optional[dict] = None) -> dict:
    """Build an appliance task response with arbitrary detail name/value pairs."""
    if detail_pairs is None:
        detail_pairs = {
            "disk_total": "104857600",
            "disk_used": "52428800",
            "disk_free": "52428800",
            "disk_usage": "50",
        }
    service_details = []
    for i, (name, value) in enumerate(detail_pairs.items()):
        service_details.append({
            "scanDetailId": i + 1,
            "detailName": name,
            "description": name.replace("_", " ").title(),
            "detailValue": str(value),
            "state": "Normal",
            "monitoringType": "Performance",
            "thresholds": [
                {"state": "Warning", "lowValue": 80, "highValue": 90},
                {"state": "Failed", "lowValue": 90, "highValue": 100},
            ],
        })
    return {
        "scanTime": "2025-01-15T10:00:00Z",
        "state": "Normal",
        "errorMessage": "",
        "serviceDetails": service_details,
    }


def make_cpu_appliance_task_data(
    usage_percent: float = 35.0,
    num_processes: int = 3,
) -> dict:
    """Build a CPU appliance task with top processes."""
    details = {"cpu_usage": str(usage_percent)}
    for i in range(1, num_processes + 1):
        details[f"top5_cpu_process{i}"] = f"process{i}.exe"
        details[f"top5_pid_process{i}"] = str(1000 + i)
        details[f"top5_user_process{i}"] = "SYSTEM"
        details[f"top5_cpu_usage{i}"] = str(10.0 + i)
    return make_appliance_task_data(details)


def make_memory_appliance_task_data(
    phys_total: float = 16777216,
    phys_used: float = 8388608,
    num_processes: int = 2,
) -> dict:
    """Build a Memory appliance task with top processes."""
    details = {
        "memory_physicaltotal": str(phys_total),
        "memory_physicalused": str(phys_used),
        "memory_physicalfree": str(phys_total - phys_used),
        "memory_physicalusage": str(round(phys_used / phys_total * 100, 1)),
        "memory_virtualtotal": str(phys_total * 2),
        "memory_virtualused": str(phys_used),
        "memory_virtualfree": str(phys_total * 2 - phys_used),
        "memory_virtualusage": str(round(phys_used / (phys_total * 2) * 100, 1)),
    }
    for i in range(1, num_processes + 1):
        details[f"memory_process{i}"] = f"memproc{i}.exe"
        details[f"memory_process_pid{i}"] = str(2000 + i)
        details[f"memory_process_user{i}"] = "LOCAL_SERVICE"
        details[f"memory_physical{i}"] = str(500000 + i * 100000)
        details[f"memory_virtual{i}"] = str(1000000 + i * 200000)
    return make_appliance_task_data(details)


def make_paginated_response(data: list, total_items: Optional[int] = None) -> dict:
    """Wrap a list of items in the standard N-Central paginated envelope."""
    return {
        "data": data,
        "totalItems": total_items if total_items is not None else len(data),
    }


def make_device_assets_data() -> dict:
    """Build a minimal but complete device assets API response."""
    return {
        "data": {
            "_extra": {
                "usbdevice": {"list": [
                    {"_index": 0, "caption": "USB Hub", "manufacturer": "Generic", "status": "OK"},
                ]},
                "osfeatures": {"list": [
                    {"_index": 0, "pkey": "Feature1", "pvalue": "Enabled"},
                ]},
                "memory": {"list": [
                    {"_index": 0, "serialnumber": "SN123", "location": "DIMM0",
                     "type": "DDR4", "partnumber": "PN456", "speed": "3200",
                     "manufacturer": "Samsung", "capacity": "17179869184"},
                ]},
                "os": {
                    "licensetype": "OEM",
                    "installdate": "2024-01-15 10:30:00",
                    "serialnumber": "XXXXX-XXXXX",
                    "publisher": "Microsoft",
                    "csdversion": None,
                    "lastbootuptime": "2025-01-10 08:00:00.000",
                    "supportedos": "windows_server_2019",
                    "licensekey": "XXXXX-XXXXX-XXXXX",
                },
                "mediaaccessdevice": {"list": [
                    {"_index": 0, "mediatype": "DVD", "uniqueid": "DVD01"},
                ]},
                "folderforshare": {"list": [
                    {"_index": 0, "path": "C:\\Shared", "sharename": "SharedFolder"},
                ]},
                "printer": {"list": [
                    {"_index": 0, "path": "\\\\server\\printer1", "port": "USB001",
                     "name": "HP LaserJet", "systemdefault": "True"},
                ]},
                "motherboard": {
                    "product": "ProLiant DL380",
                    "serialnumber": "MB123",
                    "biosversion": "2.10",
                    "version": "Rev A",
                    "manufacturer": "HP",
                },
                "physicaldrive": {"list": [
                    {"_index": 0, "serialnumber": "HD123", "modelnumber": "Samsung SSD 970",
                     "capacity": "512110190592"},
                ]},
                "processor": {
                    "maxclockspeed": "3600",
                    "cpuid": "CPU0",
                    "vendor": "GenuineIntel",
                    "description": "Intel Xeon E5-2680",
                    "architecture": "x64",
                },
                "videocontroller": {"list": [
                    {"_index": 0, "name": "NVIDIA RTX 3080",
                     "videocontrollerid": "VC01", "description": "GPU",
                     "adapterram": "10737418240"},
                ]},
                "patch": {"list": [
                    {"_index": 0, "installationresult": "Installed",
                     "installeddate": "2025-01-10 12:00:00.000",
                     "title": "KB5001234", "category": "Security"},
                    {"_index": 1, "installationresult": "Pending",
                     "installeddate": None,
                     "title": "KB5005678", "category": "Critical"},
                ]},
                "socustomer": {"customerid": "50", "customername": "MSP Corp"},
                "application": {"list": [
                    {"_index": 0, "licensetype": "Commercial",
                     "installationdate": "2024-06-15 09:00:00.000",
                     "displayname": "Visual Studio Code", "publisher": "Microsoft",
                     "version": "1.85.0", "licensekey": None},
                ]},
                "port": {"list": [
                    {"_index": 0, "port": "80", "servicename": "HTTP"},
                    {"_index": 1, "port": "443", "servicename": "HTTPS"},
                ]},
                "service": {"list": [
                    {"_index": 0, "startuptype": "Auto", "caption": "Windows Update",
                     "servicename": "wuauserv", "executablename": "svchost.exe",
                     "useraccount": "LocalSystem"},
                    {"_index": 1, "startuptype": "Manual", "caption": "Print Spooler",
                     "servicename": "Spooler", "executablename": "spoolsv.exe",
                     "useraccount": "LocalSystem"},
                    {"_index": 2, "startuptype": "Disabled", "caption": "Bluetooth",
                     "servicename": "bthserv", "executablename": "svchost.exe",
                     "useraccount": "LocalService"},
                ]},
                "computersystem": {
                    "populatedmemory_slots": "2",
                    "totalmemory_slots": "4",
                    "systemtype": "x64-based PC",
                    "uuid": "550e8400-e29b-41d4-a716-446655440000",
                },
                "logicaldevice": {"list": [
                    {"_index": 0, "maxcapacity": "512110190592", "volumename": "C:"},
                ]},
                "device": {
                    "takecontroluuid": None,
                    "customerid": "237",
                    "warrantyexpirydate": None,
                    "createdon": "2024-01-01 00:00:00.000 +0000",
                    "ncentralassettag": None,
                    "lastloggedinuser_stillloggedin": "True",
                    "lastloggedinuser_sessiontype": "Console",
                    "lastloggedinuser_domain": "DOMAIN",
                    "lastloggedinuser": "admin",
                },
                "customer": {"customerid": "237", "customername": "Acme Corp"},
            },
            "os": {
                "reportedos": "Windows Server 2019 Standard",
                "osarchitecture": "64-bit",
                "version": "10.0.17763",
            },
            "application": {"list": [
                {"_index": 0, "displayname": "Visual Studio Code"},
            ]},
            "computersystem": {
                "serialnumber": "SYS123",
                "netbiosname": "SERVER-DC01",
                "model": "ProLiant DL380 Gen10",
                "totalphysicalmemory": "17179869184",
                "manufacturer": "HPE",
            },
            "networkadapter": {"list": [
                {"_index": 0, "ipaddress": "192.168.1.100",
                 "dnsserver": "192.168.1.1", "description": "Intel Ethernet",
                 "dhcpserver": "192.168.1.1", "macaddress": "00:11:22:33:44:55",
                 "gateway": "192.168.1.1"},
            ]},
            "device": {
                "longname": "SERVER-DC01",
                "deleted": "False",
                "lastlogin": "2025-01-15 10:00:00.000 +0000",
                "deviceclass": "Windows - Server",
                "deviceid": "12345",
                "uri": "https://ncentral.test.example.com/api/devices/12345",
            },
            "processor": {
                "name": "Intel Xeon E5-2680 v4",
                "numberofcores": "14",
                "numberofcpus": "2",
            },
        },
        "_links": {"self": {"href": "/api/devices/12345/assets"}},
    }
