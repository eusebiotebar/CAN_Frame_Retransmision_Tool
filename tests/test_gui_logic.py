"""Tests for the GUI support logic (REQ-FUNC-INT-*)."""

import threading
from unittest.mock import patch

import pytest

from core.can_logic import CANManager
from core.utils import RuleParsingError, parse_rewrite_rules

# --- Tests for parse_rewrite_rules (REQ-FUNC-INT-007) ---


def test_parse_valid_rules():
    """Verify that valid hex strings are parsed correctly."""
    rules_data = [("100", "200"), ("aBc", "DeF")]
    expected = {0x100: 0x200, 0xABC: 0xDEF}
    assert parse_rewrite_rules(rules_data) == expected


def test_parse_empty_rules_list():
    """Verify that an empty list results in an empty dictionary."""
    assert parse_rewrite_rules([]) == {}


def test_parse_rules_with_empty_rows():
    """Verify that empty or whitespace-only rows are ignored."""
    rules_data = [("100", "200"), ("", "   "), ("  ", "")]
    expected = {0x100: 0x200}
    assert parse_rewrite_rules(rules_data) == expected


def test_parse_invalid_hex_raises_error():
    """Verify that non-hexadecimal strings raise RuleParsingError."""
    rules_data = [("100", "200"), ("GHI", "300")]
    with pytest.raises(RuleParsingError) as excinfo:
        parse_rewrite_rules(rules_data)
    assert excinfo.value.row == 1
    assert "Invalid ID in row 2" in str(excinfo.value)


def test_parse_incomplete_pair_raises_error():
    """Verify that a row with a missing ID raises RuleParsingError."""
    rules_data = [("100", "")]
    with pytest.raises(RuleParsingError) as excinfo:
        parse_rewrite_rules(rules_data)
    assert excinfo.value.row == 0
    assert "Invalid ID in row 1" in str(excinfo.value)


# --- Tests for CANManager channel detection (REQ-FUNC-INT-001) ---


@patch("core.can_logic.CANManager._detect_linux_can_devices", return_value=[])
@patch("core.can_logic.CANManager._detect_windows_can_devices", return_value=[])
@patch("core.can_logic.CANManager._detect_kvaser_devices")
def test_channel_detection_signal(mock_detect_kvaser, mock_detect_win, mock_detect_linux):
    """
    Verify that detect_channels emits the channels_detected signal with correct data.
    Covers: REQ-FUNC-INT-001
    """
    # Arrange
    mock_kvaser_channels = [
        {"interface": "kvaser", "channel": "0", "display_name": "Kvaser Channel 0"}
    ]
    mock_detect_kvaser.return_value = mock_kvaser_channels

    manager = CANManager()

    detected_channels_list = []
    detection_event = threading.Event()

    def on_channels_detected(channels):
        detected_channels_list.extend(channels)
        detection_event.set()

    manager.channels_detected.connect(on_channels_detected)

    # Act
    manager.detect_channels()

    # Assert
    assert detection_event.wait(timeout=2.0), "channels_detected signal timed out"

    # Check for virtual channels
    assert any(ch["interface"] == "virtual" for ch in detected_channels_list)

    # Check for mocked Kvaser channels
    assert any(ch["interface"] == "kvaser" for ch in detected_channels_list)

    # Ensure the exact mocked channel is present
    assert mock_kvaser_channels[0] in detected_channels_list

    # Ensure other detectors were called
    mock_detect_kvaser.assert_called_once()
    # Depending on the platform the test runs on, one of these will be called.
    # For simplicity, we just assert they were called, not which one.
    # In a real CI environment, you might have platform-specific checks.
    assert mock_detect_win.called or mock_detect_linux.called
