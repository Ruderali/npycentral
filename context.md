# npycentral Enhancement: Disk Usage Data from Appliance Tasks

## Goal

Add the ability to retrieve detailed disk usage metrics (total, used, free, usage %) for a device's monitored volumes. This data comes from a two-step API flow using endpoints that the library already partially wraps.

## API Flow

### Step 1: Get disk monitor task IDs

**Endpoint:** `GET /api/devices/{deviceId}/service-monitor-status`

This endpoint is already wrapped by `get_device_service_monitoring_status()` in `device_mixin.py`, returning a `ServiceMonitoringCollection`. Disk monitors have `moduleName == "Disk"` and `taskIdent` is the volume letter (e.g. `"C:"`).

The `taskId` field on each `ServiceMonitoringStatus` object is what we need for step 2.

Example disk entry from the response:
```json
{
  "taskId": 1960221156,
  "serviceId": 113,
  "taskIdent": "C:",
  "stateStatus": "Normal",
  "moduleName": "Disk",
  ...
}
```

### Step 2: Get detailed metrics for a disk task

**Endpoint:** `GET /api/appliance-tasks/{taskId}`

This endpoint is **NOT currently wrapped** by the library. It returns the actual scan data with metric values.

Example response:
```json
{
  "scanTime": "2026-02-09 10:36:17.141",
  "state": "NORMAL",
  "errorMessage": "",
  "serviceDetails": [
    {
      "scanDetailId": 3788500,
      "detailName": "disk_total",
      "description": "Total disk size (GB)",
      "detailValue": "133299196",
      "state": "NO_STATE",
      "monitoringType": "None",
      "thresholds": []
    },
    {
      "scanDetailId": 3788501,
      "detailName": "disk_used",
      "description": "Disk space used (GB)",
      "detailValue": "37979516",
      "state": "NO_STATE",
      "monitoringType": "None",
      "thresholds": []
    },
    {
      "scanDetailId": 3788502,
      "detailName": "disk_free",
      "description": "Disk free space (GB)",
      "detailValue": "95319680",
      "state": "NORMAL",
      "monitoringType": "Normal",
      "thresholds": [
        {
          "state": "NORMAL",
          "lowValue": 2000000,
          "highValue": 18446744073709551614
        },
        {
          "state": "WARNING",
          "lowValue": 1000000,
          "highValue": 2097152
        },
        {
          "state": "FAILED",
          "lowValue": 0,
          "highValue": 1048576
        }
      ]
    },
    {
      "scanDetailId": 3788503,
      "detailName": "disk_usage",
      "description": "Disk Usage (%)",
      "detailValue": "28",
      "state": "NORMAL",
      "monitoringType": "Normal",
      "thresholds": [
        {
          "state": "NORMAL",
          "lowValue": 0,
          "highValue": 95
        },
        {
          "state": "WARNING",
          "lowValue": 96,
          "highValue": 98
        },
        {
          "state": "FAILED",
          "lowValue": 99,
          "highValue": 100
        }
      ]
    }
  ]
}
```

**Important:** The `detailValue` fields are strings. Despite the descriptions saying "(GB)", the values are actually in **KB**. For example, `133299196` KB / 1024 = ~130174 MB, which matches the `maxcapacity` from the device assets endpoint for the same volume.

## Suggested Implementation

### 1. New model: `ApplianceTaskDetail` (or similar)

A dataclass to represent the `appliance-tasks/{taskId}` response. Should parse `serviceDetails` into typed objects with convenience properties for extracting disk metrics by `detailName`.

Key fields from `serviceDetails` entries:
- `scanDetailId`: int
- `detailName`: str (e.g. `"disk_total"`, `"disk_used"`, `"disk_free"`, `"disk_usage"`)
- `description`: str
- `detailValue`: str (numeric string)
- `state`: str
- `monitoringType`: str
- `thresholds`: list of threshold objects

### 2. New mixin method or addition to device_mixin

A method like `get_appliance_task_detail(task_id)` that calls `GET /api/appliance-tasks/{taskId}` and returns the typed model.

### 3. Convenience method for disk usage

A higher-level method like `get_device_disk_usage(device_id)` that:
1. Calls `get_device_service_monitoring_status(device_id)`
2. Filters for disk monitors via `.get_disk_monitors()`
3. For each disk monitor, calls `get_appliance_task_detail(monitor.taskId)`
4. Returns a structured result with per-volume metrics (volume letter, total KB, used KB, free KB, usage %)

### 4. Convenience properties on the disk usage model

- `total_gb`, `used_gb`, `free_gb` (convert from KB)
- `total_mb`, `used_mb`, `free_mb`
- `usage_percent`

## Existing Code Reference

The `ServiceMonitoringStatus` model is in `models/service_monitoring_status.py`. It already has:
- `volume_letter` property (returns `taskIdent` for disk monitors)
- `is_disk_monitor` property
- `taskId` field (needed for the appliance-tasks call)

The `ServiceMonitoringCollection` has:
- `get_disk_monitors()` — returns list of disk `ServiceMonitoringStatus` objects
- `get_disk_by_volume(volume)` — returns a specific volume's monitor

The `DeviceMixin` in `mixins/device_mixin.py` already has:
- `get_device_service_monitoring_status(device_id)` — returns `ServiceMonitoringCollection`
- `get_device_disk_status(device_id)` — returns list of disk `ServiceMonitoringStatus` (health only, no metrics)

## Test Data

- **Server NC-Reporting** (device ID `1079702067`): Disk task ID `1960221156` for `C:` volume
- **Workstation NT-5CG3242LQ3** (device ID `1282809566`): Disk task ID `733126542` for `C:` volume
