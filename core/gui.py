"""Main GUI module for the application.

This module contains the MainWindow class, which defines the UI and
connects to the CAN logic.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QLineEdit
)
from .can_logic import CANManager
from .logger_setup import setup_logging, LOG_LEVELS
from .version import __version__
from .utils import RuleParsingError, parse_rewrite_rules

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"CAN ID Reframe Tool v{__version__}")
        self.setGeometry(100, 100, 950, 700)

        self.can_manager = CANManager()
        self.is_running = False

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)

        self._create_menu()
        self._create_widgets()
        self._create_layouts()
        self._connect_signals()

        self.update_status("Desconectado", "grey")
        self.can_manager.detect_channels()
        logger.info("MainWindow initialized.")

    def _create_menu(self):
        """Creates the main menu bar for the application."""
        menu_bar = self.menuBar()
        help_menu = menu_bar.addMenu("&Ayuda")
        about_action = help_menu.addAction("&Acerca de...")
        about_action.triggered.connect(self._show_about_dialog)

    def _create_widgets(self):
        """Create all the widgets for the GUI."""
        self.connection_group = QGroupBox("Configuración de Conexión")
        self.input_channel_combo = QComboBox()
        self.output_channel_combo = QComboBox()
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(["125", "250", "500", "1000"])
        self.bitrate_combo.setCurrentText("250")
        self.start_stop_button = QPushButton("Iniciar")

        self.status_group = QGroupBox("Estado")
        self.status_label = QLabel()
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(20, 20)

        self.frames_group = QGroupBox("Últimas Tramas Recibidas")
        self.frames_table = QTableWidget()
        self.frames_table.setColumnCount(4)
        self.frames_table.setHorizontalHeaderLabels(["Timestamp", "ID (Hex)", "DLC", "Datos (Hex)"])
        self.frames_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.frames_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.frames_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.mapping_group = QGroupBox("Mapeo de IDs")
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setHorizontalHeaderLabels(["ID Original (Hex)", "ID Reescrito (Hex)"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.add_rule_button = QPushButton("Añadir Regla")
        self.delete_rule_button = QPushButton("Eliminar Regla")

        self.logging_group = QGroupBox("Configuración de Logging")
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(LOG_LEVELS.keys())
        self.log_level_combo.setCurrentText("INFO")
        self.log_file_path_edit = QLineEdit()
        self.log_file_path_edit.setPlaceholderText("Opcional: ruta al archivo de log")
        self.browse_log_file_button = QPushButton("Examinar...")

    def _create_layouts(self):
        """Create and arrange layouts."""
        top_controls_layout = QGridLayout(self.connection_group)
        top_controls_layout.addWidget(QLabel("Canal de Entrada:"), 0, 0)
        top_controls_layout.addWidget(self.input_channel_combo, 0, 1)
        top_controls_layout.addWidget(QLabel("Canal de Salida:"), 1, 0)
        top_controls_layout.addWidget(self.output_channel_combo, 1, 1)
        top_controls_layout.addWidget(QLabel("Bitrate (kbps):"), 2, 0)
        top_controls_layout.addWidget(self.bitrate_combo, 2, 1)

        status_layout = QHBoxLayout(self.status_group)
        status_layout.addWidget(self.status_indicator)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        top_bar_layout = QHBoxLayout()
        top_bar_layout.addWidget(self.connection_group, 2)
        top_bar_layout.addWidget(self.start_stop_button, 1)
        top_bar_layout.addWidget(self.status_group, 1)

        tables_layout = QHBoxLayout()
        frames_layout = QVBoxLayout(self.frames_group)
        frames_layout.addWidget(self.frames_table)

        mapping_buttons_layout = QHBoxLayout()
        mapping_buttons_layout.addStretch()
        mapping_buttons_layout.addWidget(self.add_rule_button)
        mapping_buttons_layout.addWidget(self.delete_rule_button)
        mapping_layout = QVBoxLayout(self.mapping_group)
        mapping_layout.addWidget(self.mapping_table)
        mapping_layout.addLayout(mapping_buttons_layout)
        tables_layout.addWidget(self.frames_group, 2)
        tables_layout.addWidget(self.mapping_group, 1)

        logging_layout = QGridLayout(self.logging_group)
        logging_layout.addWidget(QLabel("Nivel de Log:"), 0, 0)
        logging_layout.addWidget(self.log_level_combo, 0, 1)
        logging_layout.addWidget(QLabel("Archivo de Log:"), 1, 0)
        logging_layout.addWidget(self.log_file_path_edit, 1, 1)
        logging_layout.addWidget(self.browse_log_file_button, 1, 2)

        self.main_layout.addLayout(top_bar_layout)
        self.main_layout.addLayout(tables_layout)
        self.main_layout.addWidget(self.logging_group)

    def _connect_signals(self):
        """Connect widget signals to slots."""
        self.can_manager.channels_detected.connect(self._populate_channel_selectors)
        self.can_manager.error_occurred.connect(self._handle_error)
        self.can_manager.frame_received.connect(self._add_frame_to_view)
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        self.add_rule_button.clicked.connect(self._on_add_rule)
        self.delete_rule_button.clicked.connect(self._on_delete_rule)
        self.browse_log_file_button.clicked.connect(self._on_browse_log_file)
        self.log_level_combo.currentTextChanged.connect(self._update_logging_config)
        self.log_file_path_edit.textChanged.connect(self._update_logging_config)

    def _populate_channel_selectors(self, channels):
        self.input_channel_combo.clear()
        self.output_channel_combo.clear()
        for ch in channels:
            display_name = ch.get('display_name', f"{ch['interface']}:{ch['channel']}")
            self.input_channel_combo.addItem(display_name, userData=ch)
            self.output_channel_combo.addItem(display_name, userData=ch)
        if len(channels) > 1:
            self.output_channel_combo.setCurrentIndex(1)

    def update_status(self, message, color):
        self.status_label.setText(message)
        self.status_indicator.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

    def _add_frame_to_view(self, msg):
        if not self.is_running: return
        self.frames_table.insertRow(0)
        ts_str = f"{msg.timestamp:.3f}"
        self.frames_table.setItem(0, 0, QTableWidgetItem(ts_str))
        self.frames_table.setItem(0, 1, QTableWidgetItem(f"{msg.arbitration_id:X}"))
        self.frames_table.setItem(0, 2, QTableWidgetItem(str(msg.dlc)))
        self.frames_table.setItem(0, 3, QTableWidgetItem(msg.data.hex().upper()))
        if self.frames_table.rowCount() > 100:
            self.frames_table.removeRow(100)

    def _on_add_rule(self):
        self.mapping_table.insertRow(self.mapping_table.rowCount())

    def _on_delete_rule(self):
        if self.mapping_table.currentRow() >= 0:
            self.mapping_table.removeRow(self.mapping_table.currentRow())

    def _get_rewrite_rules(self):
        """
        Extracts rule data from the mapping table and uses the utility function to parse it.
        """
        table_data = []
        for row in range(self.mapping_table.rowCount()):
            original_item = self.mapping_table.item(row, 0)
            rewritten_item = self.mapping_table.item(row, 1)

            original_text = original_item.text() if original_item else ""
            rewritten_text = rewritten_item.text() if rewritten_item else ""

            # Don't add completely empty rows to the data to be parsed
            if original_text.strip() or rewritten_text.strip():
                table_data.append((original_text, rewritten_text))

        try:
            return parse_rewrite_rules(table_data)
        except RuleParsingError as e:
            self._show_error_message("Error de Mapeo", str(e))
            self.mapping_table.selectRow(e.row)
            return None

    def _set_controls_enabled(self, enabled):
        self.connection_group.setEnabled(enabled)
        self.mapping_group.setEnabled(enabled)

    def _on_start_stop_clicked(self):
        if self.is_running:
            logger.info("Stop button clicked.")
            self.can_manager.stop_retransmission()
            self.update_status("Detenido", "grey")
            self.start_stop_button.setText("Iniciar")
            self._set_controls_enabled(True)
            self.is_running = False
            return

        logger.info("Start button clicked.")
        input_data = self.input_channel_combo.currentData()
        output_data = self.output_channel_combo.currentData()
        if not input_data or not output_data:
            self._show_error_message("Error de Configuración", "No se han detectado canales o no se han seleccionado.")
            return
        if input_data['channel'] == output_data['channel']:
            self._show_error_message("Error de Configuración", "El canal de entrada y salida no pueden ser el mismo.")
            return
        try:
            bitrate = int(self.bitrate_combo.currentText()) * 1000
        except ValueError:
            self._show_error_message("Error de Configuración", "Bitrate inválido.")
            return
        rewrite_rules = self._get_rewrite_rules()
        if rewrite_rules is None: return

        input_config = {'interface': input_data['interface'], 'channel': input_data['channel'], 'bitrate': bitrate}
        output_config = {'interface': output_data['interface'], 'channel': output_data['channel'], 'bitrate': bitrate}

        self.can_manager.start_retransmission(input_config, output_config, rewrite_rules)
        self.update_status("Retransmitiendo", "green")
        self.start_stop_button.setText("Detener")
        self._set_controls_enabled(False)
        self.is_running = True

    def _handle_error(self, error_message):
        logger.error(f"GUI received error: {error_message}")
        self._show_error_message("Error", error_message)
        if self.is_running:
            self.update_status("Error", "red")
            self.start_stop_button.setText("Iniciar")
            self._set_controls_enabled(True)
            self.is_running = False

    def _show_error_message(self, title, text):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def _show_about_dialog(self):
        """Displays the 'About' dialog."""
        about_text = f"""
            <h2>CAN ID Reframe Tool</h2>
            <p>Versión: {__version__}</p>
            <p>Esta herramienta permite la retransmisión de tramas CAN entre dos canales, con la capacidad de reescribir IDs sobre la marcha.</p>
            <hr>
            <p><b>Advertencia de Seguridad (REQ-NFR-SAF-002):</b></p>
            <p>Sea consciente de los posibles efectos secundarios no deseados al retransmitir y modificar tramas CAN en un bus activo. Esta herramienta es para fines de diagnóstico y desarrollo y no debe ser utilizada para controlar sistemas críticos para la seguridad.</p>
        """
        QMessageBox.about(self, "Acerca de CAN ID Reframe Tool", about_text)

    def _on_browse_log_file(self):
        fileName, _ = QFileDialog.getSaveFileName(self, "Guardar Log Como", "", "Log Files (*.log);;All Files (*)")
        if fileName:
            self.log_file_path_edit.setText(fileName)

    def _update_logging_config(self):
        log_level = self.log_level_combo.currentText()
        log_file = self.log_file_path_edit.text() or None
        setup_logging(log_level, log_file)

    def closeEvent(self, event):
        logger.info("Close event received. Shutting down application.")
        self.can_manager.stop_retransmission()
        event.accept()
