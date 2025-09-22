"""Module for CAN communication logic using python-can and PyQt.

This module defines the CANManager and CANWorker classes, which handle
CAN device detection, message retransmission, and threading.
"""

import contextlib
import ctypes
import logging
import platform
import time

import can
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from .frame_logger import FrameLogger


class CANWorker(QObject):
    """Worker object that performs the CAN retransmission in a separate thread."""

    frame_received = pyqtSignal(object, int)  # msg, channel
    frame_retransmitted = pyqtSignal(object, int)  # msg, channel
    error_occurred = pyqtSignal(str)
    # Recovery lifecycle signals
    recovery_started = pyqtSignal()
    recovery_succeeded = pyqtSignal()
    recovery_failed = pyqtSignal()
    finished = pyqtSignal()

    def __init__(
        self,
        input_config,
        output_config,
        rewrite_rules,
        *,
        retry_on_busoff: bool = True,
        max_retries: int = 3,
        retry_delay: float = 0.5,
        # TX overflow/throughput controls
        max_send_retries: int = 10,
        send_retry_initial_delay: float = 0.01,
        tx_min_gap: float = 0.0,
        tx_overflow_cooldown: float = 0.05,
    ):
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
        self._busoff_streak = 0
        # TX backpressure handling (mitigate transmit buffer overflow -13)
        self._max_send_retries = max(1, int(max_send_retries))
        self._send_retry_initial_delay = max(0.0, float(send_retry_initial_delay))  # seconds
        # Adaptive throttling: ensure a minimum gap between sends and cooldown after overflow
        self._tx_min_gap = max(0.0, float(tx_min_gap))  # seconds
        self._tx_overflow_cooldown = max(0.0, float(tx_overflow_cooldown))  # seconds
        self._last_tx_time = 0.0

    def run(self):
        """The main retransmission loop."""
        try:
            if not self._open_buses():
                raise (self._last_open_error or RuntimeError("Failed to open CAN buses"))

            while self._is_running:
                # Narrow types for static analysis and ensure buses are ready
                assert self.input_bus is not None
                assert self.output_bus is not None

                # Poll Input bus (Input -> Output path with optional rewrite)
                try:
                    msg_in = self.input_bus.recv(timeout=0.01)
                    if msg_in:
                        self._busoff_streak = 0
                        new_id = self.rewrite_rules.get(msg_in.arbitration_id)
                        if new_id is not None:
                            # Emit RX for frames that will be transformed (received on channel 1)
                            self.frame_received.emit(msg_in, 1)
                            new_msg = can.Message(
                                arbitration_id=new_id,
                                data=msg_in.data,
                                dlc=msg_in.dlc,
                                is_extended_id=msg_in.is_extended_id,
                                timestamp=time.time(),
                            )
                            if self._send_with_retry_on(self.output_bus, new_msg):
                                self.frame_retransmitted.emit(new_msg, 0)  # to channel 0
                            else:
                                self.error_occurred.emit(
                                    "TX buffer overflow: dropped a rewritten frame after retries"
                                )
                        else:
                            # Emit RX for passthrough frames (received on channel 1)
                            self.frame_received.emit(msg_in, 1)
                            # Passthrough silently
                            retransmitted_msg = can.Message(
                                arbitration_id=msg_in.arbitration_id,
                                data=msg_in.data,
                                dlc=msg_in.dlc,
                                is_extended_id=msg_in.is_extended_id,
                                timestamp=time.time(),
                            )
                            if self._send_with_retry_on(self.output_bus, retransmitted_msg):
                                self.frame_retransmitted.emit(retransmitted_msg, 0)  # to ch 0
                            else:
                                self.error_occurred.emit(
                                    "TX buffer overflow: dropped a frame after retries"
                                )
                except Exception as e:
                    # Handle transient CAN errors such as bus-off
                    text = str(e).lower()
                    looks_bus_off = ("bus off" in text) or isinstance(
                        e, (can.CanError, AttributeError)
                    )
                    if self._retry_on_busoff and looks_bus_off:
                        if self._busoff_streak >= max(0, self._max_retries):
                            self.recovery_failed.emit()
                            raise can.CanError("bus off") from e
                        self._busoff_streak += 1
                        self.recovery_started.emit()
                        if self._attempt_recovery():
                            self.recovery_succeeded.emit()
                            continue
                        self.recovery_failed.emit()
                        raise can.CanError("bus off") from e
                    raise

                # Poll Output bus (Output -> Input path, always passthrough, no rewrite)
                try:
                    msg_out = self.output_bus.recv(timeout=0.01)
                    if msg_out:
                        self._busoff_streak = 0
                        # Emit RX for frames received on channel 0
                        self.frame_received.emit(msg_out, 0)
                        back_msg = can.Message(
                            arbitration_id=msg_out.arbitration_id,
                            data=msg_out.data,
                            dlc=msg_out.dlc,
                            is_extended_id=msg_out.is_extended_id,
                            timestamp=time.time(),
                        )
                        # Retransmit to Input (channel 1)
                        if self._send_with_retry_on(self.input_bus, back_msg):
                            self.frame_retransmitted.emit(back_msg, 1)  # transmitted to channel 1
                        else:
                            self.error_occurred.emit(
                                "TX buffer overflow: dropped a frame after retries"
                            )
                except Exception as e:
                    text = str(e).lower()
                    looks_bus_off = ("bus off" in text) or isinstance(
                        e, (can.CanError, AttributeError)
                    )
                    if self._retry_on_busoff and looks_bus_off:
                        if self._busoff_streak >= max(0, self._max_retries):
                            self.recovery_failed.emit()
                            raise can.CanError("bus off") from e
                        self._busoff_streak += 1
                        self.recovery_started.emit()
                        if self._attempt_recovery():
                            self.recovery_succeeded.emit()
                            continue
                        self.recovery_failed.emit()
                        raise can.CanError("bus off") from e
                    raise

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
            # Prefer not to receive our own transmitted frames to avoid echo loops
            in_cfg = dict(self.input_config)
            out_cfg = dict(self.output_config)
            if "receive_own_messages" not in in_cfg:
                in_cfg["receive_own_messages"] = False
            if "receive_own_messages" not in out_cfg:
                out_cfg["receive_own_messages"] = False

            try:
                self.input_bus = can.interface.Bus(**in_cfg)
            except TypeError:
                self.input_bus = can.interface.Bus(**self.input_config)

            try:
                self.output_bus = can.interface.Bus(**out_cfg)
            except TypeError:
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

    def _send_with_retry(self, msg: can.Message) -> bool:
        """Send a CAN message with timeout and retry/backoff when TX buffer is full.

        Returns True if the message was sent, False if dropped after exhausting retries.
        """
        assert self.output_bus is not None
        # Respect minimum gap between sends to avoid saturating slower backends
        if self._tx_min_gap > 0.0 and self._last_tx_time > 0.0:
            now = time.time()
            elapsed = now - self._last_tx_time
            remaining = self._tx_min_gap - elapsed
            if remaining > 0:
                time.sleep(remaining)

        delay = max(0.0, self._send_retry_initial_delay)
        attempts = max(1, self._max_send_retries)
        for attempt in range(1, attempts + 1):
            try:
                # Use a small timeout to allow the backend to wait for TX space
                self.output_bus.send(msg, timeout=0.1)
                # Successful send: record time for inter-send gap
                self._last_tx_time = time.time()
                return True
            except can.CanError as e:
                text = str(e).lower()
                # Common patterns across backends for TX queue saturation
                is_overflow = (
                    "overflow" in text
                    or "tx buffer" in text
                    or "transmit buffer" in text
                    or "-13" in text
                )
                if is_overflow and attempt < attempts and self._is_running:
                    time.sleep(delay)
                    # Exponential backoff but clamp to a reasonable bound
                    delay = min(delay * 2.0, 0.2)
                    continue
                # Non-overflow error or retries exhausted: fail this send
                if is_overflow and self._tx_overflow_cooldown > 0.0:
                    # Cool down briefly after overflow to avoid repeated drops
                    time.sleep(self._tx_overflow_cooldown)
                return False
            except Exception:
                # Any other unexpected error: do not crash the worker loop
                return False
        return False

    def _send_with_retry_on(self, bus: can.BusABC, msg: can.Message) -> bool:
        """Generalized send retry/backoff to a specific bus (Input or Output)."""
        # Respect minimum gap globally
        if self._tx_min_gap > 0.0 and self._last_tx_time > 0.0:
            now = time.time()
            elapsed = now - self._last_tx_time
            remaining = self._tx_min_gap - elapsed
            if remaining > 0:
                time.sleep(remaining)

        delay = max(0.0, self._send_retry_initial_delay)
        attempts = max(1, self._max_send_retries)
        for attempt in range(1, attempts + 1):
            try:
                bus.send(msg, timeout=0.1)
                self._last_tx_time = time.time()
                return True
            except can.CanError as e:
                text = str(e).lower()
                is_overflow = (
                    "overflow" in text
                    or "tx buffer" in text
                    or "transmit buffer" in text
                    or "-13" in text
                )
                if is_overflow and attempt < attempts and self._is_running:
                    time.sleep(delay)
                    delay = min(delay * 2.0, 0.2)
                    continue
                if is_overflow and self._tx_overflow_cooldown > 0.0:
                    time.sleep(self._tx_overflow_cooldown)
                return False
            except Exception:
                return False
        return False


class CANManager(QObject):
    """
    Manages the CAN worker thread and provides an interface for the GUI.
    """

    channels_detected = pyqtSignal(list)
    frame_received = pyqtSignal(object, int)  # msg, channel
    frame_retransmitted = pyqtSignal(object, int)  # msg, channel
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
        self._throttle_opts: dict[str, float | int] = {}

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
            # Suppress noisy backend warnings during detection only
            noisy_loggers = [
                "can.pcan",  # warns when 'uptime' not installed
                "can.interfaces.vector.canlib",  # warns when vxlapi64 not found
            ]
            prev_levels: dict[str, int] = {}
            for name in noisy_loggers:
                logger = logging.getLogger(name)
                prev_levels[name] = logger.level
                logger.setLevel(logging.ERROR)

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

                # Try to detect Vector devices only if the XL API DLL is present
                has_vxl = False
                try:
                    ctypes.WinDLL("vxlapi64")
                    has_vxl = True
                except OSError:
                    has_vxl = False

                if has_vxl:
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
                        # python-can vector backend not installed/available
                        pass
            finally:
                # Restore logger levels
                for name, lvl in prev_levels.items():
                    logging.getLogger(name).setLevel(lvl)

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
        # Resolve throttle options with safe defaults matching CANWorker
        opts = self._throttle_opts
        self.worker = CANWorker(
            input_config,
            output_config,
            rewrite_rules,
            max_send_retries=int(opts.get("max_send_retries", 10)),
            send_retry_initial_delay=float(opts.get("send_retry_initial_delay", 0.01)),
            tx_min_gap=float(opts.get("tx_min_gap", 0.0)),
            tx_overflow_cooldown=float(opts.get("tx_overflow_cooldown", 0.05)),
        )
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
            # Create wrapper functions to handle the new signal signature (msg, channel)
            frame_logger = self._frame_logger  # Local reference for type checker
            
            def log_rx_frame(msg, channel):
                frame_logger.log_frame("RX", msg, channel)
            
            def log_tx_frame(msg, channel):
                frame_logger.log_frame("TX", msg, channel)
            
            self.worker.frame_received.connect(log_rx_frame)
            self.worker.frame_retransmitted.connect(log_tx_frame)

        self._thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def set_throttle_options(
        self,
        *,
        max_send_retries: int,
        send_retry_initial_delay: float,
        tx_min_gap: float,
        tx_overflow_cooldown: float,
    ) -> None:
        """Set throttling/backpressure options used when creating the worker."""
        self._throttle_opts = {
            "max_send_retries": int(max(1, max_send_retries)),
            "send_retry_initial_delay": float(max(0.0, send_retry_initial_delay)),
            "tx_min_gap": float(max(0.0, tx_min_gap)),
            "tx_overflow_cooldown": float(max(0.0, tx_overflow_cooldown)),
        }

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
