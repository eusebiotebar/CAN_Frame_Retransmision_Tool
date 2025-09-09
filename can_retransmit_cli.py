#!/usr/bin/env python3
"""Entry point script for PyInstaller executable.

This script serves as the main entry point when the application
is built as a standalone executable with PyInstaller.
"""
import sys

from core.main import main_console

if __name__ == "__main__":
    sys.exit(main_console())
