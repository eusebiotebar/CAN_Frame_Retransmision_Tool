"""Main application logic module.

Contains the console bootstrap logic for the tool.
"""
from __future__ import annotations

import sys

from .version import __version__


def get_version() -> str:
    return __version__


def main_console() -> int:
    """Console entry point."""
    try:
        print(f"CAN Frame Retransmission Tool v{__version__}")
        return 0
    except Exception as exc:  # noqa: BLE001 keep broad for CLI robustness
        print(f"Fatal error: {exc}")
        return 1


def main() -> int:
    """Compatibility wrapper for the entrypoint defined in pyproject."""
    return main_console()


if __name__ == "__main__":
    sys.exit(main_console())
