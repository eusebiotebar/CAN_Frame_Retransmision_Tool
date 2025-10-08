"""Tests for CANWorker relay behavior and TX retry/backoff.

Covers:
- Reverse relay Output->Input is silent (no UI/log signals emitted)
- Retry/backoff/cooldown timing logic on overflow errors
"""

from __future__ import annotations

import threading
import time as _time
from collections.abc import Callable
from typing import cast

import can

from core.can_logic import CANWorker


class FakeBus:
    """Minimal fake CAN bus for unit tests."""

    def __init__(
        self,
        recv_queue: list[can.Message] | None = None,
        send_behavior: Callable[[can.Message], None] | None = None,
    ):
        self._in_q: list[can.Message] = list(recv_queue or [])
        self.sent: list[can.Message] = []
        self._send_behavior = send_behavior

    def recv(self, timeout: float | None = None) -> can.Message | None:  # noqa: ARG002
        return self._in_q.pop(0) if self._in_q else None

    def send(self, msg: can.Message, timeout: float | None = None):  # noqa: ARG002
        if self._send_behavior:
            self._send_behavior(msg)
            return
        self.sent.append(msg)

    def shutdown(self):
        pass


def _run_worker_in_thread(worker: CANWorker):
    th = threading.Thread(target=worker.run, daemon=True)
    th.start()
    return th


def test_reverse_relay_output_to_input_with_full_swap(qapp, monkeypatch):
    """Output->Input relay with Full Swap feature now emits RX/TX signals."""
    # Prepare a message on the Output bus
    msg = can.Message(arbitration_id=0x123, data=bytes([1, 2, 3]), is_extended_id=False)
    out_bus = FakeBus(recv_queue=[msg])
    in_bus = FakeBus()

    # Worker with no rewrite rules (passthrough mode)
    worker = CANWorker(input_config={}, output_config={}, rewrite_rules={})

    # Bypass bus opening and set fake buses
    worker.input_bus = cast(can.BusABC, in_bus)
    worker.output_bus = cast(can.BusABC, out_bus)
    # Ensure run() does not overwrite our fake buses
    monkeypatch.setattr(worker, "_open_buses", lambda: True)

    # Capture signals
    received = []
    retransmitted = []
    worker.frame_received.connect(lambda m, ch: received.append((m, ch)))
    worker.frame_retransmitted.connect(lambda m, ch: retransmitted.append((m, ch)))

    th = _run_worker_in_thread(worker)

    # Wait up to a short time for the worker to process
    deadline = _time.time() + 1.0
    while _time.time() < deadline and not in_bus.sent:
        _time.sleep(0.01)
        qapp.processEvents()  # Process PyQt events including signals

    worker.stop()
    th.join(timeout=1.0)

    # Allow final signal processing
    qapp.processEvents()

    # Assert the message was forwarded to Input
    assert len(in_bus.sent) == 1
    assert in_bus.sent[0].arbitration_id == 0x123
    assert bytes(in_bus.sent[0].data) == bytes([1, 2, 3])

    # With Full Swap, signals should now be emitted for Output->Input direction
    assert len(received) == 1
    assert received[0][0].arbitration_id == 0x123
    assert received[0][1] == 0  # Received on channel 0

    assert len(retransmitted) == 1
    assert retransmitted[0][0].arbitration_id == 0x123
    assert retransmitted[0][1] == 1  # Transmitted to channel 1


def test_retry_backoff_eventually_succeeds(monkeypatch):
    """On overflow errors, send retries with backoff and eventually succeeds."""
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    attempts = {"n": 0}

    def flaky_send(_msg: can.Message):
        # Fail twice with overflow, then succeed
        attempts["n"] += 1
        if attempts["n"] <= 2:
            raise can.CanError("Transmit buffer overflow -13")

    bus = FakeBus(send_behavior=flaky_send)
    worker = CANWorker(
        input_config={},
        output_config={},
        rewrite_rules={},
        max_send_retries=5,
        send_retry_initial_delay=0.01,
        tx_min_gap=0.0,
        tx_overflow_cooldown=0.05,
    )

    msg = can.Message(arbitration_id=0x1, data=b"\x01", is_extended_id=False)
    ok = worker._send_with_retry_on(cast(can.BusABC, bus), msg)
    assert ok is True
    # Expect at least two backoff sleeps: 0.01 and 0.02 (exponential)
    assert sleeps[:2] == [0.01, 0.02]


def test_retry_exhausts_and_cooldown(monkeypatch):
    """When retries exhaust on overflow, method returns False and applies cooldown."""
    sleeps: list[float] = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))

    def always_overflow(_msg: can.Message):
        raise can.CanError("TX buffer overflow")

    bus = FakeBus(send_behavior=always_overflow)
    worker = CANWorker(
        input_config={},
        output_config={},
        rewrite_rules={},
        max_send_retries=3,
        send_retry_initial_delay=0.01,
        tx_min_gap=0.0,
        tx_overflow_cooldown=0.05,
    )

    msg = can.Message(arbitration_id=0x2, data=b"\x02", is_extended_id=False)
    ok = worker._send_with_retry_on(cast(can.BusABC, bus), msg)
    assert ok is False
    # Cooldown should be applied at the end
    assert 0.05 in sleeps


def test_full_swap_output_to_input_with_id_mapping(qapp, monkeypatch):
    """Test Full Swap: Output->Input direction applies ID mapping rules."""
    # Prepare a message on the Output bus with an ID that should be remapped
    original_id = 0x123
    mapped_id = 0x456
    msg = can.Message(arbitration_id=original_id, data=bytes([1, 2, 3]), is_extended_id=False)
    out_bus = FakeBus(recv_queue=[msg])
    in_bus = FakeBus()

    # Worker with rewrite rules: 0x123 -> 0x456
    rewrite_rules = {original_id: mapped_id}
    worker = CANWorker(input_config={}, output_config={}, rewrite_rules=rewrite_rules)

    # Bypass bus opening and set fake buses
    worker.input_bus = cast(can.BusABC, in_bus)
    worker.output_bus = cast(can.BusABC, out_bus)
    monkeypatch.setattr(worker, "_open_buses", lambda: True)

    # Capture signals
    received = []
    retransmitted = []
    worker.frame_received.connect(lambda m, ch: received.append((m, ch)))
    worker.frame_retransmitted.connect(lambda m, ch: retransmitted.append((m, ch)))

    th = _run_worker_in_thread(worker)

    # Wait for processing
    deadline = _time.time() + 1.0
    while _time.time() < deadline and not in_bus.sent:
        _time.sleep(0.01)
        qapp.processEvents()  # Process PyQt events including signals

    worker.stop()
    th.join(timeout=1.0)

    # Allow final signal processing
    qapp.processEvents()

    # Assert the message was forwarded to Input with ID mapping applied
    assert len(in_bus.sent) == 1
    assert in_bus.sent[0].arbitration_id == mapped_id  # ID should be remapped
    assert bytes(in_bus.sent[0].data) == bytes([1, 2, 3])  # Data unchanged

    # Verify signals were emitted for Full Swap
    assert len(received) == 1
    assert received[0][0].arbitration_id == original_id  # Original ID in RX signal
    assert received[0][1] == 0  # Received on channel 0

    assert len(retransmitted) == 1
    assert retransmitted[0][0].arbitration_id == mapped_id  # Mapped ID in TX signal
    assert retransmitted[0][1] == 1  # Transmitted to channel 1


def test_full_swap_output_to_input_passthrough_no_mapping(qapp, monkeypatch):
    """Test Full Swap: Output->Input passthrough when no mapping rule exists."""
    # Prepare a message with an ID that has no mapping
    msg_id = 0x789
    msg = can.Message(arbitration_id=msg_id, data=bytes([4, 5, 6]), is_extended_id=False)
    out_bus = FakeBus(recv_queue=[msg])
    in_bus = FakeBus()

    # Worker with rewrite rules that don't include this ID
    rewrite_rules = {0x123: 0x456}  # Doesn't include 0x789
    worker = CANWorker(input_config={}, output_config={}, rewrite_rules=rewrite_rules)

    # Bypass bus opening and set fake buses
    worker.input_bus = cast(can.BusABC, in_bus)
    worker.output_bus = cast(can.BusABC, out_bus)
    monkeypatch.setattr(worker, "_open_buses", lambda: True)

    # Capture signals
    received = []
    retransmitted = []
    worker.frame_received.connect(lambda m, ch: received.append((m, ch)))
    worker.frame_retransmitted.connect(lambda m, ch: retransmitted.append((m, ch)))

    th = _run_worker_in_thread(worker)

    # Wait for processing
    deadline = _time.time() + 1.0
    while _time.time() < deadline and not in_bus.sent:
        _time.sleep(0.01)
        qapp.processEvents()  # Process PyQt events including signals

    worker.stop()
    th.join(timeout=1.0)

    # Allow final signal processing
    qapp.processEvents()

    # Assert the message was forwarded to Input without ID change (passthrough)
    assert len(in_bus.sent) == 1
    assert in_bus.sent[0].arbitration_id == msg_id  # ID should remain unchanged
    assert bytes(in_bus.sent[0].data) == bytes([4, 5, 6])  # Data unchanged

    # Verify signals were emitted for passthrough
    assert len(received) == 1
    assert received[0][0].arbitration_id == msg_id  # Same ID in RX signal
    assert received[0][1] == 0  # Received on channel 0

    assert len(retransmitted) == 1
    assert retransmitted[0][0].arbitration_id == msg_id  # Same ID in TX signal
    assert retransmitted[0][1] == 1  # Transmitted to channel 1


def test_full_swap_bidirectional_with_mapping(qapp, monkeypatch):
    """Test Full Swap: Both directions apply ID mapping when rules exist."""
    # Messages for both directions with different mappings
    input_id = 0x100
    output_id = 0x200
    mapped_input_id = 0x101
    mapped_output_id = 0x201
    
    input_msg = can.Message(arbitration_id=input_id, data=bytes([1, 2]), is_extended_id=False)
    output_msg = can.Message(arbitration_id=output_id, data=bytes([3, 4]), is_extended_id=False)
    
    in_bus = FakeBus(recv_queue=[input_msg])
    out_bus = FakeBus(recv_queue=[output_msg])

    # Rewrite rules for both directions
    rewrite_rules = {
        input_id: mapped_input_id,    # Input->Output mapping
        output_id: mapped_output_id   # Output->Input mapping
    }
    worker = CANWorker(input_config={}, output_config={}, rewrite_rules=rewrite_rules)

    # Bypass bus opening and set fake buses
    worker.input_bus = cast(can.BusABC, in_bus)
    worker.output_bus = cast(can.BusABC, out_bus)
    monkeypatch.setattr(worker, "_open_buses", lambda: True)

    # Capture signals
    received = []
    retransmitted = []
    worker.frame_received.connect(lambda m, ch: received.append((m, ch)))
    worker.frame_retransmitted.connect(lambda m, ch: retransmitted.append((m, ch)))

    th = _run_worker_in_thread(worker)

    # Wait for processing
    deadline = _time.time() + 1.0
    while _time.time() < deadline and (len(in_bus.sent) + len(out_bus.sent)) < 2:
        _time.sleep(0.01)
        qapp.processEvents()  # Process PyQt events including signals

    worker.stop()
    th.join(timeout=1.0)

    # Allow final signal processing
    qapp.processEvents()

    # Verify both messages were processed with ID mapping
    assert len(out_bus.sent) == 1  # Input->Output
    assert out_bus.sent[0].arbitration_id == mapped_input_id

    assert len(in_bus.sent) == 1   # Output->Input
    assert in_bus.sent[0].arbitration_id == mapped_output_id

    # Verify signals for both directions
    assert len(received) == 2
    assert len(retransmitted) == 2
