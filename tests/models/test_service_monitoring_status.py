"""Tests for ServiceMonitoringStatus and ServiceMonitoringCollection models."""
import pytest
from datetime import datetime

from npycentral.models.service_monitoring_status import (
    ServiceMonitoringStatus,
    ServiceMonitoringCollection,
)
from tests.factories import make_service_monitoring_status_data


# ========================================================================
# ServiceMonitoringStatus FROM_DICT TESTS
# ========================================================================

class TestServiceMonitoringStatusFromDict:
    """Verify ServiceMonitoringStatus.from_dict parsing."""

    def test_from_dict_creates_status(self):
        data = make_service_monitoring_status_data()
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.taskId == 5001
        assert status.moduleName == "Disk"
        assert status.stateStatus == "Normal"
        assert status.taskIdent == "C:"
        assert status.applianceName == "PROBE-01"


# ========================================================================
# DATETIME PROPERTY TESTS
# ========================================================================

class TestServiceMonitoringStatusDatetime:
    """Verify datetime parsing properties."""

    def test_last_scan_datetime_parses_correctly(self):
        data = make_service_monitoring_status_data()
        status = ServiceMonitoringStatus.from_dict(data)

        dt = status.last_scan_datetime
        assert dt is not None
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10

    def test_last_scan_datetime_none_for_empty_string(self):
        data = make_service_monitoring_status_data()
        data["lastScanTime"] = ""
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.last_scan_datetime is None

    def test_transition_datetime_parses_correctly(self):
        data = make_service_monitoring_status_data()
        status = ServiceMonitoringStatus.from_dict(data)

        dt = status.transition_datetime
        assert dt is not None
        assert isinstance(dt, datetime)
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 9

    def test_transition_datetime_none_for_empty_string(self):
        data = make_service_monitoring_status_data()
        data["transitionTime"] = ""
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.transition_datetime is None


# ========================================================================
# STATE STATUS PROPERTY TESTS
# ========================================================================

class TestServiceMonitoringStatusState:
    """Verify is_normal, is_warning, is_failed boolean properties."""

    def test_is_normal_true(self):
        data = make_service_monitoring_status_data(state_status="Normal")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_normal is True
        assert status.is_warning is False
        assert status.is_failed is False

    def test_is_warning_true(self):
        data = make_service_monitoring_status_data(state_status="Warning")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_warning is True
        assert status.is_normal is False
        assert status.is_failed is False

    def test_is_failed_true(self):
        data = make_service_monitoring_status_data(state_status="Failed")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_failed is True
        assert status.is_normal is False
        assert status.is_warning is False


# ========================================================================
# MODULE TYPE PROPERTY TESTS
# ========================================================================

class TestServiceMonitoringStatusModuleType:
    """Verify module type detection and volume_letter."""

    def test_is_disk_monitor(self):
        data = make_service_monitoring_status_data(module_name="Disk")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_disk_monitor is True
        assert status.is_memory_monitor is False
        assert status.is_cpu_monitor is False

    def test_is_memory_monitor(self):
        data = make_service_monitoring_status_data(module_name="Memory")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_memory_monitor is True
        assert status.is_disk_monitor is False
        assert status.is_cpu_monitor is False

    def test_is_cpu_monitor(self):
        data = make_service_monitoring_status_data(module_name="CPU")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.is_cpu_monitor is True
        assert status.is_disk_monitor is False
        assert status.is_memory_monitor is False

    def test_volume_letter_for_disk_monitor(self):
        data = make_service_monitoring_status_data(module_name="Disk", task_ident="D:")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.volume_letter == "D:"

    def test_volume_letter_none_for_non_disk_monitor(self):
        data = make_service_monitoring_status_data(module_name="CPU", task_ident="cpu0")
        status = ServiceMonitoringStatus.from_dict(data)

        assert status.volume_letter is None


# ========================================================================
# STRING REPRESENTATION TEST
# ========================================================================

class TestServiceMonitoringStatusStr:
    """Verify __str__ output."""

    def test_str_representation(self):
        data = make_service_monitoring_status_data(
            module_name="Disk",
            state_status="Normal",
            task_ident="C:",
        )
        status = ServiceMonitoringStatus.from_dict(data)
        result = str(status)

        assert "[Normal]" in result
        assert "Disk" in result
        assert "(C:)" in result


# ========================================================================
# ServiceMonitoringCollection TESTS
# ========================================================================

def _build_mixed_collection_data():
    """Build a list of status dicts with varied modules and states."""
    return [
        make_service_monitoring_status_data(
            task_id=1, module_name="Disk", state_status="Normal", task_ident="C:",
        ),
        make_service_monitoring_status_data(
            task_id=2, module_name="Disk", state_status="Warning", task_ident="D:",
        ),
        make_service_monitoring_status_data(
            task_id=3, module_name="Memory", state_status="Normal", task_ident="",
        ),
        make_service_monitoring_status_data(
            task_id=4, module_name="CPU", state_status="Failed", task_ident="",
        ),
        make_service_monitoring_status_data(
            task_id=5, module_name="Connectivity", state_status="Normal", task_ident="",
        ),
    ]


class TestServiceMonitoringCollectionFromList:
    """Verify ServiceMonitoringCollection.from_list."""

    def test_from_list_creates_collection(self):
        data = _build_mixed_collection_data()
        coll = ServiceMonitoringCollection.from_list(data)

        assert len(coll.statuses) == 5
        assert all(
            isinstance(s, ServiceMonitoringStatus) for s in coll.statuses
        )


class TestServiceMonitoringCollectionFilters:
    """Verify filter methods on the collection."""

    def test_get_disk_monitors(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        disks = coll.get_disk_monitors()

        assert len(disks) == 2
        assert all(s.is_disk_monitor for s in disks)

    def test_get_memory_monitors(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        mems = coll.get_memory_monitors()

        assert len(mems) == 1
        assert mems[0].moduleName == "Memory"

    def test_get_cpu_monitors(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        cpus = coll.get_cpu_monitors()

        assert len(cpus) == 1
        assert cpus[0].moduleName == "CPU"

    def test_get_by_module(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        conns = coll.get_by_module("Connectivity")

        assert len(conns) == 1
        assert conns[0].moduleName == "Connectivity"

    def test_get_failed(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        failed = coll.get_failed()

        assert len(failed) == 1
        assert failed[0].stateStatus == "Failed"

    def test_get_warnings(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        warnings = coll.get_warnings()

        assert len(warnings) == 1
        assert warnings[0].stateStatus == "Warning"

    def test_get_issues_returns_warnings_and_failures(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        issues = coll.get_issues()

        assert len(issues) == 2
        states = {s.stateStatus for s in issues}
        assert states == {"Warning", "Failed"}

    def test_get_disk_by_volume_found(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        disk = coll.get_disk_by_volume("D:")

        assert disk is not None
        assert disk.volume_letter == "D:"

    def test_get_disk_by_volume_not_found(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        disk = coll.get_disk_by_volume("Z:")

        assert disk is None


class TestServiceMonitoringCollectionSummary:
    """Verify summary() counts."""

    def test_summary_counts(self):
        coll = ServiceMonitoringCollection.from_list(_build_mixed_collection_data())
        summary = coll.summary()

        assert summary["total"] == 5
        assert summary["normal"] == 3
        assert summary["warning"] == 1
        assert summary["failed"] == 1
        assert summary["disk_monitors"] == 2
        assert summary["memory_monitors"] == 1
        assert summary["cpu_monitors"] == 1

    def test_summary_empty_collection(self):
        coll = ServiceMonitoringCollection.from_list([])
        summary = coll.summary()

        assert summary["total"] == 0
        assert summary["normal"] == 0
        assert summary["warning"] == 0
        assert summary["failed"] == 0
        assert summary["disk_monitors"] == 0
        assert summary["memory_monitors"] == 0
        assert summary["cpu_monitors"] == 0
