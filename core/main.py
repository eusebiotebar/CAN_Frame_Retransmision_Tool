"""Main application logic module.

Contains the bootstrap logic for the PyQt6 application.
"""

import sys
from PyQt6.QtWidgets import QApplication
from .gui import MainWindow
from .logger_setup import setup_logging


def main() -> int:
    """Main entry point for the PyQt6 application."""
    # Set up initial logging before the GUI starts
    setup_logging()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
