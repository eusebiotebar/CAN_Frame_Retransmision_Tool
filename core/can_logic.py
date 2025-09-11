"""Module for CAN communication logic using python-can and PyQt.

This module defines the CANManager and CANWorker classes, which handle
CAN device detection, message retransmission, and threading.
"""

import logging

import can
from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class CANWorker(QObject):
    """
    Worker object that performs the CAN retransmission in a separate thread.
    """
    frame_received = pyqtSignal(object)
    frame_retransmitted = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, input_config, output_config, rewrite_rules):
        super().__init__()
        self.input_bus = None
        self.output_bus = None
        self.input_config = input_config
        self.output_config = output_config
        self.rewrite_rules = rewrite_rules
        self._is_running = True
        logger.info("CANWorker initialized.")

    def run(self):
        """The main retransmission loop."""
        logger.info(
            f"Starting CAN retransmission thread. Input: {self.input_config}, "
            f"Output: {self.output_config}"
        )
        try:
            self.input_bus = can.interface.Bus(**self.input_config)
            logger.info(f"Input bus '{self.input_config['channel']}' opened.")
            self.output_bus = can.interface.Bus(**self.output_config)
            logger.info(f"Output bus '{self.output_config['channel']}' opened.")

            while self._is_running:
                msg = self.input_bus.recv(timeout=0.5)
                if msg:
                    self.frame_received.emit(msg)
                    new_id = self.rewrite_rules.get(msg.arbitration_id)

                    if new_id is not None:
                        new_msg = can.Message(
                            arbitration_id=new_id,
                            data=msg.data,
                            is_extended_id=msg.is_extended_id,
                        )
                        self.output_bus.send(new_msg)
                        self.frame_retransmitted.emit(new_msg)
                    else:
                        self.output_bus.send(msg)
                        self.frame_retransmitted.emit(msg)

        except Exception as e:
            logger.exception("An unhandled exception occurred in CANWorker.")
            self.error_occurred.emit(f"Error in CAN worker: {e}")
        finally:
            if self.input_bus:
                self.input_bus.shutdown()
                logger.info("Input bus shut down.")
            if self.output_bus:
                self.output_bus.shutdown()
                logger.info("Output bus shut down.")
            self.finished.emit()
            logger.info("CAN retransmission thread finished.")

    def stop(self):
        """Stops the listener loop."""
        logger.info("Stopping CAN worker...")
        self._is_running = False


class CANManager(QObject):
    """
    Manages the CAN worker thread and provides an interface for the GUI.
    """
    channels_detected = pyqtSignal(list)
    frame_received = pyqtSignal(object)
    frame_retransmitted = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread = None
        self.worker = None
        logger.info("CANManager initialized.")

    def detect_channels(self):
        """Detects available CAN channels."""
        logger.info("Detecting CAN channels...")
        available_channels = [
            {'interface': 'virtual', 'channel': 'vcan0', 'display_name': 'Virtual Channel 0'},
            {'interface': 'virtual', 'channel': 'vcan1', 'display_name': 'Virtual Channel 1'},
        ]
        logger.info(f"Detected channels: {available_channels}")
        self.channels_detected.emit(available_channels)

    def start_retransmission(self, input_config, output_config, rewrite_rules):
        """Starts the CAN retransmission in a separate thread."""
        logger.info("Starting retransmission process...")
        if self.thread and self.thread.isRunning():
            self.stop_retransmission()

        self.thread = QThread()
        self.thread.setObjectName("CANThread")
        self.worker = CANWorker(input_config, output_config, rewrite_rules)
        self.worker.moveToThread(self.thread)

        self.worker.frame_received.connect(self.frame_received)
        self.worker.frame_retransmitted.connect(self.frame_retransmitted)
        self.worker.error_occurred.connect(self.error_occurred)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def stop_retransmission(self):
        """Stops the CAN retransmission thread."""
        logger.info("Stopping retransmission process...")
        if self.worker:
            self.worker.stop()
        if self.thread:
            self.thread.quit()
            self.thread.wait(2000) # Wait up to 2 seconds
            if self.thread.isRunning():
                logger.warning("CAN thread did not quit gracefully. Terminating.")
                self.thread.terminate()
            self.thread = None
            self.worker = None
            logger.info("Retransmission process stopped.")
