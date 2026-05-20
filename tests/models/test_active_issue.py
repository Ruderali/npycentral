"""Tests for the ActiveIssue and IssueExtra models."""
import pytest
from datetime import datetime, timezone

from npycentral.models.active_issue import ActiveIssue, IssueExtra
from tests.factories import make_active_issue_data


# ========================================================================
# IssueExtra TESTS
# ========================================================================

class TestIssueExtra:
    """Verify IssueExtra parsing and property accessors."""

    def test_from_dict_creates_instance(self):
        data = make_active_issue_data(with_extra=True)
        extra = IssueExtra.from_dict(data["_extra"])

        assert extra.deviceName == "SERVER-DC01"
        assert extra.remoteControllable is True
        assert extra.remoteControlState == "connected"
        assert extra.customerTree == ["MSP Corp", "Acme Corp"]

    def test_transition_datetime_parses_iso_string(self):
        data = make_active_issue_data(with_extra=True)
        extra = IssueExtra.from_dict(data["_extra"])

        dt = extra.transition_datetime
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 0
        assert dt.tzinfo is not None

    def test_transition_datetime_returns_none_for_empty_string(self):
        data = make_active_issue_data(with_extra=True)
        data["_extra"]["transitionTime"] = ""
        extra = IssueExtra.from_dict(data["_extra"])

        assert extra.transition_datetime is None


# ========================================================================
# ActiveIssue FROM_DICT TESTS
# ========================================================================

class TestActiveIssueFromDict:
    """Verify ActiveIssue.from_dict parsing."""

    def test_from_dict_with_extra_creates_issue_with_issue_extra(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        assert issue.orgUnitId == 237
        assert issue.deviceId == 12345
        assert issue.notificationState == 5
        assert issue.serviceName == "Disk - C:"
        assert issue._extra is not None
        assert isinstance(issue._extra, IssueExtra)

    def test_from_dict_without_extra_has_extra_none(self):
        data = make_active_issue_data(with_extra=False)
        issue = ActiveIssue.from_dict(data)

        assert issue._extra is None

    def test_from_dict_does_not_mutate_input_dict(self):
        data = make_active_issue_data(with_extra=True)
        assert "_extra" in data

        ActiveIssue.from_dict(data)

        assert "_extra" in data


# ========================================================================
# REMOTE CONTROL PROPERTY TESTS
# ========================================================================

class TestActiveIssueRemoteControl:
    """Verify remote control property accessors."""

    def test_remote_control_available_true_when_controllable_and_state_present(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        assert issue.remote_control_available is True

    def test_remote_control_available_false_when_no_extra(self):
        data = make_active_issue_data(with_extra=False)
        issue = ActiveIssue.from_dict(data)

        assert issue.remote_control_available is False

    def test_remote_control_connected_true_when_state_is_connected(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        assert issue.remote_control_connected is True

    def test_remote_control_connected_false_when_no_extra(self):
        data = make_active_issue_data(with_extra=False)
        issue = ActiveIssue.from_dict(data)

        assert issue.remote_control_connected is False


# ========================================================================
# DEVICE NAME AND CUSTOMER TREE PROPERTY TESTS
# ========================================================================

class TestActiveIssueDeviceProperties:
    """Verify device_name, customer_tree, and transition_datetime accessors."""

    def test_device_name_from_extra(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        assert issue.device_name == "SERVER-DC01"

    def test_device_name_none_without_extra(self):
        data = make_active_issue_data(with_extra=False)
        issue = ActiveIssue.from_dict(data)

        assert issue.device_name is None

    def test_customer_tree_from_extra(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        assert issue.customer_tree == ["MSP Corp", "Acme Corp"]

    def test_customer_tree_empty_list_without_extra(self):
        data = make_active_issue_data(with_extra=False)
        issue = ActiveIssue.from_dict(data)

        assert issue.customer_tree == []

    def test_transition_datetime_from_extra(self):
        data = make_active_issue_data(with_extra=True)
        issue = ActiveIssue.from_dict(data)

        dt = issue.transition_datetime
        assert dt is not None
        assert dt == datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)


# ========================================================================
# STRING REPRESENTATION TESTS
# ========================================================================

class TestActiveIssueStr:
    """Verify __str__ output for various notification states."""

    def test_str_critical_state(self):
        data = make_active_issue_data(with_extra=True, service_name="Disk - C:")
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[CRITICAL] Disk - C: on SERVER-DC01"

    def test_str_ok_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 1
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[OK] Disk - C: on SERVER-DC01"

    def test_str_normal_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 2
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[NORMAL] Disk - C: on SERVER-DC01"

    def test_str_warning_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 3
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[WARNING] Disk - C: on SERVER-DC01"

    def test_str_failed_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 6
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[FAILED] Disk - C: on SERVER-DC01"

    def test_str_disconnected_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 7
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[DISCONNECTED] Disk - C: on SERVER-DC01"

    def test_str_disabled_state(self):
        data = make_active_issue_data(with_extra=True)
        data["notificationState"] = 8
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[DISABLED] Disk - C: on SERVER-DC01"

    def test_str_without_extra_uses_device_id(self):
        data = make_active_issue_data(with_extra=False, device_id=9999)
        issue = ActiveIssue.from_dict(data)

        assert str(issue) == "[CRITICAL] Disk - C: on Device 9999"
