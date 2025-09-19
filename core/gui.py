"""Main UI for the CAN_ID_Reframe tool.

Contains only logic and signal wiring.
"""

from __future__ import annotations

import contextlib
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import (QComboBox, QDialog, QFileDialog, QGroupBox,
                             QHeaderView, QLabel, QLineEdit, QMainWindow,
                             QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem)
from PyQt6.uic.load_ui import loadUi

from .can_logic import CANManager
from .settings_dialog import SettingsDialog
from .utils import RuleParsingError, get_resource_path, parse_rewrite_rules
from .version import __version__


class MainWindow(QMainWindow):
    """Main application window."""

    # Hints for linters to know the attributes injected by loadUi
    # Note: Connection, logging, and throttling controls are now in settings dialog
    frames_table_RX: QTableWidget
    frames_table_TX: QTableWidget
    mapping_table: QTableWidget
    add_rule_button: QPushButton
    delete_rule_button: QPushButton
    start_stop_button: QPushButton
    status_label: QLabel
    status_indicator: QLabel
    # Menu actions
    actionImport: Any  # QAction
    actionExport: Any  # QAction
    actionExit: Any  # QAction
    actionOpenSettings: Any  # QAction
    actionSaveSettings: Any  # QAction
    actionLoadSettings: Any  # QAction
    actionAcerca_de: Any  # QAction
    mapping_group: QGroupBox

    def __init__(self) -> None:
        super().__init__()
        ui_file = Path(__file__).with_name("gui.ui")
        if not ui_file.exists():
            raise FileNotFoundError(f"Interface file not found: {ui_file}")
        loadUi(str(ui_file), self)

        self.setWindowTitle(f"CAN ID Reframe Tool v{__version__}")
        # Set specific window icon (fallback if application icon not used)
        try:
            icon_path = get_resource_path("resources", "images", "app_icon.ico")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                # Fallback to SVG if ICO is unavailable during dev
                svg_path = get_resource_path("resources", "images", "can_relay_icon.svg")
                if svg_path.exists():
                    self.setWindowIcon(QIcon(str(svg_path)))
        except Exception:
            pass
        
        self.can_manager = CANManager()
        self.is_running = False
        self.settings_dialog = None
        
        # Current settings (will be managed through settings dialog)
        self.current_settings = {
            "connection": {
                "input_channel_index": 0,
                "output_channel_index": 1,
                "bitrate": "500",
            },
            "logging": {
                "log_file_path": "",
            },
            "throttling": {
                "max_send_retries": "10",
                "send_retry_initial_delay": "0.01",
                "tx_min_gap": "0.0",
                "tx_overflow_cooldown": "0.05",
            },
        }

        self._configure_widgets()
        self._connect_signals()
        self.update_status("Disconnected", "grey")
        self.can_manager.detect_channels()

    # ------------------------------------------------------------------
    # Initial widget configuration
    # ------------------------------------------------------------------
    def _configure_widgets(self) -> None:
        # Frame tables configuration
        self._configure_frame_table(self.frames_table_RX)
        self._configure_frame_table(self.frames_table_TX)

        # Mapping table
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["Original ID (Hex)", "Rewritten ID (Hex)"])
        m_header = self.mapping_table.horizontalHeader()
        if m_header is not None:
            m_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # About action
        if getattr(self, "actionAcerca_de", None):
            with contextlib.suppress(Exception):  # pragma: no cover
                self.actionAcerca_de.triggered.connect(self._show_about_dialog)

    def _configure_frame_table(self, table: QTableWidget) -> None:
        """Configure a frame table with standard settings."""
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Timestamp", "ID (Hex)", "DLC", "Data (Hex)"])
        table.setEditTriggers(table.EditTrigger.NoEditTriggers)
        header = table.horizontalHeader()
        if header is not None:  # Defense against static analysis
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self.can_manager.error_occurred.connect(self._handle_error)
        self.can_manager.frame_received.connect(self._add_received_frame_to_view)
        self.can_manager.frame_retransmitted.connect(self._add_transmitted_frame_to_view)
        # Recovery lifecycle to inform user about reconnect attempts
        self.can_manager.recovery_started.connect(
            lambda: self.update_status("Reconnecting…", "orange")
        )
        self.can_manager.recovery_succeeded.connect(
            lambda: self.update_status("Retransmitting", "green")
        )
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        self.add_rule_button.clicked.connect(self._on_add_rule)
        self.delete_rule_button.clicked.connect(self._on_delete_rule)
        
        # Menu actions - File menu
        if getattr(self, "actionImport", None):
            self.actionImport.triggered.connect(self._on_import_mapping)
        if getattr(self, "actionExport", None):
            self.actionExport.triggered.connect(self._on_export_mapping)
        if getattr(self, "actionExit", None):
            self.actionExit.triggered.connect(self.close)
            
        # Menu actions - Settings menu
        if getattr(self, "actionOpenSettings", None):
            self.actionOpenSettings.triggered.connect(self._on_open_settings)
        if getattr(self, "actionSaveSettings", None):
            self.actionSaveSettings.triggered.connect(self._on_save_settings)
        if getattr(self, "actionLoadSettings", None):
            self.actionLoadSettings.triggered.connect(self._on_load_settings)

    # ------------------------------------------------------------------
    # UI utilities
    # ------------------------------------------------------------------
    def update_status(self, message: str, color: str) -> None:
        self.status_label.setText(message)
        self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

    # ------------------------------------------------------------------
    # Frame reception and transmission
    # ------------------------------------------------------------------
    def _add_received_frame_to_view(self, msg) -> None:  # msg comes from python-can
        """Add a received CAN frame to the RX table."""
        self._add_frame_to_table(self.frames_table_RX, msg)

    def _add_transmitted_frame_to_view(self, msg) -> None:  # msg comes from python-can
        """Add a transmitted CAN frame to the TX table."""
        self._add_frame_to_table(self.frames_table_TX, msg)

    def _add_frame_to_table(self, table: QTableWidget, msg) -> None:
        """Add a CAN frame to the specified table."""
        if not self.is_running:
            return
        table.insertRow(0)
        table.setItem(0, 0, QTableWidgetItem(f"{msg.timestamp:.3f}"))
        table.setItem(0, 1, QTableWidgetItem(f"{msg.arbitration_id:X}"))
        table.setItem(0, 2, QTableWidgetItem(str(msg.dlc)))
        table.setItem(0, 3, QTableWidgetItem(msg.data.hex().upper()))
        if table.rowCount() > 100:
            table.removeRow(100)

    # ------------------------------------------------------------------
    # Rewrite rules
    # ------------------------------------------------------------------
    def _on_add_rule(self) -> None:
        self.mapping_table.insertRow(self.mapping_table.rowCount())

    def _on_delete_rule(self) -> None:
        if self.mapping_table.currentRow() >= 0:
            self.mapping_table.removeRow(self.mapping_table.currentRow())

    def _on_import_mapping(self) -> None:
        """Import ID mapping from a CSV-like file with two hex columns.
        Now supports files with header lines."""
        fileName, _ = QFileDialog.getOpenFileName(
            self,
            "Import ID Mapping",
            "",
            "CSV files (*.csv);;Text files (*.txt);;All files (*)",
        )
        if not fileName:
            return
        try:
            rows: list[tuple[str, str]] = []
            with open(fileName, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Allow separators: comma or semicolon or whitespace
                    sep = "," if "," in line else ";" if ";" in line else None
                    parts = [p.strip() for p in (line.split(sep) if sep else line.split())]
                    if len(parts) < 2:
                        # Skip invalid/incomplete lines silently
                        continue
                    
                    # Try to detect header lines by checking if the values look like hex IDs
                    # Header lines often contain text like "Original ID", "New ID", etc.
                    orig_part = parts[0].strip()
                    rew_part = parts[1].strip()
                    
                    # Skip potential header lines that don't look like hex values
                    if self._is_likely_header_line(orig_part, rew_part):
                        continue
                    
                    rows.append((orig_part, rew_part))

            # Validate by parsing with existing logic
            _ = parse_rewrite_rules(rows)

            # Populate mapping table
            self.mapping_table.setRowCount(0)
            for orig, rew in rows:
                r = self.mapping_table.rowCount()
                self.mapping_table.insertRow(r)
                self.mapping_table.setItem(r, 0, QTableWidgetItem(orig.upper()))
                self.mapping_table.setItem(r, 1, QTableWidgetItem(rew.upper()))
        except Exception as e:
            self._show_error_message("Import Error", f"Failed to import mapping: {e}")

    def _is_likely_header_line(self, col1: str, col2: str) -> bool:
        """Detect if a line is likely a header line rather than hex data."""
        # Check for common header keywords
        header_keywords = [
            "original", "new", "source", "target", "from", "to", "id", "can", 
            "old", "rewrite", "mapping", "input", "output", "hex"
        ]
        
        col1_lower = col1.lower()
        col2_lower = col2.lower()
        
        # If either column contains header keywords, it's likely a header
        for keyword in header_keywords:
            if keyword in col1_lower or keyword in col2_lower:
                return True
        
        # Check if the values don't look like hex (CAN IDs are typically hex)
        # Valid hex CAN IDs would be in format like 0x123, 123, etc.
        try:
            # Remove common hex prefixes for testing
            test_col1 = col1.replace("0x", "").replace("0X", "")
            test_col2 = col2.replace("0x", "").replace("0X", "")
            
            # If both values are pure hex digits (1-8 chars for CAN IDs), probably not a header
            if (test_col1.isdigit() or all(c in "0123456789ABCDEFabcdef" for c in test_col1)) and \
               (test_col2.isdigit() or all(c in "0123456789ABCDEFabcdef" for c in test_col2)) and \
               1 <= len(test_col1) <= 8 and 1 <= len(test_col2) <= 8:
                return False
        except:
            pass
        
        # If we can't determine it's hex data, treat as potential header if it contains non-hex chars
        return not (col1.replace("0x", "").replace("0X", "").replace(" ", "").isalnum() and 
                   col2.replace("0x", "").replace("0X", "").replace(" ", "").isalnum())

    def _on_export_mapping(self) -> None:
        """Export current ID mapping to a CSV file with two hex columns.
        Now includes header line for clarity."""
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Export ID Mapping", "", "CSV files (*.csv);;All files (*)"
        )
        if not fileName:
            return
        try:
            # Gather rows from table
            rows: list[tuple[str, str]] = []
            for row in range(self.mapping_table.rowCount()):
                orig_item = self.mapping_table.item(row, 0)
                rew_item = self.mapping_table.item(row, 1)
                orig = (orig_item.text() if orig_item else "").strip()
                rew = (rew_item.text() if rew_item else "").strip()
                if not orig and not rew:
                    continue
                rows.append((orig, rew))

            # Validate mapping before saving
            _ = parse_rewrite_rules(rows)

            with open(fileName, "w", encoding="utf-8", newline="") as f:
                # Write header line for clarity
                f.write("Original ID,Rewritten ID\n")
                for orig, rew in rows:
                    f.write(f"{orig.upper()},{rew.upper()}\n")
        except Exception as e:
            self._show_error_message("Export Error", f"Failed to export mapping: {e}")

    def _get_rewrite_rules(self):
        table_data = []
        for row in range(self.mapping_table.rowCount()):
            orig_item = self.mapping_table.item(row, 0)
            rew_item = self.mapping_table.item(row, 1)
            orig = orig_item.text() if orig_item else ""
            rew = rew_item.text() if rew_item else ""
            if orig.strip() or rew.strip():
                table_data.append((orig, rew))
        try:
            return parse_rewrite_rules(table_data)
        except RuleParsingError as e:
            self._show_error_message("Mapping Error", str(e))
            self.mapping_table.selectRow(e.row)
            return None

    # ------------------------------------------------------------------
    # Execution control
    # ------------------------------------------------------------------
    def _set_controls_enabled(self, enabled: bool) -> None:
        """Enable or disable UI controls based on running state."""
        self.mapping_group.setEnabled(enabled)

    def _on_start_stop_clicked(self) -> None:
        if self.is_running:
            self.can_manager.stop_retransmission()
            self.update_status("Stopped", "grey")
            self.start_stop_button.setText("Start")
            self._set_controls_enabled(True)
            self.is_running = False
            return

        # Get settings from current configuration
        # For now, assume we have stored channels from the last detection
        # In a more complete implementation, this would use stored channel data
        channels = [
            {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
            {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
        ]
        
        if not channels:
            self._show_error_message("Configuration Error", "No channels detected.")
            return
            
        input_index = self.current_settings["connection"]["input_channel_index"]
        output_index = self.current_settings["connection"]["output_channel_index"]
        
        if input_index >= len(channels) or output_index >= len(channels):
            self._show_error_message("Configuration Error", "Selected channels are not available.")
            return
            
        input_data = channels[input_index]
        output_data = channels[output_index]
        
        if input_data["channel"] == output_data["channel"]:
            self._show_error_message(
                "Configuration Error", "Input and output channel cannot be the same."
            )
            return
            
        try:
            bitrate = int(self.current_settings["connection"]["bitrate"]) * 1000
        except ValueError:
            self._show_error_message("Configuration Error", "Invalid bitrate.")
            return
            
        rewrite_rules = self._get_rewrite_rules()
        if rewrite_rules is None:
            return

        log_file = self.current_settings["logging"]["log_file_path"] or None

        input_cfg = {
            "interface": input_data["interface"],
            "channel": input_data["channel"],
            "bitrate": bitrate,
        }
        output_cfg = {
            "interface": output_data["interface"],
            "channel": output_data["channel"],
            "bitrate": bitrate,
        }
        
        # Apply throttle options from settings
        def _get_float(value: str, default: float) -> float:
            try:
                return float(value) if value else default
            except Exception:
                return default

        def _get_int(value: str, default: int) -> int:
            try:
                return int(value) if value else default
            except Exception:
                return default

        # Use throttling settings from current configuration
        max_send_retries = _get_int(self.current_settings["throttling"]["max_send_retries"], 10)
        send_retry_initial_delay = _get_float(
            self.current_settings["throttling"]["send_retry_initial_delay"], 0.01
        )
        tx_min_gap = _get_float(self.current_settings["throttling"]["tx_min_gap"], 0.0)
        tx_overflow_cooldown = _get_float(
            self.current_settings["throttling"]["tx_overflow_cooldown"], 0.05
        )

        self.can_manager.set_throttle_options(
            max_send_retries=max_send_retries,
            send_retry_initial_delay=send_retry_initial_delay,
            tx_min_gap=tx_min_gap,
            tx_overflow_cooldown=tx_overflow_cooldown,
        )

        self.can_manager.start_retransmission(input_cfg, output_cfg, rewrite_rules, log_file)
        self.update_status("Retransmitting", "green")
        self.start_stop_button.setText("Stop")
        self._set_controls_enabled(False)
        self.is_running = True

    # ------------------------------------------------------------------
    # Errors / dialogs
    # ------------------------------------------------------------------
    def _handle_error(self, error_message: str) -> None:
        self._show_error_message("Error", error_message)
        if self.is_running:
            self.update_status("Error", "red")
            self.start_stop_button.setText("Start")
            self._set_controls_enabled(True)
            self.is_running = False

    def _show_error_message(self, title: str, text: str) -> None:
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def _show_about_dialog(self) -> None:
        about_text = f"""
            <h2>CAN ID Reframe Tool</h2>
            <p>Version: {__version__}</p>
            <p>This tool allows retransmission of CAN frames between two channels, 
            with the ability to rewrite IDs on the fly.</p>
            <hr>
            <p><b>Safety Warning (REQ-NFR-SAF-002):</b></p>
            <p>Be aware of possible unintended side effects when 
            retransmitting and modifying CAN frames on an active bus. This tool is 
            for diagnostic and development purposes and should not be used to 
            control safety-critical systems.</p>
        """
        QMessageBox.about(self, "About CAN ID Reframe Tool", about_text)

    # ------------------------------------------------------------------
    # Menu action handlers
    # ------------------------------------------------------------------
    def _on_open_settings(self) -> None:
        """Open the settings dialog."""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        
        # Load current settings into dialog
        self.settings_dialog.set_settings(self.current_settings)
        
        if self.settings_dialog.exec() == QDialog.DialogCode.Accepted:
            # Get updated settings from dialog
            self.current_settings = self.settings_dialog.get_settings()
    
    def _on_save_settings(self) -> None:
        """Save current settings to a file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Settings", "", "JSON files (*.json);;All files (*)"
        )
        if filename:
            try:
                import json
                with open(filename, 'w') as f:
                    json.dump(self.current_settings, f, indent=2)
                QMessageBox.information(self, "Success", "Settings saved successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to save settings: {e}")
    
    def _on_load_settings(self) -> None:
        """Load settings from a file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Settings", "", "JSON files (*.json);;All files (*)"
        )
        if filename:
            try:
                import json
                with open(filename, 'r') as f:
                    self.current_settings = json.load(f)
                QMessageBox.information(self, "Success", "Settings loaded successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load settings: {e}")

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------
    def closeEvent(self, a0: QCloseEvent) -> None:  # type: ignore[override]
        with contextlib.suppress(Exception):
            self.can_manager.stop_retransmission()
        a0.accept()
