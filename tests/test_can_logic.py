"""Tests for the core CAN bus retransmission logic (REQ-FUNC-LOG-*)."""

import contextlib
import threading
import time
from collections import deque

import can
import pytest
from PyQt6.QtCore import Qt

from core.can_logic import CANWorker


@pytest.fixture(scope="function")
def virtual_can_buses():
    """Create a pair of virtual CAN buses for testing."""
    buses = deque()
    buses.append(
        can.interface.Bus(channel="vcan0", interface="virtual", receive_own_messages=False)
    )
    buses.append(
        can.interface.Bus(channel="vcan1", interface="virtual", receive_own_messages=True)
    )

    yield buses

    # Shutdown buses after test execution
    for bus in buses:
        with contextlib.suppress(can.CanError):
            bus.shutdown()


def test_can_frame_is_rewritten_and_retransmitted(virtual_can_buses):
    """
    Verify that a CAN frame is rewritten and retransmitted according to rules.
    Covers: REQ-FUNC-LOG-004, REQ-FUNC-LOG-005
    """
    input_bus, output_bus_listener = virtual_can_buses

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}
    rewrite_rules = {0x100: 0x200}

    worker = CANWorker(input_config, output_config, rewrite_rules)
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    msg_to_send = can.Message(arbitration_id=0x100, data=[1, 2, 3])
    input_bus.send(msg_to_send)

    received_msg = output_bus_listener.recv(timeout=1.0)

    worker.stop()
    worker_thread.join(timeout=1.0)

    assert received_msg is not None
    assert received_msg.arbitration_id == 0x200
    assert received_msg.data == msg_to_send.data


def test_can_frame_is_passed_through_when_no_rule_matches(virtual_can_buses):
    """
    Verify that a CAN frame is passed through with its original ID if no rule matches.
    Covers: REQ-FUNC-LOG-004, REQ-FUNC-LOG-005
    """
    input_bus, output_bus_listener = virtual_can_buses

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}
    rewrite_rules = {0x100: 0x200}

    worker = CANWorker(input_config, output_config, rewrite_rules)
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    msg_to_send = can.Message(arbitration_id=0x300, data=[4, 5, 6])
    input_bus.send(msg_to_send)

    received_msg = output_bus_listener.recv(timeout=1.0)

    worker.stop()
    worker_thread.join(timeout=1.0)

    assert received_msg is not None
    assert received_msg.arbitration_id == 0x300
    assert received_msg.data == msg_to_send.data


def test_retransmission_stops_when_worker_is_stopped(virtual_can_buses):
    """
    Verify that no more frames are processed after the worker is stopped.
    Covers: REQ-FUNC-LOG-006
    """
    input_bus, output_bus_listener = virtual_can_buses

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}
    rewrite_rules = {0x100: 0x200}

    worker = CANWorker(input_config, output_config, rewrite_rules)
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    input_bus.send(can.Message(arbitration_id=0x100))
    first_msg = output_bus_listener.recv(timeout=1.0)
    assert first_msg is not None

    worker.stop()
    worker_thread.join(timeout=1.0)

    input_bus.send(can.Message(arbitration_id=0x100))
    second_msg = output_bus_listener.recv(timeout=0.5)
    assert second_msg is None


def test_worker_handles_bus_creation_error():
    """
    Verify that the worker handles an error during bus creation gracefully.
    Covers: REQ-FUNC-LOG-001, REQ-FUNC-LOG-007
    """
    input_config = {"interface": "nonexistent", "channel": "dummy"}
    output_config = {"interface": "virtual", "channel": "vcan1"}

    error_message = None
    error_event = threading.Event()

    def on_error(msg):
        nonlocal error_message
        error_message = msg
        error_event.set()

    worker = CANWorker(input_config, output_config, {})
    worker.error_occurred.connect(on_error)

    worker.run()

    assert error_event.wait(timeout=1.0), "The error_occurred signal was not emitted"
    assert error_message is not None
    assert "Error in CAN worker" in error_message


def test_signals_are_emitted_for_frames(virtual_can_buses):
    """
    Verify that frame_received and frame_retransmitted signals are emitted.
    Covers: REQ-FUNC-LOG-003
    """
    input_bus, _ = virtual_can_buses

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}

    received_frames = []
    retransmitted_frames = []
    received_event = threading.Event()
    retransmitted_event = threading.Event()

    def on_receive(msg):
        received_frames.append(msg)
        received_event.set()

    def on_retransmit(msg):
        retransmitted_frames.append(msg)
        retransmitted_event.set()

    worker = CANWorker(input_config, output_config, {})
    worker.frame_received.connect(on_receive, type=Qt.ConnectionType.DirectConnection)
    worker.frame_retransmitted.connect(on_retransmit, type=Qt.ConnectionType.DirectConnection)

    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    msg_to_send = can.Message(arbitration_id=0x123, data=[1])
    input_bus.send(msg_to_send)

    assert received_event.wait(timeout=2.0), "frame_received signal timed out"
    assert retransmitted_event.wait(timeout=2.0), "frame_retransmitted signal timed out"

    worker.stop()
    worker_thread.join(timeout=1.0)

    assert len(received_frames) == 1
    assert received_frames[0].arbitration_id == 0x123
    assert len(retransmitted_frames) == 1
    assert retransmitted_frames[0].arbitration_id == 0x123


def test_continuous_monitoring_receives_multiple_frames(virtual_can_buses):
    """
    REQ-FUNC-LOG-002: While in Listening/Receiving state, continuously monitor input channel.
    Send multiple frames and verify that multiple retransmissions occur.
    """
    input_bus, output_bus_listener = virtual_can_buses

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}

    worker = CANWorker(input_config, output_config, {})
    worker_thread = threading.Thread(target=worker.run, daemon=True)
    worker_thread.start()
    time.sleep(0.1)

    # Send a burst of frames
    total = 5
    for i in range(total):
        input_bus.send(can.Message(arbitration_id=0x100 + i, data=[i]))

    # Collect outputs
    received = []
    t_end = time.time() + 2.0
    while time.time() < t_end and len(received) < total:
        msg = output_bus_listener.recv(timeout=0.1)
        if msg is not None:
            received.append(msg)

    worker.stop()
    worker_thread.join(timeout=1.0)

    assert len(received) >= total, f"Expected >= {total} retransmissions, got {len(received)}"


def test_bitrate_mismatch_error_emits_signal(monkeypatch):
    """
    REQ-FUNC-LOG-008: Handle bitrate mismatch detected by backend by reporting an error.
    Simulate bus creation raising a CanError('Bitrate mismatch').
    """
    # Patch Bus to raise on creation
    def raise_on_create(**kwargs):  # noqa: ARG001
        raise can.CanError("Bitrate mismatch")

    monkeypatch.setattr(can.interface, "Bus", raise_on_create)

    input_config = {"interface": "virtual", "channel": "vcan0", "bitrate": 500000}
    output_config = {"interface": "virtual", "channel": "vcan1", "bitrate": 500000}

    worker = CANWorker(input_config, output_config, {})

    error_message = None
    error_event = threading.Event()

    def on_error(msg):
        nonlocal error_message
        error_message = msg
        error_event.set()

    worker.error_occurred.connect(on_error)

    # Run synchronously
    worker.run()

    assert error_event.wait(timeout=1.0)
    assert error_message is not None
    assert "Error in CAN worker" in error_message
    assert "Bitrate mismatch" in error_message


def test_bus_off_condition_reported(monkeypatch):
    """
    REQ-FUNC-LOG-009: Detect and report CAN bus-off condition on input channel.
    Simulate recv() raising a CanError('bus off').
    """

    class FakeInputBus:
        def recv(self, timeout: float | None = None):  # noqa: ARG002
            raise can.CanError("bus off")

        def shutdown(self):
            return None

    class FakeOutputBus:
        def send(self, msg):  # noqa: ARG002
            return None

        def shutdown(self):
            return None

    # First Bus() call returns input, second returns output
    calls = []

    def bus_side_effect(**kwargs):  # noqa: ARG001
        if not calls:
            calls.append("in")
            return FakeInputBus()
        return FakeOutputBus()

    monkeypatch.setattr(can.interface, "Bus", bus_side_effect)

    input_config = {"interface": "virtual", "channel": "vcan0"}
    output_config = {"interface": "virtual", "channel": "vcan1"}

    worker = CANWorker(input_config, output_config, {})

    error_message = None
    error_event = threading.Event()

    def on_error(msg):
        nonlocal error_message
        error_message = msg
        error_event.set()

    worker.error_occurred.connect(on_error, type=Qt.ConnectionType.DirectConnection)

    # Run synchronously (will error on first recv)
    worker.run()

    assert error_event.wait(timeout=1.0)
    assert error_message is not None
    assert "Error in CAN worker" in error_message
    assert "bus off" in error_message.lower()


@pytest.mark.skip(reason="NFR-REL-001 auto-recovery not implemented yet")
def test_auto_recovery_after_bus_off(monkeypatch):
    """
    REQ-NFR-REL-001: On bus-off, system attempts to re-open the channel after a delay
    and resumes retransmission up to N retries. This is a skeleton test to be
    implemented alongside retry logic in CANManager/CANWorker.
    """
    # Plan: simulate recv raising CanError('bus off') for the first iteration,
    # then succeed and verify that frames flow again after a retry.
    # Implementation pending retry mechanism.
    pass
