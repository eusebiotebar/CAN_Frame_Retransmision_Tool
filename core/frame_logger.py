"""
This module contains the FrameLogger class for logging CAN frames to a CSV file.
"""

import csv


class FrameLogger:
    """Logs CAN frames to a CSV file with dual-channel support."""

    def __init__(self):
        self._log_file_path: str | None = None
        self._log_file = None
        self._csv_writer = None
        self.is_logging = False

    def set_log_path(self, log_file_path: str | None):
        """Sets the path for the log file."""
        self._log_file_path = log_file_path

    def start_logging(self):
        """Opens the log file and writes the CSV header."""
        if not self._log_file_path:
            return

        try:
            # Use newline='' to prevent blank rows in CSV
            # Note: We need to keep the file open for the duration of logging,
            # so we can't use a context manager here
            self._log_file = open(  # noqa: SIM115
                self._log_file_path, mode="w", newline="", encoding="utf-8"
            )
            self._csv_writer = csv.writer(self._log_file)
            # Write header with channel information
            self._csv_writer.writerow(["Timestamp", "Channel", "Direction", "ID", "DLC", "Data"])
            self.is_logging = True
        except (OSError, PermissionError) as e:
            # In a real GUI app, you'd want to show this error to the user.
            # For now, we just disable logging.
            self.is_logging = False
            # We could also re-raise a custom exception here to be caught by the GUI
            # and displayed in a dialog box.
            print(f"Error opening log file: {e}")

    def log_frame(self, direction: str, msg, channel: int = 0):
        """Logs a single CAN frame with channel information.
        
        Args:
            direction: Direction of the frame ("RX" or "TX")
            msg: CAN message object from python-can
            channel: Channel number (0 or 1)
        """
        if not self.is_logging or not self._csv_writer:
            return

        timestamp = f"{msg.timestamp:.3f}"
        can_id = f"{msg.arbitration_id:X}"
        dlc = msg.dlc
        data = msg.data.hex().upper()

        self._csv_writer.writerow([timestamp, channel, direction, can_id, dlc, data])

    def stop_logging(self):
        """Closes the log file."""
        if self.is_logging and self._log_file:
            self._log_file.close()
            self._log_file = None
            self._csv_writer = None
            self.is_logging = False
