# npycentral

A Python toolkit for the N-able N-Central RMM API.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install npycentral
```

## Quick Start

```python
from npycentral import NCentralClient

client = NCentralClient(
    base_url="https://your-ncentral.example.com",
    jwt="your-jwt-token",
    base_so_id="50"  # Almost always 50 - see note below
)
```

### Getting Your JWT Token

1. In N-Central, go to **Administration > User Management > Users**
2. Select your API user (or create one)
3. Go to the **API Access** tab
4. Generate a new JWT token

### Service Organization ID

For most N-Central instances, your SO ID is **50**. This is the default for single-SO setups, which covers the vast majority of deployments.

If you're unsure, you can check in N-Central (it's in the URL when viewing All Devices) or fetch it:

```python
service_orgs = client.get_service_orgs()
for so in service_orgs:
    print(f"{so.soName}: {so.soId}")
```

## Examples

### List Windows Servers and Check for Issues

```python
from npycentral import NCentralClient

client = NCentralClient(
    base_url="https://ncentral.example.com",
    jwt="your-jwt",
    base_so_id="50"
)

servers = client.get_devices(filter_name="Servers - Windows")
for server in servers:
    issues = client.get_device_active_issues(server.deviceId)
    print(f"{server.longName} - {len(issues)} active issues")
    for issue in issues:
        print(f"  [{issue.serviceName}] {issue.notificationState}")
```

### Get Device Details by Name

```python
# Get a specific device by name
device = client.get_device(device_name="DC01")
print(f"Device ID: {device.deviceId}")
print(f"Last Check-in: {device.last_checkin_datetime}")

# For better performance, narrow down with a filter first
device = client.get_device(device_name="DC01", filter_name="Domain Controllers")
```

### Check Disk Health

```python
device = client.get_device(device_name="FILESERVER01")
disk_status = client.check_device_disk_health(device.deviceId)

print(disk_status)
# Output: Disk Health: 3 monitors (2 normal, 1 warning, 0 failed)
#         C: Normal | D: Normal | E: Warning
```

### Get Hardware and Software Inventory

```python
device = client.get_device(device_name="WORKSTATION01")

# Load full asset details (lazy-loaded to save API calls)
assets = device.load_assets()

# Hardware summary
hw = client.get_device_hardware_summary(device.deviceId)
print(f"Model: {hw['manufacturer']} {hw['model']}")
print(f"CPU: {hw['processor']}")
print(f"RAM: {hw['memory_gb']} GB")

# Software inventory
sw = client.get_device_software_inventory(device.deviceId)
print(f"Pending patches: {len(sw['pending_patches'])}")
for patch in sw['pending_patches'][:5]:
    print(f"  - {patch.title}")
```

### Run a Script and Wait for Completion

```python
# Run an automation policy/script on a device
result = client.run_and_monitor_task(
    device_id=device.deviceId,
    task_id=12345,  # Your script/task ID from N-Central
    timeout=300     # Wait up to 5 minutes
)

print(f"Task completed with status: {result['status']}")
```

### Generate Deep Links for Tickets

```python
device = client.get_device(device_name="PROBLEMPC")

# Get URLs you can paste into tickets
overview_url = client.get_device_overview_url(device.deviceId)
remote_url = client.get_device_remote_control_url(device.deviceId)

print(f"Device Overview: {overview_url}")
print(f"Remote Control: {remote_url}")
```

## Performance Notes

- **Name lookups are slower than ID lookups.** The N-Central API doesn't support looking up devices by name directly, so `get_device(device_name="...")` fetches all devices and searches locally. Use `filter_name` to limit the scope when possible.

- **Device lists are cached.** By default, device lists are cached for 5 minutes to avoid hammering the API. You can clear the cache with `client.clear_device_cache()` or adjust the TTL with `client.set_device_cache_ttl(seconds)`.

## API Reference

See [docs/api-reference.md](docs/api-reference.md) for the complete function reference.

## License

MIT
