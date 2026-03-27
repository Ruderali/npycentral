"""Tests for DeviceMixin methods."""
import pytest
import responses

from npycentral.models import (
    Device,
    ActiveIssue,
    DeviceAssets,
    ServiceMonitoringCollection,
)
from npycentral.models.appliance_task import ApplianceTask, CpuUsage, DiskUsage, MemoryUsage
from npycentral.exceptions import NotFoundError
from tests.conftest import BASE_URL
from tests.factories import (
    make_device_data,
    make_device_filter_data,
    make_active_issue_data,
    make_service_monitoring_status_data,
    make_appliance_task_data,
    make_cpu_appliance_task_data,
    make_memory_appliance_task_data,
    make_paginated_response,
    make_device_assets_data,
)


# ========================================================================
# RESOLUTION HELPER TESTS
# ========================================================================


class TestResolveFilterId:
    """Verify _resolve_filter_id() resolves filter ID from name or returns directly."""

    def test_returns_filter_id_directly_when_provided(self, client):
        result = client._resolve_filter_id(filter_id=83)
        assert result == 83

    def test_resolves_name_to_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83", filter_name="Domain Controllers"),
            ]),
            status=200,
        )
        result = client._resolve_filter_id(filter_name="Domain Controllers")
        assert result == 83

    def test_name_not_found_raises_not_found_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83", filter_name="Domain Controllers"),
            ]),
            status=200,
        )
        with pytest.raises(NotFoundError, match="Filter not found"):
            client._resolve_filter_id(filter_name="Nonexistent Filter")

    def test_both_none_returns_none(self, client):
        result = client._resolve_filter_id()
        assert result is None


class TestResolveDeviceId:
    """Verify _resolve_device_id() resolves device ID from name or returns directly."""

    def test_returns_device_id_directly(self, client):
        result = client._resolve_device_id(device_id=12345)
        assert result == 12345

    def test_resolves_name_to_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        result = client._resolve_device_id(device_name="SERVER-DC01")
        assert result == 12345

    def test_name_not_found_raises_not_found_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        with pytest.raises(NotFoundError, match="Device not found"):
            client._resolve_device_id(device_name="NONEXISTENT")

    def test_neither_raises_value_error(self, client):
        with pytest.raises(ValueError, match="Must provide either device_id or device_name"):
            client._resolve_device_id()


# ========================================================================
# CACHE MANAGEMENT TESTS
# ========================================================================


class TestDeviceCache:
    """Verify device cache lifecycle methods."""

    def test_init_device_cache_creates_attribute(self, client):
        assert not hasattr(client, "_device_cache")
        client._init_device_cache()
        assert hasattr(client, "_device_cache")

    def test_init_device_cache_idempotent(self, activate_responses, client):
        client._init_device_cache()
        client._device_cache["devices_None"] = ["sentinel"]
        client._init_device_cache()
        # Should NOT reset the cache
        assert "devices_None" in client._device_cache

    def test_set_device_cache_ttl_changes_ttl(self, client):
        client._init_device_cache()
        client.set_device_cache_ttl(600)
        assert client._device_cache_ttl == 600

    def test_clear_device_cache_all(self, client):
        client._init_device_cache()
        client._device_cache["devices_None"] = ["fake"]
        client._device_cache["devices_83"] = ["fake2"]
        client.clear_device_cache()
        assert len(client._device_cache) == 0

    def test_clear_device_cache_specific_filter(self, client):
        client._init_device_cache()
        client._device_cache["devices_83"] = ["fake83"]
        client._device_cache["devices_84"] = ["fake84"]
        client.clear_device_cache(filter_id=83)
        assert "devices_83" not in client._device_cache
        assert "devices_84" in client._device_cache

    def test_clear_device_cache_no_cache_no_error(self, client):
        # Should not raise even if _device_cache doesn't exist
        client.clear_device_cache()

    def test_cache_miss_fetches_from_api_then_hit_reuses(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345),
            ]),
            status=200,
        )
        result1 = client.get_devices(use_cache=True)
        result2 = client.get_devices(use_cache=True)
        assert len(result1) == 1
        assert len(result2) == 1

        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/api/devices" in c.request.url
        ]
        assert len(get_calls) == 1


# ========================================================================
# CORE DEVICE METHODS
# ========================================================================


class TestGetDevices:
    """Verify get_devices() fetches and parses device list."""

    def test_returns_device_objects(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
                make_device_data(device_id=12346, long_name="SERVER-DC02"),
            ]),
            status=200,
        )
        result = client.get_devices()
        assert len(result) == 2
        assert all(isinstance(d, Device) for d in result)
        assert result[0].deviceId == 12345
        assert result[1].longName == "SERVER-DC02"

    def test_with_filter_id_passes_param(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([make_device_data()]),
            status=200,
        )
        client.get_devices(filter_id=83)
        get_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/api/devices" in c.request.url
        ]
        assert "filterId=83" in get_calls[0].request.url

    def test_with_filter_name_resolves_name_first(self, activate_responses, client):
        # Mock filter endpoint
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/device-filters",
            json=make_paginated_response([
                make_device_filter_data(filter_id="83", filter_name="Domain Controllers"),
            ]),
            status=200,
        )
        # Mock device endpoint
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([make_device_data()]),
            status=200,
        )
        result = client.get_devices(filter_name="Domain Controllers")
        assert len(result) == 1

        device_calls = [
            c for c in activate_responses.calls
            if c.request.method == "GET" and "/api/devices?" in c.request.url
        ]
        assert "filterId=83" in device_calls[0].request.url

    def test_empty_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([]),
            status=200,
        )
        result = client.get_devices()
        assert result == []


class TestGetDevice:
    """Verify get_device() retrieves a single device by ID or name."""

    def test_by_id_returns_device(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345),
            status=200,
        )
        result = client.get_device(device_id=12345)
        assert isinstance(result, Device)
        assert result.deviceId == 12345

    def test_by_name_returns_device(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
                make_device_data(device_id=12346, long_name="SERVER-DC02"),
            ]),
            status=200,
        )
        result = client.get_device(device_name="SERVER-DC02")
        assert result.deviceId == 12346

    def test_neither_raises_value_error(self, client):
        with pytest.raises(ValueError, match="Must provide either device_id or device_name"):
            client.get_device()

    def test_by_id_from_cache(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        # Populate cache
        client.get_devices(use_cache=True)
        call_count_before = len(activate_responses.calls)

        # Should find in cache
        result = client.get_device(device_id=12345, use_cache=True)
        assert result.deviceId == 12345
        assert len(activate_responses.calls) == call_count_before

    def test_name_not_found_raises_not_found_error(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        with pytest.raises(NotFoundError, match="Device not found"):
            client.get_device(device_name="NONEXISTENT")


class TestFindDevicesByName:
    """Verify find_devices_by_name() returns partial, case-insensitive matches."""

    def test_partial_match(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
                make_device_data(device_id=12346, long_name="SERVER-DC02"),
                make_device_data(device_id=12347, long_name="WORKSTATION-01"),
            ]),
            status=200,
        )
        result = client.find_devices_by_name("DC01")
        assert len(result) == 1
        assert result[0].longName == "SERVER-DC01"

    def test_case_insensitive(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        result = client.find_devices_by_name("server-dc01")
        assert len(result) == 1
        assert result[0].longName == "SERVER-DC01"

    def test_no_matches_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, long_name="SERVER-DC01"),
            ]),
            status=200,
        )
        result = client.find_devices_by_name("NONEXISTENT")
        assert result == []


class TestFindDevicesByCustomer:
    """Verify find_devices_by_customer() uses org-unit scoped endpoint."""

    def test_filters_by_customer_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/org-units/237/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, customer_id=237),
                make_device_data(device_id=12347, customer_id=237),
            ]),
            status=200,
        )
        result = client.find_devices_by_customer(237)
        assert len(result) == 2
        assert all(d.customerId == 237 for d in result)

    def test_falls_back_to_filter_when_filter_id_given(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, customer_id=237),
                make_device_data(device_id=12346, customer_id=238),
                make_device_data(device_id=12347, customer_id=237),
            ]),
            status=200,
        )
        result = client.find_devices_by_customer(237, filter_id=1)
        assert len(result) == 2
        assert all(d.customerId == 237 for d in result)


class TestFindDevicesBySite:
    """Verify find_devices_by_site() uses org-unit scoped endpoint."""

    def test_filters_by_site_id(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/org-units/500/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, site_id=500),
                make_device_data(device_id=12347, site_id=500),
            ]),
            status=200,
        )
        result = client.find_devices_by_site(500)
        assert len(result) == 2
        assert all(d.siteId == 500 for d in result)

    def test_falls_back_to_filter_when_filter_id_given(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices",
            json=make_paginated_response([
                make_device_data(device_id=12345, site_id=500),
                make_device_data(device_id=12346, site_id=501),
                make_device_data(device_id=12347, site_id=500),
            ]),
            status=200,
        )
        result = client.find_devices_by_site(500, filter_id=1)
        assert len(result) == 2
        assert all(d.siteId == 500 for d in result)


# ========================================================================
# DEEP LINK URL TESTS
# ========================================================================


class TestDeepLinkUrls:
    """Verify deep link URL generation methods."""

    def _make_device_obj(self, client):
        """Helper to build a Device object directly."""
        return Device.from_dict(
            make_device_data(device_id=12345, customer_id=237),
            client=client,
        )

    def test_get_device_overview_url_with_device_object(self, client):
        device = self._make_device_obj(client)
        url = client.get_device_overview_url(device)
        assert "deepLinkAction.do" in url
        assert "method=deviceOverview" in url
        assert "customerID=237" in url
        assert "deviceID=12345" in url
        assert ":8443/" in url

    def test_get_device_overview_url_with_int(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345, customer_id=237),
            status=200,
        )
        url = client.get_device_overview_url(12345)
        assert "method=deviceOverview" in url
        assert "deviceID=12345" in url

    def test_get_device_details_url(self, client):
        device = self._make_device_obj(client)
        url = client.get_device_details_url(device)
        assert "method=deviceDetails" in url
        assert "deviceID=12345" in url

    def test_get_device_remote_control_url(self, client):
        device = self._make_device_obj(client)
        url = client.get_device_remote_control_url(device)
        assert "method=deviceRC" in url
        assert "deviceID=12345" in url

    def test_get_dashboard_url_with_port(self, client):
        url = client.get_dashboard_url()
        assert f"{BASE_URL}:8443/deepLinkAction.do" in url
        assert "method=defaultDashboard" in url

    def test_get_dashboard_url_with_credentials(self, client):
        url = client.get_dashboard_url(username="admin", password="secret")
        assert "username=admin" in url
        assert "password=secret" in url

    def test_get_active_issues_url(self, client):
        url = client.get_active_issues_url()
        assert "method=activeissues" in url
        assert f"{BASE_URL}:8443/deepLinkAction.do" in url


# ========================================================================
# MONITORING & ISSUES TESTS
# ========================================================================


class TestGetActiveIssues:
    """Verify get_active_issues() fetches issues for an org unit."""

    def test_returns_active_issue_objects(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/org-units/237/active-issues",
            json=make_paginated_response([
                make_active_issue_data(org_unit_id=237, device_id=12345),
                make_active_issue_data(org_unit_id=237, device_id=12346, service_name="CPU"),
            ]),
            status=200,
        )
        result = client.get_active_issues(237)
        assert len(result) == 2
        assert all(isinstance(i, ActiveIssue) for i in result)
        assert result[0].deviceId == 12345


class TestGetDeviceActiveIssues:
    """Verify get_device_active_issues() filters issues for a specific device."""

    def test_filters_by_device(self, activate_responses, client):
        # Mock get_device for ID resolution and customer lookup
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345, customer_id=237),
            status=200,
        )
        # Mock active issues for the customer org unit
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/org-units/237/active-issues",
            json=make_paginated_response([
                make_active_issue_data(org_unit_id=237, device_id=12345, service_name="Disk - C:"),
                make_active_issue_data(org_unit_id=237, device_id=99999, service_name="CPU"),
            ]),
            status=200,
        )
        result = client.get_device_active_issues(device_id=12345)
        assert len(result) == 1
        assert result[0].deviceId == 12345
        assert result[0].serviceName == "Disk - C:"


class TestGetDeviceAssets:
    """Verify get_device_assets() fetches and parses device assets."""

    def test_returns_device_assets(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/assets",
            json=make_device_assets_data(),
            status=200,
        )
        result = client.get_device_assets(device_id=12345)
        assert isinstance(result, DeviceAssets)
        assert result.device_name == "SERVER-DC01"
        assert result.manufacturer == "HPE"


class TestGetDeviceServiceMonitoringStatus:
    """Verify get_device_service_monitoring_status() fetches monitoring data."""

    def test_dict_response(self, activate_responses, client):
        mon1 = make_service_monitoring_status_data(task_id=5001, module_name="Disk", task_ident="C:")
        mon2 = make_service_monitoring_status_data(task_id=5002, module_name="CPU", task_ident="")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [mon1, mon2]},
            status=200,
        )
        result = client.get_device_service_monitoring_status(device_id=12345)
        assert isinstance(result, ServiceMonitoringCollection)
        assert len(result.statuses) == 2

    def test_list_response(self, activate_responses, client):
        mon1 = make_service_monitoring_status_data(task_id=5001, module_name="Disk")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json=[mon1],
            status=200,
        )
        result = client.get_device_service_monitoring_status(device_id=12345)
        assert isinstance(result, ServiceMonitoringCollection)
        assert len(result.statuses) == 1


class TestGetDeviceDiskStatus:
    """Verify get_device_disk_status() returns only disk monitors."""

    def test_returns_only_disk_monitors(self, activate_responses, client):
        disk = make_service_monitoring_status_data(task_id=5001, module_name="Disk", task_ident="C:")
        cpu = make_service_monitoring_status_data(task_id=5002, module_name="CPU", task_ident="")
        mem = make_service_monitoring_status_data(task_id=5003, module_name="Memory", task_ident="")
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk, cpu, mem]},
            status=200,
        )
        result = client.get_device_disk_status(device_id=12345)
        assert len(result) == 1
        assert result[0].moduleName == "Disk"
        assert result[0].taskIdent == "C:"


class TestCheckDeviceDiskHealth:
    """Verify check_device_disk_health() aggregates disk health."""

    def test_all_healthy(self, activate_responses, client):
        # Mock get_device
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345),
            status=200,
        )
        # Mock monitoring status
        disk_c = make_service_monitoring_status_data(
            task_id=5001, module_name="Disk", state_status="Normal", task_ident="C:"
        )
        disk_d = make_service_monitoring_status_data(
            task_id=5002, module_name="Disk", state_status="Normal", task_ident="D:"
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk_c, disk_d]},
            status=200,
        )
        result = client.check_device_disk_health(device_id=12345)
        assert result["healthy"] is True
        assert result["disk_count"] == 2
        assert len(result["warnings"]) == 0
        assert len(result["failures"]) == 0

    def test_with_warnings(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345),
            status=200,
        )
        disk_c = make_service_monitoring_status_data(
            task_id=5001, module_name="Disk", state_status="Normal", task_ident="C:"
        )
        disk_d = make_service_monitoring_status_data(
            task_id=5002, module_name="Disk", state_status="Warning", task_ident="D:"
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk_c, disk_d]},
            status=200,
        )
        result = client.check_device_disk_health(device_id=12345)
        assert result["healthy"] is False
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["volume"] == "D:"


class TestGetDeviceMonitoringSummary:
    """Verify get_device_monitoring_summary() returns summary dict."""

    def test_returns_summary_dict(self, activate_responses, client):
        # Mock monitoring status
        disk = make_service_monitoring_status_data(
            task_id=5001, module_name="Disk", state_status="Normal", task_ident="C:"
        )
        cpu = make_service_monitoring_status_data(
            task_id=5002, module_name="CPU", state_status="Warning", task_ident=""
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk, cpu]},
            status=200,
        )
        # Mock get_device for device info
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345",
            json=make_device_data(device_id=12345, long_name="SERVER-DC01"),
            status=200,
        )
        result = client.get_device_monitoring_summary(device_id=12345)
        assert result["device_name"] == "SERVER-DC01"
        assert result["device_id"] == 12345
        assert result["total"] == 2
        assert result["normal"] == 1
        assert result["warning"] == 1
        assert "issues" in result
        assert len(result["issues"]) == 1  # CPU warning


# ========================================================================
# RESOURCE USAGE TESTS
# ========================================================================


class TestGetApplianceTask:
    """Verify get_appliance_task() fetches and parses task data."""

    def test_returns_appliance_task(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/appliance-tasks/5001",
            json=make_appliance_task_data(),
            status=200,
        )
        result = client.get_appliance_task(5001)
        assert isinstance(result, ApplianceTask)
        assert result.state == "Normal"
        assert len(result.serviceDetails) > 0


class TestGetDeviceDiskUsage:
    """Verify get_device_disk_usage() chains monitoring + appliance task."""

    def test_returns_disk_usage_list(self, activate_responses, client):
        # Mock monitoring status with one disk monitor
        disk_mon = make_service_monitoring_status_data(
            task_id=5001, module_name="Disk", task_ident="C:"
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk_mon]},
            status=200,
        )
        # Mock appliance task for the disk monitor
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/appliance-tasks/5001",
            json=make_appliance_task_data(),
            status=200,
        )
        result = client.get_device_disk_usage(device_id=12345)
        assert len(result) == 1
        assert isinstance(result[0], DiskUsage)
        assert result[0].volume == "C:"
        assert result[0].usage_percent == 50.0


class TestGetDeviceCpuUsage:
    """Verify get_device_cpu_usage() chains monitoring + appliance task."""

    def test_returns_cpu_usage(self, activate_responses, client):
        # Mock monitoring status with CPU monitor
        cpu_mon = make_service_monitoring_status_data(
            task_id=5010, module_name="CPU", task_ident=""
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [cpu_mon]},
            status=200,
        )
        # Mock appliance task for CPU
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/appliance-tasks/5010",
            json=make_cpu_appliance_task_data(usage_percent=35.0),
            status=200,
        )
        result = client.get_device_cpu_usage(device_id=12345)
        assert isinstance(result, CpuUsage)
        assert result.usage_percent == 35.0
        assert len(result.top_processes) == 3

    def test_no_cpu_monitor_raises_not_found_error(self, activate_responses, client):
        # Mock monitoring status with NO CPU monitor
        disk_mon = make_service_monitoring_status_data(
            task_id=5001, module_name="Disk", task_ident="C:"
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [disk_mon]},
            status=200,
        )
        with pytest.raises(NotFoundError, match="No CPU monitor found"):
            client.get_device_cpu_usage(device_id=12345)


class TestGetDeviceMemoryUsage:
    """Verify get_device_memory_usage() chains monitoring + appliance task."""

    def test_returns_memory_usage(self, activate_responses, client):
        # Mock monitoring status with Memory monitor
        mem_mon = make_service_monitoring_status_data(
            task_id=5020, module_name="Memory", task_ident=""
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [mem_mon]},
            status=200,
        )
        # Mock appliance task for Memory
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/appliance-tasks/5020",
            json=make_memory_appliance_task_data(),
            status=200,
        )
        result = client.get_device_memory_usage(device_id=12345)
        assert isinstance(result, MemoryUsage)
        assert result.physical_total_kb == 16777216.0
        assert result.physical_used_kb == 8388608.0
        assert len(result.top_processes) == 2

    def test_no_memory_monitor_raises_not_found_error(self, activate_responses, client):
        # Mock monitoring status with NO Memory monitor
        cpu_mon = make_service_monitoring_status_data(
            task_id=5010, module_name="CPU", task_ident=""
        )
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/devices/12345/service-monitor-status",
            json={"data": [cpu_mon]},
            status=200,
        )
        with pytest.raises(NotFoundError, match="No memory monitor found"):
            client.get_device_memory_usage(device_id=12345)
