# API Reference

Complete reference for all npycentral functions.

---

## Client Setup

### NCentralClient

```python
from npycentral import NCentralClient

client = NCentralClient(
    base_url="https://ncentral.example.com",
    jwt="your-jwt-token",
    base_so_id="50",                          # Almost always 50
    default_timezone="Australia/Perth",  # optional
    ui_port=8443,                         # optional
    token_ttl=3600                        # optional
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | required | N-Central server URL |
| `jwt` | str | required | JWT token from N-Central |
| `base_so_id` | str | None | Service Organization ID (almost always "50") |
| `default_timezone` | str | "UTC" | IANA timezone for datetime operations |
| `ui_port` | int | 8443 | N-Central UI port for deep links |
| `token_ttl` | int | 3600 | Access token cache TTL in seconds |

### Security

The client protects sensitive tokens from accidental exposure. JWT and access tokens are wrapped in `SecretString` objects that mask their values when printed or logged:

```python
print(client)
# NCentralClient(base_url='https://ncentral.example.com')

print(client.__dict__)
# {..., '_jwt': SecretString('**********'), ...}

# Tokens can still be accessed explicitly when needed:
client._jwt.get_secret_value()
```

---

## Devices

### Device Retrieval

| Method | Description |
|--------|-------------|
| `get_devices(filter_id, filter_name, pagesize, use_cache, max_pages)` | Get all devices, optionally filtered |
| `get_device(device_id, device_name, filter_id, filter_name)` | Get single device by ID or name |
| `find_devices_by_name(device_name, filter_id, filter_name)` | Find all devices matching a name pattern |
| `find_devices_by_customer(customer_id, filter_id, filter_name)` | Find all devices for a customer |
| `find_devices_by_site(site_id, filter_id, filter_name)` | Find all devices for a site |

**Example: Get Windows Servers**
```python
servers = client.get_devices(filter_name="Servers - Windows")
for server in servers:
    print(f"{server.longName} - Last checkin: {server.last_checkin_datetime}")
```

**Example: Limit Results (for testing/sampling)**
```python
# Get only the first page of results
sample = client.get_devices(filter_name="Servers - Windows", max_pages=1)
print(f"Got {len(sample)} devices from first page")
```

**Example: Get Device by Name**
```python
# Simple lookup (searches all devices)
device = client.get_device(device_name="DC01")

# Faster lookup (searches within filter)
device = client.get_device(device_name="DC01", filter_name="Domain Controllers")

print(f"Device ID: {device.deviceId}")
print(f"Customer ID: {device.customerId}")
```

### Device Assets

| Method | Description |
|--------|-------------|
| `get_device_assets(device_id, device_name)` | Get full hardware/software inventory |
| `get_device_hardware_summary(device_id, device_name)` | Get concise hardware specs |
| `get_device_software_inventory(device_id, device_name)` | Get software and patch status |

**Example: Hardware Summary**
```python
hw = client.get_device_hardware_summary(device_name="WORKSTATION01")
print(f"Model: {hw['manufacturer']} {hw['model']}")
print(f"CPU: {hw['processor']}")
print(f"RAM: {hw['memory_gb']} GB")
```

**Example: Check Pending Patches**
```python
sw = client.get_device_software_inventory(device_name="SERVER01")
print(f"Pending patches: {sw['patches']['pending_count']}")
for title in sw['patches']['pending_titles'][:5]:
    print(f"  - {title}")
```

**Example: Lazy-Load Assets on Device Object**
```python
device = client.get_device(device_name="DC01")
print(device.has_assets)  # False - not loaded yet

assets = device.load_assets()  # Fetches from API
print(f"Memory: {assets.total_memory_gb:.1f} GB")
print(f"OS: {assets.operating_system}")
```

### Device Monitoring

| Method | Description |
|--------|-------------|
| `get_device_active_issues(device_id, device_name)` | Get active issues for a device |
| `get_device_service_monitoring_status(device_id, device_name)` | Get all monitoring statuses |
| `get_device_disk_status(device_id, device_name)` | Get disk monitoring for all volumes |
| `get_device_monitoring_summary(device_id, device_name)` | Get summary of all monitors |
| `check_device_disk_health(device_id, device_name)` | Check disk health report |

**Example: Check Active Issues**
```python
issues = client.get_device_active_issues(device_name="PROBLEMSERVER")
for issue in issues:
    print(f"[{issue.serviceName}] State: {issue.notificationState}")
```

**Example: Check Disk Health**
```python
health = client.check_device_disk_health(device_name="FILESERVER01")
print(f"Healthy: {health['healthy']}")
for vol in health['volumes']:
    print(f"  {vol['volume']}: {vol['status']}")
```

### Active Issues

| Method | Description |
|--------|-------------|
| `get_active_issues(org_unit_id, pagesize)` | Get all active issues for an org unit |

**Example: All Issues for a Customer**
```python
customer_id = 456
issues = client.get_active_issues(customer_id)
print(f"Total issues: {len(issues)}")
```

---

## Customers & Sites

| Method | Description |
|--------|-------------|
| `get_customers(so_id, pagesize)` | List all customers |
| `get_customer(customer_id)` | Get specific customer |
| `create_customer(customer_data, so_id)` | Create new customer |
| `create_site(customer_id, site_data)` | Create site under customer |
| `get_service_orgs(pagesize)` | List all service organizations |

**Example: List Customers**
```python
customers = client.get_customers()
for c in customers:
    print(f"{c['customerName']} (ID: {c['customerId']})")
```

**Example: Find Your SO ID**
```python
service_orgs = client.get_service_orgs()
for so in service_orgs:
    print(f"{so.soName}: {so.soId}")
```

**Example: Create a Site**
```python
site = client.create_site(
    customer_id=123,
    site_data={
        "siteName": "Branch Office",
        "contactFirstName": "John",
        "contactLastName": "Smith"
    }
)
```

---

## Device Filters

| Method | Description |
|--------|-------------|
| `get_filters(view_scope, pagesize)` | Get all device filters |
| `get_filter_by_id(filter_id)` | Get filter by ID |
| `get_filter_by_name(filter_name)` | Get filter by name |

**Example: List All Filters**
```python
filters = client.get_filters()
for f in filters:
    print(f"{f.filterName} (ID: {f.filterId})")
```

**Example: Use Filter with Devices**
```python
# These are equivalent:
devices = client.get_devices(filter_name="Servers - Windows")

filter_obj = client.get_filter_by_name("Servers - Windows")
devices = client.get_devices(filter_id=filter_obj.filterId)
```

---

## Custom Properties

| Method | Description |
|--------|-------------|
| `get_device_custom_properties(device_id)` | List all custom properties |
| `get_device_custom_property(device_id, property_id)` | Get property by ID |
| `get_device_custom_property_by_name(device_id, property_name)` | Get property by name |
| `update_device_custom_property(device_id, property_id, value)` | Update property value |

**Example: Read Custom Properties**
```python
device = client.get_device(device_name="SERVER01")
props = client.get_device_custom_properties(device.deviceId)
for prop in props:
    print(f"{prop.propertyName}: {prop.value}")
```

**Example: Update a Property**
```python
# Find property by name
prop = client.get_device_custom_property_by_name(device.deviceId, "AssetTag")

# Update value
client.update_device_custom_property(
    device_id=device.deviceId,
    property_id=prop.propertyId,
    value="ASSET-12345"
)
```

---

## Tasks (Automation)

| Method | Description |
|--------|-------------|
| `run_task(repo_id, task_name, customer_id, device_id, ...)` | Run a script/automation policy |
| `check_task_status(task_id)` | Get task status details |
| `monitor_task(task_id, interval, timeout)` | Poll until completion |
| `run_and_monitor_task(repo_id, task_name, customer_id, device_id, ...)` | Run and wait for completion |

**Example: Run Script and Wait**
```python
device = client.get_device(device_name="TARGET-PC")

result = client.run_and_monitor_task(
    repo_id=12345,                 # Script ID from N-Central
    task_name="Clear Temp Files",
    customer_id=device.customerId,
    device_id=device.deviceId,
    timeout=300                    # Wait up to 5 minutes
)

print(f"Status: {result['status']['status']}")
```

**Example: Fire and Forget**
```python
response = client.run_task(
    repo_id=12345,
    task_name="Restart Service",
    customer_id=device.customerId,
    device_id=device.deviceId
)
task_id = response['data']['taskId']
print(f"Task started: {task_id}")
```

---

## Deep Links / URLs

| Method | Description |
|--------|-------------|
| `get_device_overview_url(device, username, password)` | Device overview page URL |
| `get_device_details_url(device, username, password)` | Device details page URL |
| `get_device_remote_control_url(device, username, password)` | Remote control URL |
| `get_dashboard_url(username, password, language)` | Default dashboard URL |
| `get_active_issues_url(username, password, language)` | Active issues view URL |

**Example: Generate Ticket Links**
```python
device = client.get_device(device_name="PROBLEM-PC")

overview = client.get_device_overview_url(device.deviceId)
remote = client.get_device_remote_control_url(device.deviceId)

print(f"Overview: {overview}")
print(f"Remote Control: {remote}")
```

---

## Caching

Device lists are cached to improve performance. Default TTL is 5 minutes.

| Method | Description |
|--------|-------------|
| `set_device_cache_ttl(ttl_seconds)` | Set cache time-to-live |
| `clear_device_cache(filter_id)` | Clear cache (specific filter or all) |

**Example: Adjust Cache TTL**
```python
# Cache for 10 minutes
client.set_device_cache_ttl(600)

# Cache for 30 seconds (if you need fresher data)
client.set_device_cache_ttl(30)
```

**Example: Force Fresh Data**
```python
# Clear all cached device lists
client.clear_device_cache()

# Clear cache for specific filter only
filter_obj = client.get_filter_by_name("Servers - Windows")
client.clear_device_cache(filter_id=filter_obj.filterId)

# Or just bypass cache for one call
devices = client.get_devices(filter_name="Servers", use_cache=False)
```

---

## Exceptions

All methods can raise these exceptions:

| Exception | Description |
|-----------|-------------|
| `NCentralError` | Base exception for all errors |
| `AuthenticationError` | JWT or token authentication failed |
| `APIError` | General API error (has `status_code` and `response` attrs) |
| `NotFoundError` | Resource not found (404) |
| `RateLimitError` | Rate limit exceeded (429) |
| `ValidationError` | Invalid parameters |
| `TaskError` | Task execution failed |

**Example: Handle Errors**
```python
from npycentral.exceptions import NotFoundError, APIError

try:
    device = client.get_device(device_name="NONEXISTENT")
except NotFoundError:
    print("Device not found")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```
