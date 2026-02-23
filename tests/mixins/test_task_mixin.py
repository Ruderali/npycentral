"""Tests for TaskMixin methods."""
import json
from unittest.mock import patch

import pytest
import responses

from npycentral.exceptions import TaskError
from tests.conftest import BASE_URL


# ========================================================================
# run_task TESTS
# ========================================================================


class TestRunTask:
    """Verify run_task() sends correct POST payload."""

    def test_run_task_returns_response(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/scheduled-tasks/direct",
            json={"data": {"taskId": 456}},
            status=200,
        )
        result = client.run_task(
            repo_id=100,
            task_name="Reboot Server",
            customer_id=237,
            device_id=12345,
        )
        assert result["data"]["taskId"] == 456

        # Verify payload
        post_calls = [
            c for c in activate_responses.calls
            if c.request.method == "POST" and "/scheduled-tasks/direct" in c.request.url
        ]
        assert len(post_calls) == 1
        body = json.loads(post_calls[0].request.body)
        assert body["name"] == "Reboot Server"
        assert body["itemId"] == 100
        assert body["taskType"] == "Automation Policy"
        assert body["customerId"] == 237
        assert body["deviceId"] == 12345
        assert body["credential"] == {"type": "LocalSystem", "username": None, "password": None}
        assert body["parameters"] == []

    def test_run_task_with_custom_parameters(self, activate_responses, client):
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/scheduled-tasks/direct",
            json={"data": {"taskId": 789}},
            status=200,
        )
        params = [{"name": "timeout", "value": "300"}]
        result = client.run_task(
            repo_id=200,
            task_name="Custom Script",
            customer_id=237,
            device_id=12345,
            parameters=params,
        )
        assert result["data"]["taskId"] == 789

        post_calls = [
            c for c in activate_responses.calls
            if c.request.method == "POST" and "/scheduled-tasks/direct" in c.request.url
        ]
        body = json.loads(post_calls[0].request.body)
        assert body["parameters"] == [{"name": "timeout", "value": "300"}]


# ========================================================================
# check_task_status TESTS
# ========================================================================


class TestCheckTaskStatus:
    """Verify check_task_status() retrieves task status details."""

    def test_returns_task_details(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Running", "progress": 50}]},
            status=200,
        )
        result = client.check_task_status(456)
        assert len(result) == 1
        assert result[0]["status"] == "Running"

    def test_empty_returns_empty_list(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": []},
            status=200,
        )
        result = client.check_task_status(456)
        assert result == []


# ========================================================================
# monitor_task TESTS
# ========================================================================


class TestMonitorTask:
    """Verify monitor_task() polling and termination logic."""

    def test_immediate_success(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Success", "progress": 100}]},
            status=200,
        )
        with patch("npycentral.mixins.task_mixin.time.sleep"):
            result = client.monitor_task(456)
        assert result["status"] == "Success"
        assert result["task"]["status"] == "Success"

    def test_eventual_success(self, activate_responses, client):
        # First poll: Running
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Running", "progress": 50}]},
            status=200,
        )
        # Second poll: Success
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Success", "progress": 100}]},
            status=200,
        )
        with patch("npycentral.mixins.task_mixin.time.sleep") as mock_sleep:
            result = client.monitor_task(456)
        assert result["status"] == "Success"
        mock_sleep.assert_called_once()

    def test_failure(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Failed", "error": "Script error"}]},
            status=200,
        )
        with patch("npycentral.mixins.task_mixin.time.sleep"):
            result = client.monitor_task(456)
        assert result["status"] == "Failed"

    def test_timeout(self, activate_responses, client):
        # Always return Running
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Running"}]},
            status=200,
        )

        call_count = 0

        def fake_monotonic():
            nonlocal call_count
            call_count += 1
            # First call (start_time) returns 0, second call (elapsed check) returns 700
            return 0 if call_count <= 1 else 700

        with patch("npycentral.mixins.task_mixin.time.monotonic", side_effect=fake_monotonic), \
             patch("npycentral.mixins.task_mixin.time.sleep"):
            result = client.monitor_task(456, timeout=600)
        assert result["status"] == "Timeout"

    def test_no_details_returns_unknown(self, activate_responses, client):
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": []},
            status=200,
        )

        call_count = 0

        def fake_monotonic():
            nonlocal call_count
            call_count += 1
            return 0 if call_count <= 1 else 700

        with patch("npycentral.mixins.task_mixin.time.monotonic", side_effect=fake_monotonic), \
             patch("npycentral.mixins.task_mixin.time.sleep"):
            result = client.monitor_task(456, timeout=600)
        assert result["status"] == "Timeout"


# ========================================================================
# run_and_monitor_task TESTS
# ========================================================================


class TestRunAndMonitorTask:
    """Verify run_and_monitor_task() chains run + monitor."""

    def test_success(self, activate_responses, client):
        # Mock run_task POST
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/scheduled-tasks/direct",
            json={"data": {"taskId": 456}},
            status=200,
        )
        # Mock monitor_task status check
        activate_responses.add(
            responses.GET,
            f"{BASE_URL}/api/scheduled-tasks/456/status/details",
            json={"data": [{"status": "Success"}]},
            status=200,
        )
        with patch("npycentral.mixins.task_mixin.time.sleep"):
            result = client.run_and_monitor_task(
                repo_id=100,
                task_name="Test Task",
                customer_id=237,
                device_id=12345,
            )
        assert result["task_id"] == 456
        assert result["status"]["status"] == "Success"
        assert result["device_id"] == 12345
        assert result["customer_id"] == 237

    def test_no_task_id_raises_task_error(self, activate_responses, client):
        # Mock run_task POST returning no taskId
        activate_responses.add(
            responses.POST,
            f"{BASE_URL}/api/scheduled-tasks/direct",
            json={"data": {}},
            status=200,
        )
        with pytest.raises(TaskError, match="no taskId"):
            client.run_and_monitor_task(
                repo_id=100,
                task_name="Broken Task",
                customer_id=237,
                device_id=12345,
            )
