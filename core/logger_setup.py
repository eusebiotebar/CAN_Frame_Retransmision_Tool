"""Module for setting up application-wide logging."""

import logging
import sys

LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def setup_logging(log_level_str="INFO", log_file=None):
    """
    Configures the root logger for the application.

    Args:
        log_level_str (str): The desired logging level as a string.
        log_file (str, optional): Path to the log file. If None, logs only to console.
    """
    log_level = LOG_LEVELS.get(log_level_str.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicate logs on re-configuration
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Formatter for the logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-20s - %(levelname)-8s - %(message)s'
    )

    # Console Handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)
    root_logger.addHandler(stdout_handler)

    # File Handler (optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # If file logging fails, log an error to the console.
            root_logger.error(f"Failed to set up log file at {log_file}: {e}")

    logging.info(f"Logging configured. Level: {log_level_str}, File: {log_file}")
