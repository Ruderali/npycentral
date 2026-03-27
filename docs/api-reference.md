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
    base_so_id="50",                    # Almost always 50
    default_timezone="Australia/Perth", # optional
    ui_port=8443,                       # optional
    token_ttl=3600,                     # optional
    max_retries=3,                      # optional
    retry_backoff_base=2,               # optional
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | required | N-Central server URL |
| `jwt` | str | required | JWT token from N-Central |
| `base_so_id` | str | `"50"` | Service Organization ID (almost always "50") |
| `default_timezone` | str | `"UTC"` | IANA timezone for datetime operations |
| `ui_port` | int | `8443` | N-Central UI port for deep links |
| `token_ttl` | int | `3600` | Access token cache TTL in seconds |
| `max_retries` | int | `3` | Retry attempts on 429 rate-limit responses |
| `retry_backoff_base` | int | `2` | Exponential backoff base in seconds (2 → 2s, 4s, 8s) |

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
| `get_devices(...)` | Get devices with optional server-side and client-side filters |
| `get_device(device_id, device_name, filter_id, filter_name)` | Get a single device by ID or name |
| `find_devices_by_name(device_name, filter_id, filter_name)` | Find all devices matching a name pattern |
| `find_devices_by_customer(customer_id, filter_id, filter_name)` | Find all devices for a customer |
| `find_devices_by_site(site_id, filter_id, filter_name)` | Find all devices for a site |

#### `get_devices()`

```python
devices = client.get_devices(
    filter_id=None,       # N-Central filter ID (server-side)
    filter_name=None,     # N-Central filter name (resolved to ID)
    customer_id=None,     # Scope to a customer (server-side when no filter)
    customer_name=None,   # Resolve customer by name then scope
    site_id=None,         # Scope to a site (server-side when no filter)
    device_class=None,    # e.g. "Server", "Workstation" (client-side, substring)
    os_type=None,         # e.g. "Windows", "Linux" (client-side, substring)
    pagesize=50,
    use_cache=False,
    max_pages=None,
)
```

**Fetch strategy:** When `customer_id` or `site_id` is provided without a `filter_id`, npycentral uses the `org-units/{id}/devices` endpoint for a server-side scoped fetch — avoiding a full environment scan. When a `filter_id` is also provided, the N-Central filter is applied server-side and any `customer_id`/`site_id` is applied client-side afterward. `device_class` and `os_type` are always client-side substring matches.

**Example: All servers for a customer**
```python
servers = client.get_devices(customer_name="Acme Corp", device_class="Server")
```

**Example: Windows devices at a site**
```python
devices = client.get_devices(site_id=114, os_type="Windows")
```

**Example: Use an N-Central filter**
```python
dcs = client.get_devices(filter_name="Domain Controllers")
```

**Example: Sample first page only**
```python
sample = client.get_devices(filter_name="All Devices", max_pages=1)
```

#### `find_devices_by_customer()` and `find_devices_by_site()`

These use the same server-side scoped fetch as `get_devices()` when no `filter_id` is given. Pass a `filter_id` to scope within a specific N-Central filter instead.

```python
# Server-side scoped to customer (efficient)
devices = client.find_devices_by_customer(customer_id=237)

# Scoped within a filter (client-side customer filter after fetching filter results)
devices = client.find_devices_by_customer(customer_id=237, filter_name="Servers")

# Site-scoped
devices = client.find_devices_by_site(site_id=114)
```

### Device Count Helpers

Get a count without fetching all device objects.

| Method | Description |
|--------|-------------|
| `get_customer_device_count(customer_id)` | Total device count for a customer |
| `get_filter_device_count(filter_id)` | Total device count matching an N-Central filter |

```python
count = client.get_customer_device_count(237)
print(f"Customer has {count} devices")

count = client.get_filter_device_count(filter_id=42)
print(f"Filter matches {count} devices")
```

### Device Lifecycle

| Method | Description |
|--------|-------------|
| `delete_device(device_id, device_name, remove_agents)` | Delete a device from N-Central |

```python
client.delete_device(device_id=12345)
client.delete_device(device_name="OLD-WORKSTATION01")
client.delete_device(device_id=12345, remove_agents=True)
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
assets = device.load_assets()
print(f"Memory: {assets.total_memory_gb:.1f} GB")
print(f"OS: {assets.operating_system}")
```

### Scheduled Tasks and Maintenance Windows

| Method | Description |
|--------|-------------|
| `get_device_scheduled_tasks(device_id, device_name)` | Get scheduled tasks configured on a device |
| `get_device_maintenance_windows(device_id, device_name)` | Get maintenance windows configured on a device |

```python
tasks = client.get_device_scheduled_tasks(device_name="SERVER01")
for task in tasks:
    print(f"{task.taskName} ({task.taskType}): {task.status}")

windows = client.get_device_maintenance_windows(device_name="SERVER01")
for w in windows:
    print(f"{w.windowName}: {w.startTime} → {w.endTime} (active: {w.isActive})")

# MaintenanceWindow also provides parsed datetime properties:
print(w.start_datetime)  # datetime object
print(w.end_datetime)
```

### Device Monitoring

| Method | Description |
|--------|-------------|
| `get_device_active_issues(device_id, device_name)` | Get active issues for a specific device |
| `get_device_service_monitoring_status(device_id, device_name)` | Get all monitoring statuses |
| `get_device_disk_status(device_id, device_name)` | Get disk monitoring for all volumes |
| `get_device_monitoring_summary(device_id, device_name)` | Get summary of all monitors |
| `check_device_disk_health(device_id, device_name)` | Check disk health report |

```python
issues = client.get_device_active_issues(device_name="PROBLEMSERVER")
for issue in issues:
    print(f"[{issue.serviceName}] State: {issue.notificationState}")
```

```python
health = client.check_device_disk_health(device_name="FILESERVER01")
print(f"Healthy: {health['healthy']}")
for vol in health['volumes']:
    print(f"  {vol['volume']}: {vol['status']}")
```

### Active Issues (Org Unit Scope)

| Method | Description |
|--------|-------------|
| `get_active_issues(...)` | Get active issues scoped to a customer, site, or service org |

```python
issues = client.get_active_issues(
    customer_id=None,    # Scope to a customer (orgUnitId == customerId)
    customer_name=None,  # Resolve by name then scope
    site_id=None,        # Scope to a site
    so_id=None,          # Scope to a service org (fetches per-customer, expensive)
    org_unit_id=None,    # Direct org unit ID
    severity=None,       # Client-side filter: "WARNING", "CRITICAL", "FAILED", "DISCONNECTED"
    pagesize=50,
)
```

**Example: Issues for a customer, critical only**
```python
issues = client.get_active_issues(customer_name="Acme Corp", severity="CRITICAL")
for issue in issues:
    print(f"{issue.deviceName}: {issue.serviceName}")
```

**Example: Issues at a site**
```python
issues = client.get_active_issues(site_id=114)
```

### Appliance Tasks & Resource Usage

| Method | Description |
|--------|-------------|
| `get_appliance_task(task_id)` | Get raw appliance task scan data |
| `get_device_disk_usage(device_id, device_name)` | Disk usage per volume |
| `get_device_cpu_usage(device_id, device_name)` | CPU usage % and top processes |
| `get_device_memory_usage(device_id, device_name)` | Memory usage and top processes |

```python
disks = client.get_device_disk_usage(device_name="FILESERVER01")
for disk in disks:
    print(f"{disk.volume}: {disk.free_gb:.1f} GB free ({disk.usage_percent:.0f}% used)")

cpu = client.get_device_cpu_usage(device_name="DC01")
print(f"CPU: {cpu.usage_percent}%")

mem = client.get_device_memory_usage(device_name="DC01")
print(f"Physical: {mem.physical_used_gb:.1f}/{mem.physical_total_gb:.1f} GB")
```

---

## Customers & Sites

### Customer Retrieval

| Method | Description |
|--------|-------------|
| `get_customers(so_id, pagesize, use_cache)` | List customers under a specific service org |
| `get_all_customers(pagesize, use_cache)` | List all customers across all service orgs |
| `get_customer(customer_id, customer_name, so_id, use_cache)` | Get a customer by ID or name |
| `find_customers_by_name(customer_name, so_id, use_cache)` | Find all customers matching a name pattern |
| `create_customer(customer_data, so_id)` | Create a new customer |

```python
# All customers across every service org
customers = client.get_all_customers()
for c in customers:
    print(f"{c.customerName} (ID: {c.customerId}, SO: {c.soId})")

# Customers under a specific SO
customers = client.get_customers(so_id=50)

# Lookup by name
customer = client.get_customer(customer_name="Acme Corp")
print(f"Contact: {customer.full_contact_name}")
```

### Sites

| Method | Description |
|--------|-------------|
| `get_sites(customer_id, pagesize)` | List sites under a customer |
| `get_all_sites(pagesize)` | List all sites across the environment |
| `create_site(customer_id, site_data)` | Create a site under a customer |

```python
sites = client.get_sites(customer_id=237)
for site in sites:
    print(f"{site.siteName} (ID: {site.siteId}, parentId: {site.parentId})")

# site.customerId is an alias for site.parentId
print(site.customerId)

# All sites in the environment
all_sites = client.get_all_sites()
```

```python
site = client.create_site(
    customer_id=123,
    site_data={
        "siteName": "Branch Office",
        "contactFirstName": "John",
        "contactLastName": "Smith",
    }
)
```

### Device Classes

Returns a hardcoded list of well-known N-Central device classes. No REST endpoint exists for this resource.

| Method | Description |
|--------|-------------|
| `get_device_classes()` | Get the list of N-Central device classes |

```python
from npycentral import DEVICE_CLASSES

classes = client.get_device_classes()
for dc in classes:
    print(f"{dc.deviceClassId}: {dc.deviceClassName}")
```

### Service Organizations

| Method | Description |
|--------|-------------|
| `get_service_orgs(pagesize, use_cache)` | List all service organizations |

```python
orgs = client.get_service_orgs()
for org in orgs:
    print(f"{org.soName}: {org.soId}")

# Cached (TTL: 1 hour — SOs rarely change)
orgs = client.get_service_orgs(use_cache=True)
```

### PSA Integration

| Method | Description |
|--------|-------------|
| `get_psa_customer_id(customer_id)` | Get PSA (ConnectWise/Autotask) customer ID |
| `get_psa_customer_mapping(customer_id)` | Get full PSA mapping details |

```python
customer = client.get_customer(customer_name="Acme Corp")

# PSA ID is lazy-loaded on first access
print(f"ConnectWise ID: {customer.psa_customer_id}")

# Direct lookup
psa_id = client.get_psa_customer_id(237)
mapping = client.get_psa_customer_mapping(237)
```

### Customer Cache

| Method | Description |
|--------|-------------|
| `set_customer_cache_ttl(ttl_seconds)` | Set cache TTL |
| `clear_customer_cache(so_id)` | Clear cache (specific SO or all) |

```python
customers = client.get_customers(use_cache=True)  # cached
client.clear_customer_cache()
customers = client.get_customers(use_cache=True)  # fresh
```

---

## Device Filters

| Method | Description |
|--------|-------------|
| `get_filters(view_scope, pagesize, use_cache)` | Get all device filters |
| `get_filter_by_id(filter_id)` | Get filter by ID |
| `get_filter_by_name(filter_name)` | Get filter by name |

`get_filters()` caches results (TTL: 5 minutes) by default. Pass `use_cache=False` to force a fresh fetch.

```python
filters = client.get_filters()
for f in filters:
    print(f"{f.filterName} (ID: {f.filterId})")

# These are equivalent:
devices = client.get_devices(filter_name="Servers - Windows")
f = client.get_filter_by_name("Servers - Windows")
devices = client.get_devices(filter_id=f.filterId)
```

---

## Custom Properties

### Device Custom Properties

| Method | Description |
|--------|-------------|
| `get_device_custom_properties(device_id)` | List all custom properties for a device |
| `get_device_custom_property(device_id, property_id)` | Get a property by ID |
| `get_device_custom_property_by_name(device_id, property_name)` | Get a property by name |
| `update_device_custom_property(device_id, property_id, value)` | Update a property value |

```python
props = client.get_device_custom_properties(device.deviceId)
for prop in props:
    print(f"{prop.propertyName}: {prop.value}")

prop = client.get_device_custom_property_by_name(device.deviceId, "AssetTag")
client.update_device_custom_property(
    device_id=device.deviceId,
    property_id=prop.propertyId,
    value="ASSET-12345"
)
```

### Customer Custom Properties

| Method | Description |
|--------|-------------|
| `get_customer_custom_properties(customer_id)` | List all custom properties for a customer |
| `get_customer_custom_property(customer_id, property_id)` | Get a property by ID |
| `get_customer_custom_property_by_name(customer_id, property_name)` | Get a property by name |
| `update_customer_custom_property(customer_id, property_id, value)` | Update a property value |

```python
props = client.get_customer_custom_properties(customer_id=237)
for prop in props:
    print(f"{prop.propertyName}: {prop.value}")

prop = client.get_customer_custom_property_by_name(237, "ContractType")
client.update_customer_custom_property(
    customer_id=237,
    property_id=prop.propertyId,
    value="Managed"
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

**Example: Run and wait**
```python
device = client.get_device(device_name="TARGET-PC")
result = client.run_and_monitor_task(
    repo_id=12345,
    task_name="Clear Temp Files",
    customer_id=device.customerId,
    device_id=device.deviceId,
    timeout=300
)
print(f"Status: {result['status']['status']}")
```

**Example: Fire and forget**
```python
response = client.run_task(
    repo_id=12345,
    task_name="Restart Service",
    customer_id=device.customerId,
    device_id=device.deviceId
)
task_id = response['data']['taskId']
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

```python
device = client.get_device(device_name="PROBLEM-PC")
overview = client.get_device_overview_url(device.deviceId)
remote = client.get_device_remote_control_url(device.deviceId)
print(f"Overview: {overview}")
print(f"Remote Control: {remote}")
```

---

## Caching

Device and customer lists are cached to improve performance. Default TTL is 5 minutes (300 seconds). Filter and service org lists have their own caches.

### Device Cache

| Method | Description |
|--------|-------------|
| `set_device_cache_ttl(ttl_seconds)` | Set cache TTL |
| `clear_device_cache(filter_id)` | Clear cache (specific filter/org-unit or all) |

```python
client.set_device_cache_ttl(600)   # 10 minutes
client.clear_device_cache()        # clear all
client.clear_device_cache(filter_id=42)  # clear one filter
devices = client.get_devices(filter_name="Servers", use_cache=False)  # bypass cache
```

### Customer Cache

| Method | Description |
|--------|-------------|
| `set_customer_cache_ttl(ttl_seconds)` | Set cache TTL |
| `clear_customer_cache(so_id)` | Clear cache (specific SO or all) |

### Filter Cache

`get_filters()` caches by `view_scope` with a 5-minute TTL. Pass `use_cache=False` to bypass.

### Service Org Cache

`get_service_orgs()` caches with a 1-hour TTL (service orgs rarely change). Pass `use_cache=False` to bypass.

---

## Models

Key model classes returned by the SDK:

| Model | Fields (selected) |
|-------|-------------------|
| `Device` | `deviceId`, `longName`, `customerId`, `customerName`, `siteId`, `siteName`, `deviceClass`, `deviceClassLabel`, `supportedOs`, `supportedOsLabel`, `last_checkin_datetime` |
| `Customer` | `customerId`, `customerName`, `soId`, `contactFirstName`, `contactLastName`, `full_contact_name`, `psa_customer_id` |
| `Site` | `siteId`, `siteName`, `parentId`, `customerId` (alias for parentId), `stateProv`, `isActive` |
| `DeviceClass` | `deviceClassId`, `deviceClassName` |
| `DeviceFilter` | `filterId`, `filterName` |
| `CustomProperty` | `propertyId`, `propertyName`, `value` |
| `ServiceOrganization` | `soId`, `soName` |
| `ActiveIssue` | `deviceId`, `deviceName`, `serviceName`, `notificationState`, `severity` |
| `MaintenanceWindow` | `windowId`, `windowName`, `startTime`, `endTime`, `recurrence`, `isActive`, `start_datetime`, `end_datetime` |
| `ScheduledTask` | `taskId`, `taskName`, `taskType`, `status`, `scheduledTime`, `lastRunTime`, `nextRunTime` |

All models are plain dataclasses. `from_dict()` ignores unknown API fields, so new N-Central fields won't break existing code.

---

## Exceptions

| Exception | Description |
|-----------|-------------|
| `NCentralError` | Base exception for all errors |
| `AuthenticationError` | JWT or token authentication failed |
| `APIError` | General API error (has `status_code` and `response` attrs) |
| `NotFoundError` | Resource not found (404) |
| `RateLimitError` | Rate limit exceeded (429), retried automatically |
| `ValidationError` | Invalid parameters |
| `TaskError` | Task execution failed |

```python
from npycentral.exceptions import NotFoundError, APIError

try:
    device = client.get_device(device_name="NONEXISTENT")
except NotFoundError:
    print("Device not found")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```
