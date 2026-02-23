"""Tests for the appliance_task models."""
import pytest

from npycentral.models.appliance_task import (
    ApplianceTask,
    ApplianceTaskServiceDetail,
    ApplianceTaskThreshold,
    CpuUsage,
    DiskUsage,
    MemoryUsage,
    TopCpuProcess,
    TopMemoryProcess,
)
from tests.factories import (
    make_appliance_task_data,
    make_cpu_appliance_task_data,
    make_memory_appliance_task_data,
)


# ========================================================================
# THRESHOLD TESTS
# ========================================================================

class TestApplianceTaskThreshold:
    """Verify ApplianceTaskThreshold.from_dict creates thresholds correctly."""

    def test_from_dict_creates_threshold(self):
        data = {"state": "Warning", "lowValue": 80, "highValue": 90}
        threshold = ApplianceTaskThreshold.from_dict(data)

        assert threshold.state == "Warning"
        assert threshold.lowValue == 80
        assert threshold.highValue == 90

    def test_from_dict_with_failed_state(self):
        data = {"state": "Failed", "lowValue": 90, "highValue": 100}
        threshold = ApplianceTaskThreshold.from_dict(data)

        assert threshold.state == "Failed"
        assert threshold.lowValue == 90
        assert threshold.highValue == 100


# ========================================================================
# SERVICE DETAIL TESTS
# ========================================================================

class TestApplianceTaskServiceDetail:
    """Verify ApplianceTaskServiceDetail parsing, numeric_value, and str."""

    def test_from_dict_parses_thresholds(self):
        data = {
            "scanDetailId": 1,
            "detailName": "disk_total",
            "description": "Disk Total",
            "detailValue": "104857600",
            "state": "Normal",
            "monitoringType": "Performance",
            "thresholds": [
                {"state": "Warning", "lowValue": 80, "highValue": 90},
                {"state": "Failed", "lowValue": 90, "highValue": 100},
            ],
        }
        detail = ApplianceTaskServiceDetail.from_dict(data)

        assert detail.scanDetailId == 1
        assert detail.detailName == "disk_total"
        assert detail.description == "Disk Total"
        assert detail.detailValue == "104857600"
        assert detail.state == "Normal"
        assert detail.monitoringType == "Performance"
        assert len(detail.thresholds) == 2
        assert isinstance(detail.thresholds[0], ApplianceTaskThreshold)
        assert detail.thresholds[0].state == "Warning"
        assert detail.thresholds[1].state == "Failed"

    def test_numeric_value_returns_float_for_numeric_string(self):
        data = {
            "scanDetailId": 1,
            "detailName": "metric",
            "description": "A metric",
            "detailValue": "42.5",
            "state": "Normal",
            "monitoringType": "Performance",
            "thresholds": [],
        }
        detail = ApplianceTaskServiceDetail.from_dict(data)

        assert detail.numeric_value == 42.5
        assert isinstance(detail.numeric_value, float)

    def test_numeric_value_returns_none_for_non_numeric(self):
        data = {
            "scanDetailId": 1,
            "detailName": "status",
            "description": "Status",
            "detailValue": "N/A",
            "state": "Normal",
            "monitoringType": "Performance",
            "thresholds": [],
        }
        detail = ApplianceTaskServiceDetail.from_dict(data)

        assert detail.numeric_value is None

    def test_str_representation(self):
        data = {
            "scanDetailId": 1,
            "detailName": "disk_usage",
            "description": "Disk Usage",
            "detailValue": "50",
            "state": "Normal",
            "monitoringType": "Performance",
            "thresholds": [],
        }
        detail = ApplianceTaskServiceDetail.from_dict(data)

        assert str(detail) == "disk_usage: 50 (Disk Usage)"


# ========================================================================
# APPLIANCE TASK TESTS
# ========================================================================

class TestApplianceTask:
    """Verify ApplianceTask.from_dict, get_detail, get_detail_value, and str."""

    def test_from_dict_with_service_details(self):
        data = make_appliance_task_data({"disk_total": "104857600", "disk_used": "52428800"})
        task = ApplianceTask.from_dict(data)

        assert task.scanTime == "2025-01-15T10:00:00Z"
        assert task.state == "Normal"
        assert task.errorMessage == ""
        assert len(task.serviceDetails) == 2
        assert isinstance(task.serviceDetails[0], ApplianceTaskServiceDetail)
        assert task.serviceDetails[0].detailName == "disk_total"
        assert task.serviceDetails[1].detailName == "disk_used"

    def test_from_dict_with_empty_service_details(self):
        data = make_appliance_task_data({})
        task = ApplianceTask.from_dict(data)

        assert task.serviceDetails == []

    def test_get_detail_found(self):
        data = make_appliance_task_data({"disk_total": "104857600", "disk_used": "52428800"})
        task = ApplianceTask.from_dict(data)

        detail = task.get_detail("disk_total")
        assert detail is not None
        assert detail.detailName == "disk_total"
        assert detail.detailValue == "104857600"

    def test_get_detail_not_found(self):
        data = make_appliance_task_data({"disk_total": "104857600"})
        task = ApplianceTask.from_dict(data)

        assert task.get_detail("nonexistent") is None

    def test_get_detail_value_returns_float(self):
        data = make_appliance_task_data({"disk_usage": "75.5"})
        task = ApplianceTask.from_dict(data)

        value = task.get_detail_value("disk_usage")
        assert value == 75.5
        assert isinstance(value, float)

    def test_get_detail_value_returns_none_for_missing(self):
        data = make_appliance_task_data({"disk_total": "104857600"})
        task = ApplianceTask.from_dict(data)

        assert task.get_detail_value("nonexistent") is None

    def test_str_representation(self):
        data = make_appliance_task_data({"disk_usage": "50"})
        task = ApplianceTask.from_dict(data)

        result = str(task)
        assert "[Normal]" in result
        assert "2025-01-15T10:00:00Z" in result
        assert "disk_usage" in result


# ========================================================================
# DISK USAGE TESTS
# ========================================================================

class TestDiskUsage:
    """Verify DiskUsage properties for GB/MB conversions and str."""

    def test_total_gb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,  # 1 GB
            used_kb=524288.0,
            free_kb=524288.0,
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.total_gb == pytest.approx(1.0)

    def test_used_gb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,
            used_kb=524288.0,  # 0.5 GB
            free_kb=524288.0,
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.used_gb == pytest.approx(0.5)

    def test_free_gb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,
            used_kb=524288.0,
            free_kb=524288.0,  # 0.5 GB
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.free_gb == pytest.approx(0.5)

    def test_total_mb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,  # 1024 MB
            used_kb=524288.0,
            free_kb=524288.0,
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.total_mb == pytest.approx(1024.0)

    def test_used_mb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,
            used_kb=524288.0,  # 512 MB
            free_kb=524288.0,
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.used_mb == pytest.approx(512.0)

    def test_free_mb(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=1048576.0,
            used_kb=524288.0,
            free_kb=524288.0,  # 512 MB
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        assert disk.free_mb == pytest.approx(512.0)

    def test_str_representation(self):
        disk = DiskUsage(
            volume="C:",
            total_kb=104857600.0,
            used_kb=52428800.0,
            free_kb=52428800.0,
            usage_percent=50.0,
            state="Normal",
            scan_time="2025-01-15T10:00:00Z",
        )
        result = str(disk)
        assert "C:" in result
        assert "[Normal]" in result
        assert "50%" in result
        assert "2025-01-15T10:00:00Z" in result


# ========================================================================
# TOP CPU PROCESS TESTS
# ========================================================================

class TestTopCpuProcess:
    """Verify TopCpuProcess str representation."""

    def test_str_representation(self):
        proc = TopCpuProcess(
            name="process1.exe",
            pid=1001,
            user="SYSTEM",
            cpu_usage_percent=11.0,
        )
        result = str(proc)
        assert "process1.exe" in result
        assert "1001" in result
        assert "11.0%" in result
        assert "SYSTEM" in result


# ========================================================================
# CPU USAGE TESTS
# ========================================================================

class TestCpuUsage:
    """Verify CpuUsage.from_appliance_task and str."""

    def test_from_appliance_task(self):
        task_data = make_cpu_appliance_task_data(usage_percent=35.0, num_processes=3)
        task = ApplianceTask.from_dict(task_data)
        cpu = CpuUsage.from_appliance_task(task)

        assert cpu.usage_percent == 35.0
        assert cpu.state == "Normal"
        assert cpu.scan_time == "2025-01-15T10:00:00Z"
        assert len(cpu.top_processes) == 3
        assert cpu.top_processes[0].name == "process1.exe"
        assert cpu.top_processes[0].pid == 1001
        assert cpu.top_processes[0].user == "SYSTEM"
        assert cpu.top_processes[0].cpu_usage_percent == 11.0
        assert cpu.top_processes[1].name == "process2.exe"
        assert cpu.top_processes[1].pid == 1002
        assert cpu.top_processes[1].cpu_usage_percent == 12.0
        assert cpu.top_processes[2].name == "process3.exe"
        assert cpu.top_processes[2].pid == 1003
        assert cpu.top_processes[2].cpu_usage_percent == 13.0

    def test_from_appliance_task_no_processes(self):
        task_data = make_cpu_appliance_task_data(usage_percent=10.0, num_processes=0)
        task = ApplianceTask.from_dict(task_data)
        cpu = CpuUsage.from_appliance_task(task)

        assert cpu.usage_percent == 10.0
        assert cpu.top_processes == []

    def test_from_appliance_task_partial_processes(self):
        task_data = make_cpu_appliance_task_data(usage_percent=55.0, num_processes=2)
        task = ApplianceTask.from_dict(task_data)
        cpu = CpuUsage.from_appliance_task(task)

        assert cpu.usage_percent == 55.0
        assert len(cpu.top_processes) == 2
        assert cpu.top_processes[0].name == "process1.exe"
        assert cpu.top_processes[1].name == "process2.exe"

    def test_str_representation(self):
        task_data = make_cpu_appliance_task_data(usage_percent=35.0, num_processes=3)
        task = ApplianceTask.from_dict(task_data)
        cpu = CpuUsage.from_appliance_task(task)

        result = str(cpu)
        assert "CPU" in result
        assert "[Normal]" in result
        assert "35%" in result
        assert "3 top processes" in result
        assert "2025-01-15T10:00:00Z" in result


# ========================================================================
# TOP MEMORY PROCESS TESTS
# ========================================================================

class TestTopMemoryProcess:
    """Verify TopMemoryProcess properties and str."""

    def test_physical_mb(self):
        proc = TopMemoryProcess(
            name="memproc1.exe",
            pid=2001,
            user="LOCAL_SERVICE",
            physical_kb=512000.0,
            virtual_kb=1024000.0,
        )
        assert proc.physical_mb == pytest.approx(500.0)

    def test_virtual_mb(self):
        proc = TopMemoryProcess(
            name="memproc1.exe",
            pid=2001,
            user="LOCAL_SERVICE",
            physical_kb=512000.0,
            virtual_kb=1024000.0,
        )
        assert proc.virtual_mb == pytest.approx(1000.0)

    def test_str_representation(self):
        proc = TopMemoryProcess(
            name="memproc1.exe",
            pid=2001,
            user="LOCAL_SERVICE",
            physical_kb=512000.0,
            virtual_kb=1024000.0,
        )
        result = str(proc)
        assert "memproc1.exe" in result
        assert "2001" in result
        assert "LOCAL_SERVICE" in result


# ========================================================================
# MEMORY USAGE TESTS
# ========================================================================

class TestMemoryUsage:
    """Verify MemoryUsage.from_appliance_task, conversions, and str."""

    def test_from_appliance_task(self):
        phys_total = 16777216.0  # 16 GB in KB
        phys_used = 8388608.0   # 8 GB in KB
        task_data = make_memory_appliance_task_data(
            phys_total=phys_total,
            phys_used=phys_used,
            num_processes=2,
        )
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_total_kb == phys_total
        assert mem.physical_used_kb == phys_used
        assert mem.physical_free_kb == phys_total - phys_used
        assert mem.physical_usage_percent == pytest.approx(50.0)
        assert mem.virtual_total_kb == phys_total * 2
        assert mem.virtual_used_kb == phys_used
        assert mem.virtual_free_kb == phys_total * 2 - phys_used
        assert mem.virtual_usage_percent == pytest.approx(25.0)
        assert mem.state == "Normal"
        assert mem.scan_time == "2025-01-15T10:00:00Z"
        assert len(mem.top_processes) == 2
        assert mem.top_processes[0].name == "memproc1.exe"
        assert mem.top_processes[0].pid == 2001
        assert mem.top_processes[0].user == "LOCAL_SERVICE"
        assert mem.top_processes[1].name == "memproc2.exe"

    def test_physical_total_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_total_gb == pytest.approx(16.0)

    def test_physical_used_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_used_gb == pytest.approx(8.0)

    def test_physical_free_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_free_gb == pytest.approx(8.0)

    def test_physical_total_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_total_mb == pytest.approx(16384.0)

    def test_physical_used_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_used_mb == pytest.approx(8192.0)

    def test_physical_free_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.physical_free_mb == pytest.approx(8192.0)

    def test_virtual_total_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        # Virtual total = phys_total * 2
        assert mem.virtual_total_gb == pytest.approx(32.0)

    def test_virtual_used_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.virtual_used_gb == pytest.approx(8.0)

    def test_virtual_free_gb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        # Virtual free = phys_total*2 - phys_used = 33554432 - 8388608 = 25165824 KB
        assert mem.virtual_free_gb == pytest.approx(24.0)

    def test_virtual_total_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.virtual_total_mb == pytest.approx(32768.0)

    def test_virtual_used_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.virtual_used_mb == pytest.approx(8192.0)

    def test_virtual_free_mb(self):
        task_data = make_memory_appliance_task_data(phys_total=16777216.0, phys_used=8388608.0)
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.virtual_free_mb == pytest.approx(24576.0)

    def test_from_appliance_task_no_processes(self):
        task_data = make_memory_appliance_task_data(
            phys_total=16777216.0,
            phys_used=8388608.0,
            num_processes=0,
        )
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        assert mem.top_processes == []
        assert mem.physical_total_kb == 16777216.0

    def test_str_representation(self):
        task_data = make_memory_appliance_task_data(
            phys_total=16777216.0,
            phys_used=8388608.0,
            num_processes=2,
        )
        task = ApplianceTask.from_dict(task_data)
        mem = MemoryUsage.from_appliance_task(task)

        result = str(mem)
        assert "Memory" in result
        assert "[Normal]" in result
        assert "Physical:" in result
        assert "Virtual:" in result
        assert "2025-01-15T10:00:00Z" in result
