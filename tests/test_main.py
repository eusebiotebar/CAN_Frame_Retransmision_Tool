"""Tests for main module."""

import sys
from unittest.mock import patch

import pytest

from core.main import main


def test_main_help_cli_argument():
    """Test main function with --help-cli argument."""
    # Mock sys.argv to include --help-cli
    with patch.object(sys, "argv", ["can-id-reframe", "--help-cli"]):
        # Mock print to avoid actual output during tests
        with patch("builtins.print"):
            result = main()
            assert result == 0


def test_main_version_argument():
    """Test main function with --version argument."""
    # Mock sys.argv to include --version
    with patch.object(sys, "argv", ["can-id-reframe", "--version"]):
        # --version should cause SystemExit with code 0
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 0


def test_main_invalid_argument():
    """Test main function with invalid argument."""
    # Mock sys.argv to include invalid argument
    with patch.object(sys, "argv", ["can-id-reframe", "--invalid-arg"]):
        # Invalid argument should cause SystemExit with code 2
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 2