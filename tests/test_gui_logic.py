"""Tests for the GUI support logic (REQ-FUNC-INT-*)."""

import threading
from unittest.mock import patch

import pytest

from core.can_logic import CANManager
from core.gui import MainWindow
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


# --- GUI behavior tests (REQ-FUNC-INT-002 .. 010) ---


def test_default_bitrate_is_250(qapp):
    """
    REQ-FUNC-INT-005: Upon startup or channel selection, bitrate defaults to 250 kbps.
    """
    win = MainWindow()
    assert win.bitrate_combo.currentText() == "250"


def test_two_distinct_selectors_for_channels(qapp):
    """
    REQ-FUNC-INT-002: GUI presents separate selectors for input and output channels.
    """
    win = MainWindow()
    assert win.input_channel_combo is not win.output_channel_combo


def test_same_channel_selection_is_prevented(qapp, monkeypatch):
    """
    REQ-FUNC-INT-003: Same channel for input and output triggers an error and prevents start.
    """
    win = MainWindow()

    # Populate with two channels manually
    channels = [
        {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
        {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
    ]
    win._populate_channel_selectors(channels)

    # Select same channel index for both
    win.input_channel_combo.setCurrentIndex(0)
    win.output_channel_combo.setCurrentIndex(0)

    # Intercept error dialog
    errors = []

    def fake_error(title, text):
        errors.append((title, text))

    monkeypatch.setattr(win, "_show_error_message", fake_error)

    # Attempt to start
    win._on_start_stop_clicked()

    assert errors, "Expected configuration error when selecting the same channel"
    assert any("cannot be the same" in e[1] for e in errors)
    assert win.is_running is False


def test_status_indicator_changes(qapp, monkeypatch):
    """
    REQ-FUNC-INT-009: Status label and indicator update appropriately.
    """
    win = MainWindow()
    win.update_status("Listening", "green")
    assert win.status_label.text() == "Listening"
    # Basic check on style change applied
    assert "background-color: green" in win.status_indicator.styleSheet()


def test_latest_frames_view_exists(qapp):
    """
    REQ-FUNC-INT-010: Latest frames tables exist and are configured.
    This test validates presence and basic configuration only.
    """
    win = MainWindow()
    assert win.frames_table_RX.columnCount() == 4
    assert win.frames_table_TX.columnCount() == 4
