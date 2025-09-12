"""Module for CAN communication logic using python-can and PyQt.

This module defines the CANManager and CANWorker classes, which handle
CAN device detection, message retransmission, and threading.
"""

import logging
import platform

import can
from PyQt6.QtCore import QObject, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class CANWorker(QObject):
    """Worker object that performs the CAN retransmission in a separate thread."""

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
        self._thread: QThread | None = None
        self.worker: CANWorker | None = None
        logger.info("CANManager initialized.")

    def detect_channels(self):
        """Detects available CAN channels including physical devices."""
        logger.info("Detecting CAN channels...")
        available_channels = []

        # Add virtual channels for testing
        available_channels.extend(
            [
                {"interface": "virtual", "channel": "vcan0", "display_name": "Virtual Channel 0"},
                {"interface": "virtual", "channel": "vcan1", "display_name": "Virtual Channel 1"},
            ]
        )

        # Detect physical CAN interfaces
        try:
            # Detect Kvaser devices
            available_channels.extend(self._detect_kvaser_devices())

            # Detect other physical interfaces based on platform
            if platform.system() == "Windows":
                available_channels.extend(self._detect_windows_can_devices())
            elif platform.system() == "Linux":
                available_channels.extend(self._detect_linux_can_devices())

        except Exception as e:
            logger.warning(f"Error detecting physical CAN devices: {e}")

        logger.info(f"Detected channels: {available_channels}")
        self.channels_detected.emit(available_channels)

    def _detect_kvaser_devices(self) -> list[dict[str, str]]:
        """Detect Kvaser CAN devices."""
        kvaser_channels: list[dict[str, str]] = []
        try:
            # Try to import and use Kvaser canlib if available
            from can.interfaces.kvaser import KvaserBus

            # Kvaser devices typically show up as channel 0, 1, etc.
            for channel_num in range(8):  # Check up to 8 channels
                try:
                    # Try to create a bus to test if the channel exists
                    test_bus = KvaserBus(channel=channel_num, receive_own_messages=False)
                    test_bus.shutdown()

                    kvaser_channels.append(
                        {
                            "interface": "kvaser",
                            "channel": str(channel_num),
                            "display_name": f"Kvaser Channel {channel_num}",
                        }
                    )
                    logger.info(f"Detected Kvaser device: Channel {channel_num}")
                except Exception:
                    # Channel doesn't exist or can't be opened
                    continue

        except ImportError:
            logger.debug("Kvaser canlib not available")
        except Exception as e:
            logger.warning(f"Error detecting Kvaser devices: {e}")

        return kvaser_channels

    def _detect_windows_can_devices(self) -> list[dict[str, str]]:
        """Detect CAN devices on Windows."""
        windows_channels: list[dict[str, str]] = []
        try:
            # Try to detect PCAN devices
            try:
                from can.interfaces.pcan import PcanBus

                # Common PCAN channels
                pcan_channels = [
                    "PCAN_USBBUS1",
                    "PCAN_USBBUS2",
                    "PCAN_USBBUS3",
                    "PCAN_USBBUS4",
                    "PCAN_USBBUS5",
                    "PCAN_USBBUS6",
                    "PCAN_USBBUS7",
                    "PCAN_USBBUS8",
                ]

                for channel in pcan_channels:
                    try:
                        test_bus = PcanBus(channel=channel, bitrate=500000)
                        test_bus.shutdown()

                        windows_channels.append(
                            {
                                "interface": "pcan",
                                "channel": channel,
                                "display_name": f"PCAN {channel}",
                            }
                        )
                        logger.info(f"Detected PCAN device: {channel}")
                    except Exception:
                        continue

            except ImportError:
                logger.debug("PCAN interface not available")

            # Try to detect Vector devices
            try:
                from can.interfaces.vector import VectorBus

                # Vector channels are typically numbered
                for channel_num in range(4):
                    try:
                        vector_bus = VectorBus(channel=channel_num, bitrate=500000)
                        vector_bus.shutdown()

                        windows_channels.append(
                            {
                                "interface": "vector",
                                "channel": str(channel_num),
                                "display_name": f"Vector Channel {channel_num}",
                            }
                        )
                        logger.info(f"Detected Vector device: Channel {channel_num}")
                    except Exception:
                        continue

            except ImportError:
                logger.debug("Vector interface not available")

        except Exception as e:
            logger.warning(f"Error detecting Windows CAN devices: {e}")

        return windows_channels

    def _detect_linux_can_devices(self) -> list[dict[str, str]]:
        """Detect CAN devices on Linux."""
        linux_channels: list[dict[str, str]] = []
        try:
            # Check for SocketCAN interfaces
            import re
            import subprocess

            # Get network interfaces
            result = subprocess.run(
                ["ip", "link", "show"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                # Look for CAN interfaces (can0, can1, etc.)
                can_interfaces = re.findall(r"\d+:\s+(can\d+):", result.stdout)

                for interface in can_interfaces:
                    linux_channels.append(
                        {
                            "interface": "socketcan",
                            "channel": interface,
                            "display_name": f"SocketCAN {interface}",
                        }
                    )
                    logger.info(f"Detected SocketCAN interface: {interface}")

        except Exception as e:
            logger.warning(f"Error detecting Linux CAN devices: {e}")

        return linux_channels

    def start_retransmission(self, input_config, output_config, rewrite_rules):
        """Starts the CAN retransmission in a separate thread."""
        logger.info("Starting retransmission process...")
        if self._thread and self._thread.isRunning():
            self.stop_retransmission()

        self._thread = QThread()
        self._thread.setObjectName("CANThread")
        self.worker = CANWorker(input_config, output_config, rewrite_rules)
        self.worker.moveToThread(self._thread)

        self.worker.frame_received.connect(self.frame_received)
        self.worker.frame_retransmitted.connect(self.frame_retransmitted)
        self.worker.error_occurred.connect(self.error_occurred)

        self._thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_retransmission(self):
        """Stops the CAN retransmission thread."""
        logger.info("Stopping retransmission process...")
        if self.worker:
            self.worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)  # Wait up to 2 seconds
            if self._thread.isRunning():
                logger.warning("CAN thread did not quit gracefully. Terminating.")
                self._thread.terminate()
            self._thread = None
            self.worker = None
            logger.info("Retransmission process stopped.")
