"""
This module contains the FrameLogger class for logging CAN frames to a CSV file.
"""

import csv


class FrameLogger:
    """Logs CAN frames to a CSV file."""

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
            # Write header
            self._csv_writer.writerow(["Timestamp", "Direction", "ID", "DLC", "Data"])
            self.is_logging = True
        except (OSError, PermissionError) as e:
            # In a real GUI app, you'd want to show this error to the user.
            # For now, we just disable logging.
            self.is_logging = False
            # We could also re-raise a custom exception here to be caught by the GUI
            # and displayed in a dialog box.
            print(f"Error opening log file: {e}")

    def log_frame(self, direction: str, msg):
        """Logs a single CAN frame."""
        if not self.is_logging or not self._csv_writer:
            return

        timestamp = f"{msg.timestamp:.3f}"
        can_id = f"{msg.arbitration_id:X}"
        dlc = msg.dlc
        data = msg.data.hex().upper()

        self._csv_writer.writerow([timestamp, direction, can_id, dlc, data])

    def stop_logging(self):
        """Closes the log file."""
        if self.is_logging and self._log_file:
            self._log_file.close()
            self._log_file = None
            self._csv_writer = None
            self.is_logging = False
