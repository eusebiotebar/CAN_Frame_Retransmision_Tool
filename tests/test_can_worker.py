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


def test_reverse_relay_output_to_input_is_silent(qapp, monkeypatch):
    """Output->Input relay should forward frames without emitting RX/TX signals."""
    # Prepare a message on the Output bus
    msg = can.Message(arbitration_id=0x123, data=bytes([1, 2, 3]), is_extended_id=False)
    out_bus = FakeBus(recv_queue=[msg])
    in_bus = FakeBus()

    # Worker with no rewrite rules
    worker = CANWorker(input_config={}, output_config={}, rewrite_rules={})

    # Bypass bus opening and set fake buses
    worker.input_bus = cast(can.BusABC, in_bus)
    worker.output_bus = cast(can.BusABC, out_bus)
    # Ensure run() does not overwrite our fake buses
    monkeypatch.setattr(worker, "_open_buses", lambda: True)

    # Capture signals
    received = []
    retransmitted = []
    worker.frame_received.connect(lambda m: received.append(m))
    worker.frame_retransmitted.connect(lambda m: retransmitted.append(m))

    th = _run_worker_in_thread(worker)

    # Wait up to a short time for the worker to process
    deadline = _time.time() + 1.0
    while _time.time() < deadline and not in_bus.sent:
        _time.sleep(0.01)

    worker.stop()
    th.join(timeout=1.0)

    # Assert the message was forwarded to Input
    assert len(in_bus.sent) == 1
    assert in_bus.sent[0].arbitration_id == 0x123
    assert bytes(in_bus.sent[0].data) == bytes([1, 2, 3])

    # No UI/log signals should have been emitted for reverse relay
    assert not received
    assert not retransmitted


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
