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
    Verify that FrameLogger writes CSV with header and frame rows.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()

        # Write two frames
        logger.log_frame("RX", DummyMsg(0x123, bytes([1, 2]), 2, 1726480000.123))
        logger.log_frame("TX", DummyMsg(0x456, bytes([0xAA]), 1, 1726480001.999))
        logger.stop_logging()

        # Read and assert contents
        assert log_path.exists()
        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

        assert rows[0] == ["Timestamp", "Direction", "ID", "DLC", "Data"]
        # Two data rows
        assert len(rows) == 3
        # Basic format assertions (timestamp with 3 decimals, uppercase hex)
        assert rows[1][1] == "RX" and rows[2][1] == "TX"
        assert rows[1][2] == "123" and rows[2][2] == "456"
        assert rows[1][4] == "0102" and rows[2][4] == "AA"


def test_frame_logger_formats_fields_per_req_log_011():
    """
    REQ-FUNC-LOG-011: Each log entry includes timestamp (ms), direction, ID, DLC,
    and Data in a human-readable format. This focuses on precise formatting validation
    without altering report-generation mechanisms.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test_log_req011.csv"

        logger = FrameLogger()
        logger.set_log_path(str(log_path))
        logger.start_logging()
        # Write a pair of frames with edge timestamps
        logger.log_frame("RX", DummyMsg(0x1A2B3C, bytes([0x00, 0xFF, 0x10]), 3, 1000.0))
        logger.log_frame("TX", DummyMsg(0x7FF, bytes([0xAB, 0xCD]), 2, 1000.4567))
        logger.stop_logging()

        with log_path.open(newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))

    # Header
    assert rows[0] == ["Timestamp", "Direction", "ID", "DLC", "Data"]
    # Two rows
    assert len(rows) == 3

    # Directions
    assert rows[1][1] == "RX" and rows[2][1] == "TX"

    # ID is uppercase hex without 0x prefix
    assert rows[1][2] == "1A2B3C"  # 0x1A2B3C -> "1A2B3C"
    assert rows[2][2] == "7FF"     # 0x7FF -> "7FF"

    # DLC matches
    assert rows[1][3] == "3" and rows[2][3] == "2"

    # Data is concatenated uppercase hex bytes
    assert rows[1][4] == "00FF10"
    assert rows[2][4] == "ABCD"

    # Timestamp formatted to 3 decimals
    assert re.fullmatch(r"\d+\.\d{3}", rows[1][0])
    assert re.fullmatch(r"\d+\.\d{3}", rows[2][0])
    # Check specific rounding/formatting
    assert rows[1][0].endswith(".000")
    assert rows[2][0].endswith(".457")  # 1000.4567 -> 1000.457
