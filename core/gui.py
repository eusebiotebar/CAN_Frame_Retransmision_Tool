"""Main UI for the CAN_ID_Reframe tool.

Contains only logic and signal wiring.
"""
from __future__ import annotations

import contextlib
import logging
from pathlib import Path
from typing import Any

from PyQt6 import uic
from PyQt6.QtWidgets import (QComboBox, QFileDialog, QGroupBox, QHeaderView,
                             QLabel, QLineEdit, QMainWindow, QMessageBox,
                             QPushButton, QTableWidget, QTableWidgetItem)

from .can_logic import CANManager
from .logger_setup import LOG_LEVELS, setup_logging
from .utils import RuleParsingError, parse_rewrite_rules
from .version import __version__

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    # Hints for linters to know the attributes injected by loadUi
    input_channel_combo: QComboBox
    output_channel_combo: QComboBox
    bitrate_combo: QComboBox
    start_stop_button: QPushButton
    status_label: QLabel
    status_indicator: QLabel
    frames_table: QTableWidget
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
        uic.loadUi(str(ui_file), self)  # type: ignore[attr-defined]

        self.setWindowTitle(f"CAN ID Reframe Tool v{__version__}")
        self.can_manager = CANManager()
        self.is_running = False

        self._configure_widgets()
        self._connect_signals()
        self.update_status("Disconnected", "grey")
        self.can_manager.detect_channels()
        logger.info("MainWindow initialized (UI loaded from gui.ui).")

    # ------------------------------------------------------------------
    # Initial widget configuration
    # ------------------------------------------------------------------
    def _configure_widgets(self) -> None:
        # Frame table
        self.frames_table.setColumnCount(4)
        self.frames_table.setHorizontalHeaderLabels(["Timestamp", "ID (Hex)", "DLC", "Data (Hex)"])
        self.frames_table.setEditTriggers(self.frames_table.EditTrigger.NoEditTriggers)
        header = self.frames_table.horizontalHeader()
        if header is not None:  # Defense against static analysis
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

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

        # Log levels
        self.log_level_combo.clear()
        self.log_level_combo.addItems(LOG_LEVELS.keys())
        info_idx = self.log_level_combo.findText("INFO")
        if info_idx >= 0:
            self.log_level_combo.setCurrentIndex(info_idx)

        # About action
        if getattr(self, "actionAcerca_de", None):  # type: ignore[attr-defined]
            with contextlib.suppress(Exception):  # pragma: no cover
                self.actionAcerca_de.triggered.connect(self._show_about_dialog)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Signal connections
    # ------------------------------------------------------------------
    def _connect_signals(self) -> None:
        self.can_manager.channels_detected.connect(self._populate_channel_selectors)
        self.can_manager.error_occurred.connect(self._handle_error)
        self.can_manager.frame_received.connect(self._add_frame_to_view)
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        self.add_rule_button.clicked.connect(self._on_add_rule)
        self.delete_rule_button.clicked.connect(self._on_delete_rule)
        self.browse_log_file_button.clicked.connect(self._on_browse_log_file)
        self.log_level_combo.currentTextChanged.connect(self._update_logging_config)
        self.log_file_path_edit.textChanged.connect(self._update_logging_config)

    # ------------------------------------------------------------------
    # UI utilities
    # ------------------------------------------------------------------
    def _populate_channel_selectors(self, channels) -> None:
        self.input_channel_combo.clear()
        self.output_channel_combo.clear()
        for ch in channels:
            display_name = ch.get("display_name", f"{ch["interface"]}:{ch["channel"]}")
            self.input_channel_combo.addItem(display_name, userData=ch)
            self.output_channel_combo.addItem(display_name, userData=ch)
        if len(channels) > 1:
            self.output_channel_combo.setCurrentIndex(1)

    def update_status(self, message: str, color: str) -> None:
        self.status_label.setText(message)
        self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

    # ------------------------------------------------------------------
    # Frame reception
    # ------------------------------------------------------------------
    def _add_frame_to_view(self, msg) -> None:  # msg comes from python-can
        if not self.is_running:
            return
        self.frames_table.insertRow(0)
        self.frames_table.setItem(0, 0, QTableWidgetItem(f"{msg.timestamp:.3f}"))
        self.frames_table.setItem(0, 1, QTableWidgetItem(f"{msg.arbitration_id:X}"))
        self.frames_table.setItem(0, 2, QTableWidgetItem(str(msg.dlc)))
        self.frames_table.setItem(0, 3, QTableWidgetItem(msg.data.hex().upper()))
        if self.frames_table.rowCount() > 100:
            self.frames_table.removeRow(100)

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
            logger.info("Stop button clicked.")
            self.can_manager.stop_retransmission()
            self.update_status("Stopped", "grey")
            self.start_stop_button.setText("Start")
            self._set_controls_enabled(True)
            self.is_running = False
            return

        logger.info("Start button clicked.")
        input_data = self.input_channel_combo.currentData()
        output_data = self.output_channel_combo.currentData()
        if not input_data or not output_data:
            self._show_error_message(
                "Configuration Error", 
                "No channels detected or selected."
            )
            return
        if input_data["channel"] == output_data["channel"]:
            self._show_error_message(
                "Configuration Error", 
                "Input and output channel cannot be the same."
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
        input_cfg = {
            "interface": input_data["interface"], 
            "channel": input_data["channel"], 
            "bitrate": bitrate
        }
        output_cfg = {
            "interface": output_data["interface"], 
            "channel": output_data["channel"], 
            "bitrate": bitrate
        }
        self.can_manager.start_retransmission(input_cfg, output_cfg, rewrite_rules)
        self.update_status("Retransmitting", "green")
        self.start_stop_button.setText("Stop")
        self._set_controls_enabled(False)
        self.is_running = True

    # ------------------------------------------------------------------
    # Errors / dialogs
    # ------------------------------------------------------------------
    def _handle_error(self, error_message: str) -> None:
        logger.error(f"GUI received error: {error_message}")
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
    def _on_browse_log_file(self) -> None:
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Log As", "", "Log Files (*.log);;All Files (*)"
        )
        if fileName:
            self.log_file_path_edit.setText(fileName)

    def _update_logging_config(self) -> None:
        log_level = self.log_level_combo.currentText()
        log_file = self.log_file_path_edit.text() or None
        setup_logging(log_level, log_file)

    # ------------------------------------------------------------------
    # Close event
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        logger.info("Close event received. Shutting down application.")
        with contextlib.suppress(Exception):
            self.can_manager.stop_retransmission()
        event.accept()

