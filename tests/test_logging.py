"""Tests for logging feature (REQ-FUNC-LOG-010)."""

from __future__ import annotations

import csv
import re
import tempfile
from pathlib import Path

import pytest

from core.frame_logger import FrameLogger


class DummyMsg:
    def __init__(self, arbitration_id: int, data: bytes, dlc: int, timestamp: float) -> None:
        self.arbitration_id = arbitration_id
        self.data = data
        self.dlc = dlc
        self.timestamp = timestamp


@pytest.mark.requirements(["REQ-FUNC-LOG-010", "REQ-FUNC-LOG-011"])
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
    # Direction present
    assert rows[1][1] == "RX" and rows[2][1] == "TX"
    # ID in hex (uppercase) as per implementation
    assert rows[1][2] == "123" and rows[2][2] == "456"
    # DLC present and correct
    assert rows[1][3] == "2" and rows[2][3] == "1"
    # Data field in uppercase hex
    assert rows[1][4] == "0102" and rows[2][4] == "AA"
    # Timestamp has millisecond precision (3 decimals)
    assert re.fullmatch(r"\d+\.\d{3}", rows[1][0])
    assert re.fullmatch(r"\d+\.\d{3}", rows[2][0])
    # And matches expected rounding of inputs
    assert rows[1][0] == "1726480000.123"
    # 1.999 has exactly 3 decimals, so formatting keeps it as 1.999
    assert rows[2][0] == "1726480001.999"
