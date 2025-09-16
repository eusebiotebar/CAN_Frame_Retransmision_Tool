"""Module for CAN communication logic using python-can and PyQt.

This module defines the CANManager and CANWorker classes, which handle
CAN device detection, message retransmission, and threading.
"""

import contextlib
import platform
import time
from functools import partial

import can
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .frame_logger import FrameLogger


class CANWorker(QObject):
    """Worker object that performs the CAN retransmission in a separate thread."""

    frame_received = pyqtSignal(object)
    frame_retransmitted = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    # Recovery lifecycle signals
    recovery_started = pyqtSignal()
    recovery_succeeded = pyqtSignal()
    recovery_failed = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, input_config, output_config, rewrite_rules,
                 *, retry_on_busoff: bool = True, max_retries: int = 3, retry_delay: float = 0.5):
        super().__init__()
        # Buses are opened lazily in _open_buses
        self.input_bus: can.BusABC | None = None
        self.output_bus: can.BusABC | None = None
        self.input_config = input_config
        self.output_config = output_config
        self.rewrite_rules = rewrite_rules
        self._is_running = True
        # NFR-REL-001: Auto-recovery parameters
        self._retry_on_busoff = retry_on_busoff
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._last_open_error: Exception | None = None
        # Track consecutive bus-off recoveries to enforce max retries across iterations
        self._busoff_streak: int = 0

    def run(self):
        """The main retransmission loop."""
        try:
            if not self._open_buses():
                raise (self._last_open_error or RuntimeError("Failed to open CAN buses"))

            while self._is_running:
                try:
                    # Narrow types for static analysis and ensure buses are ready
                    assert self.input_bus is not None
                    assert self.output_bus is not None
                    msg = self.input_bus.recv(timeout=0.5)
                    # Successful receive: reset bus-off streak
                    self._busoff_streak = 0
                except Exception as e:  # Handle transient CAN errors such as bus-off
                    # REQ-NFR-REL-001: attempt auto-recovery when bus-off occurs or input bus broken
                    text = str(e).lower()
                    looks_bus_off = ("bus off" in text) or isinstance(
                        e, (can.CanError, AttributeError)
                    )
                    if self._retry_on_busoff and looks_bus_off:
                        # Enforce maximum consecutive recovery attempts
                        if self._busoff_streak >= max(0, self._max_retries):
                            self.recovery_failed.emit()
                            raise can.CanError("bus off") from e
                        self._busoff_streak += 1
                        # Inform listeners that recovery will be attempted
                        self.recovery_started.emit()
                        recovered = self._attempt_recovery()
                        if recovered:
                            self.recovery_succeeded.emit()
                            # Continue loop and try receiving again
                            continue
                        # If not recovered, escalate as bus-off for consistent reporting
                        self.recovery_failed.emit()
                        raise can.CanError("bus off") from e
                    # Propagate to outer handler
                    raise
                if msg:
                    self.frame_received.emit(msg)
                    new_id = self.rewrite_rules.get(msg.arbitration_id)

                    if new_id is not None:
                        new_msg = can.Message(
                            arbitration_id=new_id,
                            data=msg.data,
                            dlc=msg.dlc,
                            is_extended_id=msg.is_extended_id,
                            timestamp=time.time(),
                        )
                        assert self.output_bus is not None
                        self.output_bus.send(new_msg)
                        self.frame_retransmitted.emit(new_msg)
                    else:
                        # Create a new message from the original to get a fresh timestamp
                        retransmitted_msg = can.Message(
                            arbitration_id=msg.arbitration_id,
                            data=msg.data,
                            dlc=msg.dlc,
                            is_extended_id=msg.is_extended_id,
                            timestamp=time.time(),
                        )
                        assert self.output_bus is not None
                        self.output_bus.send(retransmitted_msg)
                        self.frame_retransmitted.emit(retransmitted_msg)

        except Exception as e:
            self.error_occurred.emit(f"Error in CAN worker: {e}")
        finally:
            if self.input_bus:
                self.input_bus.shutdown()
            if self.output_bus:
                self.output_bus.shutdown()
            self.finished.emit()

    def stop(self):
        """Stops the listener loop."""
        self._is_running = False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _open_buses(self) -> bool:
        """Open input/output buses according to configs. Returns True on success."""
        try:
            self.input_bus = can.interface.Bus(**self.input_config)
            self.output_bus = can.interface.Bus(**self.output_config)
            return True
        except Exception as e:
            self._last_open_error = e
            return False

    def _attempt_recovery(self) -> bool:
        """Attempt to recover from a bus-off by reopening buses with retries.

        Returns True if recovery succeeded, False otherwise.
        """
        # Close current buses defensively
        with contextlib.suppress(Exception):
            if self.input_bus:
                self.input_bus.shutdown()
        with contextlib.suppress(Exception):
            if self.output_bus:
                self.output_bus.shutdown()

        for _ in range(max(0, self._max_retries)):
            if not self._is_running:
                return False
            time.sleep(max(0.0, self._retry_delay))
            if self._open_buses() and hasattr(self.input_bus, "recv") and hasattr(
                self.output_bus, "send"
            ):
                return True
                # Otherwise, keep trying
        return False


class CANManager(QObject):
    """
    Manages the CAN worker thread and provides an interface for the GUI.
    """

    channels_detected = pyqtSignal(list)
    frame_received = pyqtSignal(object)
    frame_retransmitted = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    # Forwarded worker recovery signals
    recovery_started = pyqtSignal()
    recovery_succeeded = pyqtSignal()
    recovery_failed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._thread: QThread | None = None
        self.worker: CANWorker | None = None
        self._frame_logger: FrameLogger | None = None

    def detect_channels(self):
        """Detects available CAN channels including physical devices."""
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

        except Exception:
            # Keep going even if physical device detection fails
            pass

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
                except Exception:
                    # Channel doesn't exist or can't be opened
                    continue

        except (ImportError, Exception):
            # Kvaser library not available or other error
            pass

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
                    except Exception:
                        continue

            except (ImportError, Exception):
                pass

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
                    except Exception:
                        continue

            except (ImportError, Exception):
                pass

        except Exception:
            pass

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

        except Exception:
            pass

        return linux_channels

    def start_retransmission(
        self, input_config, output_config, rewrite_rules, log_file: str | None
    ):
        """Starts the CAN retransmission in a separate thread."""
        if self._thread and self._thread.isRunning():
            self.stop_retransmission()

        if log_file:
            self._frame_logger = FrameLogger()
            self._frame_logger.set_log_path(log_file)
            self._frame_logger.start_logging()

        self._thread = QThread()
        self._thread.setObjectName("CANThread")
        self.worker = CANWorker(input_config, output_config, rewrite_rules)
        self.worker.moveToThread(self._thread)

        # Forward signals from worker to the manager's signals
        self.worker.frame_received.connect(self.frame_received)
        self.worker.frame_retransmitted.connect(self.frame_retransmitted)
        self.worker.error_occurred.connect(self.error_occurred)
        # Forward recovery lifecycle
        self.worker.recovery_started.connect(self.recovery_started)
        self.worker.recovery_succeeded.connect(self.recovery_succeeded)
        self.worker.recovery_failed.connect(self.recovery_failed)

        # Connect worker signals to logger if active
        if self._frame_logger and self._frame_logger.is_logging:
            self.worker.frame_received.connect(partial(self._frame_logger.log_frame, "RX"))
            self.worker.frame_retransmitted.connect(partial(self._frame_logger.log_frame, "TX"))

        self._thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def stop_retransmission(self):
        """Stops the CAN retransmission thread."""
        if self.worker:
            self.worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)  # Wait up to 2 seconds
            if self._thread.isRunning():
                self._thread.terminate()
            self._thread = None
            self.worker = None

        if self._frame_logger:
            self._frame_logger.stop_logging()
            self._frame_logger = None
