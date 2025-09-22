"""Tests for the GUI support logic (REQ-FUNC-INT-*).

Also covers selected NFRs where feasible via GUI-level checks.
"""

import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QTableWidgetItem

import core.gui as gui_mod
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


def test_default_bitrate_is_500(qapp):
    """
    REQ-FUNC-INT-005: Upon startup or channel selection, bitrate defaults to 500 kbps.
    """
    win = MainWindow()
    assert win.bitrate_combo.currentText() == "500"


def test_two_distinct_selectors_for_channels(qapp):
    """
    REQ-FUNC-INT-002: GUI presents separate selectors for input and output channels.
    """
    win = MainWindow()
    assert win.input_channel_combo is not win.output_channel_combo


def test_same_channel_selection_is_prevented(qapp, monkeypatch):
    """
    REQ-FUNC-INT-003: Same channel for input and output triggers an error and prevents start.
    REQ-NFR-USA-004: Error message is clear and actionable for the user.
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


def test_set_default_log_path_non_frozen(qapp, monkeypatch, tmp_path):
    """Default log path is generated under CWD/LOGS when not frozen."""
    win = MainWindow()

    # Simulate non-frozen and temporary CWD
    monkeypatch.setattr(gui_mod.sys, "frozen", False, raising=False)
    monkeypatch.chdir(tmp_path)

    win._set_default_log_path()
    text = win.log_file_path_edit.text()
    assert text
    p = Path(text)
    assert p.parent.name == "LOGS"
    assert p.suffix == ".csv"


def test_get_rewrite_rules_error_path_selects_row(qapp, monkeypatch):
    """On RuleParsingError, GUI selects the failing row and shows a clear error."""
    win = MainWindow()

    # Insert an invalid row to trigger error on parse
    win.mapping_table.setRowCount(2)
    win.mapping_table.setItem(0, 0, QTableWidgetItem("100"))
    win.mapping_table.setItem(0, 1, QTableWidgetItem("200"))
    win.mapping_table.setItem(1, 0, QTableWidgetItem("GHI"))
    win.mapping_table.setItem(1, 1, QTableWidgetItem("1"))

    captured = []

    def fake_error(title, text):
        captured.append((title, text))

    monkeypatch.setattr(win, "_show_error_message", fake_error)

    rules = win._get_rewrite_rules()
    assert rules is None
    # Error message was shown
    assert captured and ("Mapping Error" in captured[-1][0])
    # Failing row is selected (row index from RuleParsingError)
    assert win.mapping_table.currentRow() == 1


def test_latest_frames_view_exists(qapp):
    """
    REQ-FUNC-INT-010: Latest frames tables exist and are configured.
    This test validates presence and basic configuration only.
    """
    win = MainWindow()
    # Test both channel frame tables exist and are configured
    assert win.frames_table_RX_Channel0.columnCount() == 4
    assert win.frames_table_TX_Channel0.columnCount() == 4
    assert win.frames_table_RX_Channel1.columnCount() == 4
    assert win.frames_table_TX_Channel1.columnCount() == 4


def test_bitrate_applied_on_start(qapp, monkeypatch):
    """
    REQ-FUNC-INT-004: The system uses the user-selected bitrate for both channels when starting.
    """
    win = MainWindow()

    # Prepare two channels
    channels = [
        {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
        {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
    ]
    win._populate_channel_selectors(channels)
    win.input_channel_combo.setCurrentIndex(0)
    win.output_channel_combo.setCurrentIndex(1)

    # Change bitrate selection to 500 kbps
    idx = win.bitrate_combo.findText("500")
    if idx >= 0:
        win.bitrate_combo.setCurrentIndex(idx)

    captured = {}

    def fake_start(input_cfg, output_cfg, rewrite_rules, log_file):
        captured["input"] = input_cfg
        captured["output"] = output_cfg
        captured["rules"] = rewrite_rules
        captured["log_file"] = log_file

    monkeypatch.setattr(win.can_manager, "start_retransmission", fake_start)

    # Ensure empty mapping accepted
    win.mapping_table.setRowCount(0)

    # Act
    win._on_start_stop_clicked()

    assert "input" in captured and "output" in captured
    assert captured["input"]["bitrate"] == captured["output"]["bitrate"]
    assert captured["input"]["bitrate"] in (250000, 500000)
    # If combo had 500, ensure 500000; otherwise default 250000
    if idx >= 0:
        assert captured["input"]["bitrate"] == 500000


def test_mapping_table_used_on_start(qapp, monkeypatch):
    """
    REQ-FUNC-INT-006: The user-defined ID mapping table is parsed and applied when starting.
    REQ-FUNC-INT-007: IDs must be valid hex (verified indirectly via parse).
    """
    win = MainWindow()

    # Prepare channels
    channels = [
        {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
        {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
    ]
    win._populate_channel_selectors(channels)
    win.input_channel_combo.setCurrentIndex(0)
    win.output_channel_combo.setCurrentIndex(1)

    # Add a valid mapping rule 0x100 -> 0x200
    win.mapping_table.setRowCount(1)
    win.mapping_table.setItem(0, 0, QTableWidgetItem("100"))
    win.mapping_table.setItem(0, 1, QTableWidgetItem("200"))

    captured = {}

    def fake_start(input_cfg, output_cfg, rewrite_rules, log_file):
        captured["rules"] = dict(rewrite_rules)

    monkeypatch.setattr(win.can_manager, "start_retransmission", fake_start)

    # Act
    win._on_start_stop_clicked()

    assert captured.get("rules") == {0x100: 0x200}


def test_start_stop_button_toggles(qapp, monkeypatch):
    """
    REQ-FUNC-INT-008: The GUI provides a Start/Stop button that toggles states.
    """
    win = MainWindow()

    # Prepare channels
    channels = [
        {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
        {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
    ]
    win._populate_channel_selectors(channels)
    win.input_channel_combo.setCurrentIndex(0)
    win.output_channel_combo.setCurrentIndex(1)

    # No-op starts/stops
    monkeypatch.setattr(win.can_manager, "start_retransmission", lambda *args, **kwargs: None)
    monkeypatch.setattr(win.can_manager, "stop_retransmission", lambda *args, **kwargs: None)

    # Start
    win._on_start_stop_clicked()
    assert win.is_running is True
    assert win.start_stop_button.text() == "Stop"

    # Stop
    win._on_start_stop_clicked()
    assert win.is_running is False
    assert win.start_stop_button.text() == "Start"


def test_ui_timestamps_include_milliseconds(qapp):
    """
    REQ-NFR-USA-002: The timestamps in the UI include milliseconds and match
    the underlying message timestamp within a small tolerance.
    """
    win = MainWindow()

    # Simulate running state so rows are added
    win.is_running = True

    class DummyMsg:
        def __init__(self, ts: float) -> None:
            self.timestamp = ts
            self.arbitration_id = 0x1AA
            self.dlc = 2
            self.data = bytes([0x01, 0x02])

    ts = 1726480000.1234
    # Test adding frame to channel 1 (input channel)
    win._add_received_frame_to_view(DummyMsg(ts), channel=1)

    # Read back the timestamp text from the RX table for channel 1
    item = win.frames_table_RX_Channel1.item(0, 0)
    assert item is not None
    text = item.text()

    # Expect exactly 3 decimals as per GUI formatting and close to original
    assert "." in text and len(text.split(".")[-1]) == 3
    assert abs(float(text) - ts) < 0.002  # within 2 ms


def test_about_dialog_contains_disclaimer(qapp, monkeypatch):
    """
    REQ-NFR-SAF-001, REQ-NFR-SAF-002: The About dialog presents a disclaimer
    stating the tool is not intended for safety-critical control and warns
    about unintended side effects when retransmitting frames.
    """
    win = MainWindow()

    captured = {}

    def fake_about(parent, title, text):  # noqa: ARG001
        captured["title"] = title
        captured["text"] = text

    # Patch QMessageBox.about used in the GUI module to avoid real dialog
    monkeypatch.setattr(gui_mod.QMessageBox, "about", fake_about)

    win._show_about_dialog()

    assert captured.get("title")
    about_html = captured.get("text", "")
    # Normalize whitespace for robust matching
    normalized = " ".join(about_html.split())
    # Check for key phrases in the disclaimer
    assert ("Safety Warning" in normalized) or ("Warning" in normalized)
    assert ("not be used to control safety-critical systems" in normalized) or (
        "safety-critical" in normalized
    )


def test_mapping_error_message_is_clear(qapp, monkeypatch):
    """
    REQ-NFR-USA-004: Error messages and UI feedback SHALL be clear and actionable.
    Trigger a mapping validation error and verify the shown message indicates the cause.
    """
    win = MainWindow()

    # Prepare valid channels so the flow reaches mapping parsing
    channels = [
        {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
        {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
    ]
    win._populate_channel_selectors(channels)
    win.input_channel_combo.setCurrentIndex(0)
    win.output_channel_combo.setCurrentIndex(1)

    # Add an invalid mapping row to provoke RuleParsingError
    win.mapping_table.setRowCount(1)
    win.mapping_table.setItem(0, 0, QTableWidgetItem("GHI"))
    win.mapping_table.setItem(0, 1, QTableWidgetItem("200"))

    captured = []

    def fake_error(title, text):
        captured.append((title, text))

    monkeypatch.setattr(win, "_show_error_message", fake_error)

    # Act: attempt to start, should hit mapping error and not start
    win._on_start_stop_clicked()

    assert captured, "Expected an error message for invalid mapping"
    title, text = captured[-1]
    assert "Invalid ID in row" in text or "Mapping Error" in title
    assert win.is_running is False


def test_handle_error_resets_ui(qapp, monkeypatch):
    """_handle_error should stop running state and reset controls and labels without blocking."""
    win = MainWindow()
    # Avoid modal dialog during tests
    monkeypatch.setattr(win, "_show_error_message", lambda *args, **kwargs: None)
    win.is_running = True
    win.start_stop_button.setText("Stop")
    win._set_controls_enabled(False)

    win._handle_error("Some error")

    assert win.is_running is False
    assert win.start_stop_button.text() == "Start"
    # Status label should reflect error and indicator should be red
    assert win.status_label.text() == "Error"
    assert "background-color: red" in win.status_indicator.styleSheet()


def test_browse_log_file_updates_path(qapp, monkeypatch, tmp_path):
    """Simulate browse dialog to ensure selected path is applied to QLineEdit."""
    win = MainWindow()
    target = str(tmp_path / "mylog.csv")

    def fake_getSaveFileName(*args, **kwargs):  # noqa: ARG001
        return target, "CSV files (*.csv)"

    monkeypatch.setattr(gui_mod.QFileDialog, "getSaveFileName", fake_getSaveFileName)

    win._on_browse_log_file()
    assert win.log_file_path_edit.text() == target


def test_recovery_signals_update_status(qapp):
    """Recovery signals should update the status label and color accordingly."""
    win = MainWindow()
    # Emit signals from the manager and verify UI changes
    win.can_manager.recovery_started.emit()
    assert win.status_label.text() == "Reconnecting…"
    assert "orange" in win.status_indicator.styleSheet()

    win.can_manager.recovery_succeeded.emit()
    assert win.status_label.text() == "Retransmitting"
    assert "green" in win.status_indicator.styleSheet()


# --- Tests for new functionality (Settings Dialog and CSV Header Support) ---


def test_header_line_detection():
    """
    Covers: REQ-FUNC-INT-013

    Test that header lines are correctly detected and skipped.
    """
    from core.gui import MainWindow
    
    win = MainWindow()
    
    # Test obvious header lines
    assert win._is_likely_header_line("Original ID", "New ID")
    assert win._is_likely_header_line("FROM", "TO")
    assert win._is_likely_header_line("Source CAN ID", "Target ID")
    
    # Test valid hex data (should not be detected as header)
    assert not win._is_likely_header_line("100", "200")
    assert not win._is_likely_header_line("0x1A2B", "0x3C4D")
    assert not win._is_likely_header_line("ABC", "DEF")
    
    # Test mixed cases
    assert win._is_likely_header_line("ID", "Value")
    assert win._is_likely_header_line("old_id", "new_id")


def test_csv_import_with_headers(qapp, tmp_path, monkeypatch):
    """
    Covers: REQ-FUNC-INT-013

    Test CSV import functionality with header lines.
    """
    # Create a CSV file with headers
    csv_file = tmp_path / "test_mapping.csv"
    csv_content = """Original ID,Rewritten ID
100,200
ABC,DEF
0x1A2,0x3B4
"""
    csv_file.write_text(csv_content)
    
    # Mock the file dialog to return our test file
    monkeypatch.setattr("PyQt6.QtWidgets.QFileDialog.getOpenFileName", 
                       lambda *args, **kwargs: (str(csv_file), ""))
    
    win = MainWindow()
    
    # Call the import function
    win._on_import_mapping()
    
    # Check that the mapping table was populated correctly (excluding header)
    assert win.mapping_table.rowCount() == 3
    
    # Check the actual data
    it = win.mapping_table.item(0, 0)
    assert it is not None and it.text() == "100"
    it = win.mapping_table.item(0, 1)
    assert it is not None and it.text() == "200"
    it = win.mapping_table.item(1, 0)
    assert it is not None and it.text() == "ABC"
    it = win.mapping_table.item(1, 1)
    assert it is not None and it.text() == "DEF"
    it = win.mapping_table.item(2, 0)
    assert it is not None and it.text() == "1A2"
    it = win.mapping_table.item(2, 1)
    assert it is not None and it.text() == "3B4"


def test_csv_export_with_headers(qapp, tmp_path, monkeypatch):
    """
    Covers: REQ-FUNC-INT-014

    Test CSV export functionality that includes header lines.
    """
    # Mock the file dialog to return our test file
    export_file = tmp_path / "exported_mapping.csv"
    monkeypatch.setattr("PyQt6.QtWidgets.QFileDialog.getSaveFileName", 
                       lambda *args, **kwargs: (str(export_file), ""))
    
    win = MainWindow()
    
    # Add some test data to the mapping table
    win.mapping_table.setRowCount(2)
    win.mapping_table.setItem(0, 0, QTableWidgetItem("100"))
    win.mapping_table.setItem(0, 1, QTableWidgetItem("200"))
    win.mapping_table.setItem(1, 0, QTableWidgetItem("ABC"))
    win.mapping_table.setItem(1, 1, QTableWidgetItem("DEF"))
    
    # Call the export function
    win._on_export_mapping()
    
    # Check that the file was created with headers
    exported_content = export_file.read_text()
    lines = exported_content.strip().split('\n')
    
    assert len(lines) == 3  # Header + 2 data lines
    assert lines[0] == "Original ID,Rewritten ID"
    assert lines[1] == "100,200"
    assert lines[2] == "ABC,DEF"


def test_settings_dialog_creation(qapp):
    """
    Covers: REQ-FUNC-INT-015

    Test that settings dialog can be created and initialized.
    """
    from core.gui import MainWindow
    from core.settings_dialog import SettingsDialog
    
    parent = MainWindow()
    dialog = SettingsDialog(parent)
    
    # Test that dialog has the expected tabs
    assert dialog.settingsTabWidget.count() == 3
    assert dialog.settingsTabWidget.tabText(0) == "Connection"
    assert dialog.settingsTabWidget.tabText(1) == "Logging"
    assert dialog.settingsTabWidget.tabText(2) == "Advanced Throttling"


def test_settings_dialog_get_set_settings(qapp):
    """
    Covers: REQ-FUNC-INT-015, REQ-FUNC-INT-016

    Test settings dialog get/set functionality.
    """
    from core.gui import MainWindow
    from core.settings_dialog import SettingsDialog
    
    parent = MainWindow()
    dialog = SettingsDialog(parent)
    
    # Test initial settings
    initial_settings = dialog.get_settings()
    assert "connection" in initial_settings
    assert "logging" in initial_settings
    assert "throttling" in initial_settings
    
    # Test setting new values
    test_settings = {
        "connection": {
            "input_channel_index": 1,
            "output_channel_index": 2,
            "bitrate": "1000",
        },
        "logging": {
            "log_file_path": "/test/path/logfile.csv",
        },
        "throttling": {
            "max_send_retries": "5",
            "send_retry_initial_delay": "0.02",
            "tx_min_gap": "0.001",
            "tx_overflow_cooldown": "0.1",
        },
    }
    
    dialog.set_settings(test_settings)
    retrieved_settings = dialog.get_settings()
    
    assert retrieved_settings["connection"]["bitrate"] == "1000"
    assert retrieved_settings["logging"]["log_file_path"] == "/test/path/logfile.csv"
    assert retrieved_settings["throttling"]["max_send_retries"] == "5"


def test_settings_file_save_load(qapp, tmp_path):
    """
    Covers: REQ-FUNC-INT-016

    Test settings dialog file save/load functionality.
    """
    from core.gui import MainWindow
    from core.settings_dialog import SettingsDialog
    
    parent = MainWindow()
    dialog = SettingsDialog(parent)
    
    # Create test settings
    test_settings = {
        "connection": {
            "input_channel_index": 1,
            "output_channel_index": 2,
            "bitrate": "1000",
        },
        "logging": {
            "log_file_path": "/test/path/logfile.csv",
        },
        "throttling": {
            "max_send_retries": "15",
            "send_retry_initial_delay": "0.05",
            "tx_min_gap": "0.002",
            "tx_overflow_cooldown": "0.2",
        },
    }
    
    # Save settings to file
    settings_file = tmp_path / "test_settings.json"
    dialog.set_settings(test_settings)
    dialog.save_settings_to_file(str(settings_file))
    
    # Create new dialog and load settings
    dialog2 = SettingsDialog(parent)
    dialog2.load_settings_from_file(str(settings_file))
    
    loaded_settings = dialog2.get_settings()
    assert loaded_settings["connection"]["bitrate"] == "1000"
    assert loaded_settings["throttling"]["max_send_retries"] == "15"


def test_main_window_settings_integration(qapp):
    """
    Covers: REQ-FUNC-INT-012, REQ-FUNC-INT-015

    Test that main window properly integrates with settings dialog.
    """
    win = MainWindow()
    
    # Test initial settings exist
    assert hasattr(win, 'current_settings')
    assert "connection" in win.current_settings
    assert "logging" in win.current_settings
    assert "throttling" in win.current_settings
    
    # Test settings dialog creation
    assert win.settings_dialog is None
    win._on_open_settings()  # This should create the dialog
    assert win.settings_dialog is not None


def test_menu_actions_exist(qapp):
    """
    Covers: REQ-FUNC-INT-011, REQ-FUNC-INT-012

    Test that all new menu actions are properly connected.
    """
    win = MainWindow()
    
    # Test that menu actions exist
    assert hasattr(win, 'actionImport')
    assert hasattr(win, 'actionExport') 
    assert hasattr(win, 'actionExit')
    assert hasattr(win, 'actionOpenSettings')
    assert hasattr(win, 'actionSaveSettings')
    assert hasattr(win, 'actionLoadSettings')


def test_csv_import_mixed_separators(qapp, tmp_path, monkeypatch):
    """
    Covers: REQ-FUNC-INT-013

    Test CSV import with different separators and malformed lines.
    """
    csv_file = tmp_path / "mixed_separators.csv"
    csv_content = """Original ID;New ID
100,200
ABC;DEF
# This is a comment line
   
1A2 3B4
invalid_line_with_one_column
0x5E6,0x7F8
"""
    csv_file.write_text(csv_content)
    
    monkeypatch.setattr("PyQt6.QtWidgets.QFileDialog.getOpenFileName", 
                       lambda *args, **kwargs: (str(csv_file), ""))
    
    win = MainWindow()
    win._on_import_mapping()
    
    # Should have imported 4 valid rows (excluding header, comments, empty lines, invalid lines)
    assert win.mapping_table.rowCount() == 4
    
    it = win.mapping_table.item(0, 0)
    assert it is not None and it.text() == "100"
    it = win.mapping_table.item(1, 0)
    assert it is not None and it.text() == "ABC"
    it = win.mapping_table.item(2, 0)
    assert it is not None and it.text() == "1A2"
    it = win.mapping_table.item(3, 0)
    assert it is not None and it.text() == "5E6"
