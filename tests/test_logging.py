"""Tests for logging feature (REQ-FUNC-LOG-010/011)."""

from __future__ import annotations

import csv
import re
import tempfile
from pathlib import Path

from core.frame_logger import FrameLogger


class DummyMsg:
    def __init__(self, arbitration_id: int, data: bytes, dlc: int, timestamp: float) -> None:
        self.arbitration_id = arbitration_id
        self.data = data
        self.dlc = dlc
        self.timestamp = timestamp


def test_frame_logger_writes_csv():
    """
    REQ-FUNC-LOG-010: Provide configurable console/file logging for operational events.
    Verify that FrameLogger writes CSV with header and frame rows including channel info.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()

        # Write two frames with different channels
        logger.log_frame("RX", DummyMsg(0x123, bytes([1, 2]), 2, 1726480000.123), 0)
        logger.log_frame("TX", DummyMsg(0x456, bytes([0xAA]), 1, 1726480001.999), 1)
        logger.stop_logging()

        # Read and assert contents
        assert log_path.exists()
        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        assert rows[0] == ["Timestamp", "Channel", "Direction", "ID", "DLC", "Data"]
        # Two data rows
        assert len(rows) == 3
        # Basic format assertions (timestamp with 3 decimals, uppercase hex)
        assert rows[1][1] == "0" and rows[1][2] == "RX"  # Channel 0, RX
        assert rows[2][1] == "1" and rows[2][2] == "TX"  # Channel 1, TX
        assert rows[1][3] == "123" and rows[2][3] == "456"
        assert rows[1][5] == "0102" and rows[2][5] == "AA"


def test_frame_logger_formats_fields_per_req_log_011():
    """
    REQ-FUNC-LOG-011: Each log entry includes timestamp (ms), channel, direction, ID, DLC,
    and Data in a human-readable format. This focuses on precise formatting validation
    without altering report-generation mechanisms.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log_req011.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()
        # Write a pair of frames with edge timestamps and different channels
        logger.log_frame("RX", DummyMsg(0x1A2B3C, bytes([0x00, 0xFF, 0x10]), 3, 1000.0), 0)
        logger.log_frame("TX", DummyMsg(0x7FF, bytes([0xAB, 0xCD]), 2, 1000.4567), 1)
        logger.stop_logging()

        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

    # Header
    assert rows[0] == ["Timestamp", "Channel", "Direction", "ID", "DLC", "Data"]
    # Two rows
    assert len(rows) == 3

    # Channel and directions
    assert rows[1][1] == "0" and rows[1][2] == "RX"  # Channel 0, RX
    assert rows[2][1] == "1" and rows[2][2] == "TX"  # Channel 1, TX

    # ID is uppercase hex without 0x prefix
    assert rows[1][3] == "1A2B3C"  # 0x1A2B3C -> "1A2B3C"
    assert rows[2][3] == "7FF"     # 0x7FF -> "7FF"

    # DLC matches
    assert rows[1][4] == "3" and rows[2][4] == "2"

    # Data is concatenated uppercase hex bytes
    assert rows[1][5] == "00FF10"
    assert rows[2][5] == "ABCD"

    # Timestamp formatted to 3 decimals
    assert re.fullmatch(r"\d+\.\d{3}", rows[1][0])
    assert re.fullmatch(r"\d+\.\d{3}", rows[2][0])
    # Check specific rounding/formatting
    assert rows[1][0].endswith(".000")
    assert rows[2][0].endswith(".457")  # 1000.4567 -> 1000.457


def test_frame_logger_dual_channel_grouping():
    """
    Test dual-channel logging with proper grouping by channel and direction.
    Verifies that messages from both channels are logged with correct channel information.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_dual_channel_log.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()

        # Write frames for both channels and both directions
        logger.log_frame("RX", DummyMsg(0x100, bytes([0x01]), 1, 1000.0), 0)  # Channel 0 RX
        logger.log_frame("TX", DummyMsg(0x200, bytes([0x02]), 1, 1000.1), 0)  # Channel 0 TX
        logger.log_frame("RX", DummyMsg(0x300, bytes([0x03]), 1, 1000.2), 1)  # Channel 1 RX
        logger.log_frame("TX", DummyMsg(0x400, bytes([0x04]), 1, 1000.3), 1)  # Channel 1 TX
        logger.stop_logging()

        # Read and verify grouping
        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        # Header row
        assert rows[0] == ["Timestamp", "Channel", "Direction", "ID", "DLC", "Data"]
        # Four data rows
        assert len(rows) == 5

        # Verify each frame has correct channel and direction
        assert rows[1][1] == "0" and rows[1][2] == "RX" and rows[1][3] == "100"
        assert rows[2][1] == "0" and rows[2][2] == "TX" and rows[2][3] == "200"
        assert rows[3][1] == "1" and rows[3][2] == "RX" and rows[3][3] == "300"
        assert rows[4][1] == "1" and rows[4][2] == "TX" and rows[4][3] == "400"


def test_frame_logger_backward_compatibility():
    """
    Test that the logger maintains backward compatibility when channel is not provided.
    Default channel should be 0.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_backward_compat_log.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()

        # Write frame without specifying channel (should default to 0)
        logger.log_frame("RX", DummyMsg(0x123, bytes([0xAB]), 1, 1000.0))
        logger.stop_logging()

        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        # Verify default channel is 0
        assert rows[1][1] == "0"  # Channel column should be "0"
        assert rows[1][2] == "RX"  # Direction column


def test_frame_logger_no_log_path():
    """
    Test that logger handles gracefully when no log path is set.
    This should cover the early return in start_logging when path is None.
    """
    logger = FrameLogger()
    # Don't set any log path
    logger.start_logging()  # Should return early without error
    
    # Logger should not be active
    assert not logger.is_logging
    
    # Trying to log should be safe (no-op)
    logger.log_frame("RX", DummyMsg(0x123, bytes([0xAB]), 1, 1000.0), 0)


def test_frame_logger_invalid_file_path():
    """
    Test error handling when log file cannot be opened.
    This covers the exception handling in start_logging.
    """
    logger = FrameLogger()
    # Set an invalid path (directory that doesn't exist or invalid name)
    logger.set_log_path("/invalid/nonexistent/path/test.csv")
    logger.start_logging()
    
    # Logger should not be active due to file error
    assert not logger.is_logging


def test_frame_logger_no_logging_active():
    """
    Test that log_frame returns early when logging is not active.
    This covers the early return in log_frame method.
    """
    logger = FrameLogger()
    # Don't start logging
    assert not logger.is_logging
    
    # Try to log a frame - should return early without error
    logger.log_frame("RX", DummyMsg(0x123, bytes([0xAB]), 1, 1000.0), 0)
