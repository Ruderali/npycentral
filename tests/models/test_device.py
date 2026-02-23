"""Tests for the Device model."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from npycentral.models.device import Device
from tests.factories import make_device_data


# ========================================================================
# FROM_DICT TESTS
# ========================================================================

class TestDeviceFromDict:
    """Verify Device.from_dict parses dictionaries correctly."""

    def test_from_dict_creates_device_with_all_fields(self):
        data = make_device_data()
        device = Device.from_dict(data)

        assert device.deviceId == 12345
        assert device.uri == "https://ncentral.test.example.com/api/devices/12345"
        assert device.remoteControlUri is None
        assert device.sourceUri is None
        assert device.longName == "SERVER-DC01"
        assert device.deviceClass == "Windows - Server"
        assert device.description == ""
        assert device.isProbe is False
        assert device.osId == "700000004"
        assert device.supportedOs == "windows_server_2019"
        assert device.discoveredName == "SERVER-DC01"
        assert device.deviceClassLabel == "Windows - Server"
        assert device.supportedOsLabel == "Windows Server 2019"
        assert device.lastLoggedInUser == "DOMAIN\\admin"
        assert device.stillLoggedIn is True
        assert device.licenseMode == "Professional"
        assert device.orgUnitId == 237
        assert device.soId == 50
        assert device.soName == "MSP Service Org"
        assert device.customerId == 237
        assert device.customerName == "Acme Corp"
        assert device.siteId == 500
        assert device.siteName == "Main Office"
        assert device.applianceId == 999
        assert device.lastApplianceCheckinTime == "2025-01-15T10:30:00Z"
        assert device.timezone == ZoneInfo("UTC")
        assert device.assets is None
        assert device._client is None

    def test_from_dict_passes_timezone(self):
        data = make_device_data()
        tz = ZoneInfo("America/New_York")
        device = Device.from_dict(data, timezone=tz)

        assert device.timezone == tz

    def test_from_dict_passes_client_reference(self):
        data = make_device_data()
        mock_client = MagicMock()
        device = Device.from_dict(data, client=mock_client)

        assert device._client is mock_client


# ========================================================================
# LAST_CHECKIN_DATETIME TESTS
# ========================================================================

class TestDeviceLastCheckinDatetime:
    """Verify last_checkin_datetime parsing and timezone conversion."""

    def test_parses_utc_timestamp(self):
        data = make_device_data(lastApplianceCheckinTime="2025-01-15T10:30:00Z")
        device = Device.from_dict(data)

        dt = device.last_checkin_datetime
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
        assert dt.second == 0
        assert dt.tzinfo is not None

    def test_converts_to_eastern_timezone(self):
        data = make_device_data(lastApplianceCheckinTime="2025-01-15T10:30:00Z")
        eastern = ZoneInfo("America/New_York")
        device = Device.from_dict(data, timezone=eastern)

        dt = device.last_checkin_datetime
        assert dt is not None
        # UTC 10:30 -> Eastern is 05:30 (EST is UTC-5)
        assert dt.hour == 5
        assert dt.minute == 30
        assert dt.tzinfo is not None

    def test_returns_none_when_checkin_time_is_none(self):
        data = make_device_data(lastApplianceCheckinTime=None)
        device = Device.from_dict(data)

        assert device.last_checkin_datetime is None


# ========================================================================
# LOAD_ASSETS TESTS
# ========================================================================

class TestDeviceLoadAssets:
    """Verify load_assets lazy-loading, caching, and force_refresh."""

    def test_raises_runtime_error_without_client(self):
        device = Device.from_dict(make_device_data())

        with pytest.raises(RuntimeError, match="Cannot load assets"):
            device.load_assets()

    def test_calls_client_get_device_assets(self):
        mock_client = MagicMock()
        mock_assets = MagicMock()
        mock_client.get_device_assets.return_value = mock_assets
        device = Device.from_dict(make_device_data(), client=mock_client)

        result = device.load_assets()

        mock_client.get_device_assets.assert_called_once_with(12345)
        assert result is mock_assets

    def test_caches_assets_on_second_call(self):
        mock_client = MagicMock()
        mock_assets = MagicMock()
        mock_client.get_device_assets.return_value = mock_assets
        device = Device.from_dict(make_device_data(), client=mock_client)

        device.load_assets()
        device.load_assets()

        mock_client.get_device_assets.assert_called_once()

    def test_force_refresh_re_calls_api(self):
        mock_client = MagicMock()
        mock_assets_1 = MagicMock()
        mock_assets_2 = MagicMock()
        mock_client.get_device_assets.side_effect = [mock_assets_1, mock_assets_2]
        device = Device.from_dict(make_device_data(), client=mock_client)

        first = device.load_assets()
        second = device.load_assets(force_refresh=True)

        assert mock_client.get_device_assets.call_count == 2
        assert first is mock_assets_1
        assert second is mock_assets_2


# ========================================================================
# HAS_ASSETS TESTS
# ========================================================================

class TestDeviceHasAssets:
    """Verify has_assets property before and after loading."""

    def test_false_initially(self):
        device = Device.from_dict(make_device_data())

        assert device.has_assets is False

    def test_true_after_load(self):
        mock_client = MagicMock()
        mock_client.get_device_assets.return_value = MagicMock()
        device = Device.from_dict(make_device_data(), client=mock_client)

        device.load_assets()

        assert device.has_assets is True


# ========================================================================
# DEEP LINK URL TESTS
# ========================================================================

class TestDeviceDeepLinkUrl:
    """Verify get_deep_link_url and convenience URL methods."""

    def test_generates_correct_url_with_port(self):
        device = Device.from_dict(make_device_data(device_id=12345, customer_id=237))
        url = device.get_deep_link_url(
            base_url="https://ncentral.example.com",
            method="deviceDetails",
            ui_port=8443,
            language="en",
        )

        assert url == (
            "https://ncentral.example.com:8443/deepLinkAction.do?"
            "method=deviceDetails&customerID=237&deviceID=12345&language=en"
        )

    def test_generates_url_without_port(self):
        device = Device.from_dict(make_device_data(device_id=12345, customer_id=237))
        url = device.get_deep_link_url(
            base_url="https://ncentral.example.com",
            method="deviceDetails",
            ui_port=None,
            language="en",
        )

        assert url == (
            "https://ncentral.example.com/deepLinkAction.do?"
            "method=deviceDetails&customerID=237&deviceID=12345&language=en"
        )

    def test_generates_url_with_credentials(self):
        device = Device.from_dict(make_device_data(device_id=12345, customer_id=237))
        url = device.get_deep_link_url(
            base_url="https://ncentral.example.com",
            method="deviceDetails",
            ui_port=8443,
            username="admin",
            password="secret",
            language="en",
        )

        assert "username=admin" in url
        assert "password=secret" in url

    def test_get_overview_url(self):
        device = Device.from_dict(make_device_data())
        url = device.get_overview_url(
            base_url="https://ncentral.example.com",
            ui_port=8443,
        )

        assert "method=deviceOverview" in url

    def test_get_details_url(self):
        device = Device.from_dict(make_device_data())
        url = device.get_details_url(
            base_url="https://ncentral.example.com",
            ui_port=8443,
        )

        assert "method=deviceDetails" in url

    def test_get_remote_control_url(self):
        device = Device.from_dict(make_device_data())
        url = device.get_remote_control_url(
            base_url="https://ncentral.example.com",
            ui_port=8443,
        )

        assert "method=deviceRC" in url
