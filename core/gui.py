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
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt6.uic.load_ui import loadUi

from .can_logic import CANManager
from .utils import RuleParsingError, get_resource_path, parse_rewrite_rules
from .version import __version__


class MainWindow(QMainWindow):
    """Main application window."""

    # Hints for linters to know the attributes injected by loadUi
    input_channel_combo: QComboBox
    output_channel_combo: QComboBox
    bitrate_combo: QComboBox
    start_stop_button: QPushButton
    status_label: QLabel
    status_indicator: QLabel
    frames_table_RX: QTableWidget
    frames_table_TX: QTableWidget
    mapping_table: QTableWidget
    add_rule_button: QPushButton
    delete_rule_button: QPushButton
    log_level_combo: QComboBox
    log_file_path_edit: QLineEdit
    browse_log_file_button: QPushButton
    actionAcerca_de: Any  # QAction
    connection_group: QGroupBox
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

        # Default bitrate
        idx = self.bitrate_combo.findText("250")
        if idx >= 0:
            self.bitrate_combo.setCurrentIndex(idx)

        # About action
        if getattr(self, "actionAcerca_de", None):
            with contextlib.suppress(Exception):  # pragma: no cover
                self.actionAcerca_de.triggered.connect(self._show_about_dialog)

        self._set_default_log_path()

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
        self.can_manager.channels_detected.connect(self._populate_channel_selectors)
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
        self.browse_log_file_button.clicked.connect(self._on_browse_log_file)

    # ------------------------------------------------------------------
    # UI utilities
    # ------------------------------------------------------------------
    def _populate_channel_selectors(self, channels) -> None:
        self.input_channel_combo.clear()
        self.output_channel_combo.clear()
        for ch in channels:
            display_name = ch.get("display_name", f"{ch['interface']}:{ch['channel']}")
            self.input_channel_combo.addItem(display_name, userData=ch)
            self.output_channel_combo.addItem(display_name, userData=ch)
        if len(channels) > 1:
            self.output_channel_combo.setCurrentIndex(1)

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
        self.connection_group.setEnabled(enabled)
        self.mapping_group.setEnabled(enabled)

    def _on_start_stop_clicked(self) -> None:
        if self.is_running:
            self.can_manager.stop_retransmission()
            self.update_status("Stopped", "grey")
            self.start_stop_button.setText("Start")
            self._set_controls_enabled(True)
            self.is_running = False
            return

        input_data = self.input_channel_combo.currentData()
        output_data = self.output_channel_combo.currentData()
        if not input_data or not output_data:
            self._show_error_message("Configuration Error", "No channels detected or selected.")
            return
        if input_data["channel"] == output_data["channel"]:
            self._show_error_message(
                "Configuration Error", "Input and output channel cannot be the same."
            )
            return
        try:
            bitrate = int(self.bitrate_combo.currentText()) * 1000
        except ValueError:
            self._show_error_message("Configuration Error", "Invalid bitrate.")
            return
        rewrite_rules = self._get_rewrite_rules()
        if rewrite_rules is None:
            return

        log_file = self.log_file_path_edit.text() or None

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
    # Logging
    # ------------------------------------------------------------------
    def _set_default_log_path(self) -> None:
        """Generates and sets the default log file path."""
        try:
            # Determine the base path depending on whether the app is frozen
            base_path = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()

            log_dir = base_path / "LOGS"
            log_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            app_name = "can-id-reframe"
            log_file_name = f"{app_name}_{timestamp}_log.csv"

            default_path = log_dir / log_file_name
            self.log_file_path_edit.setText(str(default_path))
        except Exception:
            # If path generation fails, leave the field blank
            self.log_file_path_edit.setText("")

    def _on_browse_log_file(self) -> None:
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Log As", "", "CSV files (*.csv);;All files (*)"
        )
        if fileName:
            self.log_file_path_edit.setText(fileName)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------
    def closeEvent(self, a0: QCloseEvent) -> None:  # type: ignore[override]
        with contextlib.suppress(Exception):
            self.can_manager.stop_retransmission()
        a0.accept()
