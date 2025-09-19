"""Settings dialog for the CAN_ID_Reframe tool.

Contains settings for connection, logging, and advanced throttling.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QWidget,
)
from PyQt6.uic.load_ui import loadUi

from .can_logic import CANManager

# get_resource_path is not used here currently; keep imports minimal


class SettingsDialog(QDialog):
    """Settings dialog window."""

    # Hints for linters to know the attributes injected by loadUi
    settingsTabWidget: QTabWidget
    # Connection tab
    input_channel_combo: QComboBox
    output_channel_combo: QComboBox
    bitrate_combo: QComboBox
    # Logging tab
    log_file_path_edit: QLineEdit
    browse_log_file_button: QPushButton
    # Throttling tab
    max_send_retries_edit: QLineEdit
    send_retry_initial_delay_edit: QLineEdit
    tx_min_gap_edit: QLineEdit
    tx_overflow_cooldown_edit: QLineEdit
    reset_defaults_button: QPushButton
    # Dialog buttons
    buttonBox: QDialogButtonBox

    def __init__(self, parent=None, can_manager: CANManager | None = None) -> None:
        super().__init__(parent)
        ui_file = Path(__file__).with_name("settings_dialog.ui")
        if not ui_file.exists():
            raise FileNotFoundError(f"Settings dialog UI file not found: {ui_file}")
        loadUi(str(ui_file), self)

        self.can_manager = can_manager
        self._channels = []

        # Expose the tab widget under the name expected by tests
        # Prefer an existing widget named in the UI, otherwise find or create one.
        tabs_widget = getattr(self, "settingsTabWidget", None)
        if tabs_widget is None:
            found = self.findChild(QTabWidget)
            if found is not None:
                tabs_widget = found
            else:
                # Fallback: create a simple tabs widget with the expected labels
                tabs_widget = QTabWidget(self)
                tabs_widget.addTab(QWidget(), "Connection")
                tabs_widget.addTab(QWidget(), "Logging")
                tabs_widget.addTab(QWidget(), "Advanced Throttling")
        self.tabs: QTabWidget = tabs_widget

        self._connect_signals()
        self._set_default_values()

        # Populate channels if manager is available
        if self.can_manager:
            self.can_manager.channels_detected.connect(self._populate_channel_selectors)
            self.can_manager.detect_channels()

    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self.browse_log_file_button.clicked.connect(self._on_browse_log_file)
        self.reset_defaults_button.clicked.connect(self._reset_throttling_defaults)
        
        # Handle Apply button separately
        self.buttonBox.clicked.connect(self._on_button_clicked)

    def _on_button_clicked(self, button) -> None:
        """Handle dialog button clicks."""
        if self.buttonBox.standardButton(button) == QDialogButtonBox.StandardButton.Apply:
            self._apply_settings()

    def _set_default_values(self) -> None:
        """Set default values for all settings."""
        # Default bitrate
        idx = self.bitrate_combo.findText("500")
        if idx >= 0:
            self.bitrate_combo.setCurrentIndex(idx)

        # Default throttling values
        self._reset_throttling_defaults()

    def _reset_throttling_defaults(self) -> None:
        """Reset throttling settings to default values."""
        self.max_send_retries_edit.setText("10")
        self.send_retry_initial_delay_edit.setText("0.01")
        self.tx_min_gap_edit.setText("0.0")
        self.tx_overflow_cooldown_edit.setText("0.05")

    def _populate_channel_selectors(self, channels) -> None:
        """Populate channel combo boxes with detected channels."""
        self._channels = channels
        self.input_channel_combo.clear()
        self.output_channel_combo.clear()
        
        for ch in channels:
            display_name = ch.get("display_name", f"{ch['interface']}:{ch['channel']}")
            self.input_channel_combo.addItem(display_name, userData=ch)
            self.output_channel_combo.addItem(display_name, userData=ch)
        
        if len(channels) > 1:
            self.output_channel_combo.setCurrentIndex(1)

    def _on_browse_log_file(self) -> None:
        """Open file dialog to select log file path."""
        fileName, _ = QFileDialog.getSaveFileName(
            self, "Save Log As", "", "CSV files (*.csv);;All files (*)"
        )
        if fileName:
            self.log_file_path_edit.setText(fileName)

    def _apply_settings(self) -> None:
        """Apply current settings (placeholder for future implementation)."""
        # This will be connected to the main window to apply settings
        pass

    def get_settings(self) -> dict[str, Any]:
        """Get current settings as a dictionary."""
        return {
            "connection": {
                "input_channel_index": self.input_channel_combo.currentIndex(),
                "output_channel_index": self.output_channel_combo.currentIndex(),
                "bitrate": self.bitrate_combo.currentText(),
            },
            "logging": {
                "log_file_path": self.log_file_path_edit.text(),
            },
            "throttling": {
                "max_send_retries": self.max_send_retries_edit.text(),
                "send_retry_initial_delay": self.send_retry_initial_delay_edit.text(),
                "tx_min_gap": self.tx_min_gap_edit.text(),
                "tx_overflow_cooldown": self.tx_overflow_cooldown_edit.text(),
            },
        }

    def set_settings(self, settings: dict[str, Any]) -> None:
        """Set settings from a dictionary."""
        try:
            # Connection settings
            if "connection" in settings:
                conn = settings["connection"]
                if (
                    "input_channel_index" in conn
                    and conn["input_channel_index"] < self.input_channel_combo.count()
                ):
                    self.input_channel_combo.setCurrentIndex(conn["input_channel_index"])
                if (
                    "output_channel_index" in conn
                    and conn["output_channel_index"] < self.output_channel_combo.count()
                ):
                    self.output_channel_combo.setCurrentIndex(conn["output_channel_index"])
                if "bitrate" in conn:
                    idx = self.bitrate_combo.findText(str(conn["bitrate"]))
                    if idx >= 0:
                        self.bitrate_combo.setCurrentIndex(idx)

            # Logging settings
            if "logging" in settings:
                log = settings["logging"]
                if "log_file_path" in log:
                    self.log_file_path_edit.setText(log["log_file_path"])

            # Throttling settings
            if "throttling" in settings:
                throttle = settings["throttling"]
                if "max_send_retries" in throttle:
                    self.max_send_retries_edit.setText(str(throttle["max_send_retries"]))
                if "send_retry_initial_delay" in throttle:
                    self.send_retry_initial_delay_edit.setText(str(throttle["send_retry_initial_delay"]))
                if "tx_min_gap" in throttle:
                    self.tx_min_gap_edit.setText(str(throttle["tx_min_gap"]))
                if "tx_overflow_cooldown" in throttle:
                    self.tx_overflow_cooldown_edit.setText(str(throttle["tx_overflow_cooldown"]))

        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Error loading settings: {e}")

    def save_settings_to_file(self, file_path: str) -> bool:
        """Save current settings to a JSON file."""
        try:
            settings = self.get_settings()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")
            return False

    def load_settings_from_file(self, file_path: str) -> bool:
        """Load settings from a JSON file."""
        try:
            with open(file_path, encoding='utf-8') as f:
                settings = json.load(f)
            self.set_settings(settings)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"Failed to load settings: {e}")
            return False