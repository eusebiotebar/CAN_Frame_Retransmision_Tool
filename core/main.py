"""Main application logic module.

Contains the bootstrap logic for the PyQt6 application.
"""

import argparse
import sys

from .version import __version__


def main() -> int:
    """Main entry point for the PyQt6 application."""
    # Parse command line arguments first
    parser = argparse.ArgumentParser(
        prog="can-id-reframe",
        description=(
            "CAN Frame Retransmission Tool - GUI application for CAN bus "
            "analysis and retransmission"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--help-cli",
        action="store_true",
        help="Show this help message and exit (for CI testing)",
    )

    args = parser.parse_args()

    # Handle --help-cli for CI testing (exits without GUI)
    if args.help_cli:
        parser.print_help()
        return 0

    # Import PyQt6 only when we actually need the GUI
    from PyQt6.QtWidgets import QApplication

    from .gui import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return int(app.exec())


if __name__ == "__main__":
    sys.exit(main())
