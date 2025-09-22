"""Tests for version module."""

from unittest.mock import patch

from core.version import __version__, _load_version


def test_load_version_success():
    """Test successful version loading."""
    # __version__ should be loaded at import time
    assert isinstance(__version__, str)
    assert len(__version__) > 0
    # Should follow semantic versioning pattern (at least major.minor.patch)
    version_parts = __version__.split(".")
    assert len(version_parts) >= 3


def test_load_version_fallback_on_exception():
    """Test that _load_version returns '0.0.0' when exception occurs."""
    # Mock resources.files to raise an exception
    with patch("core.version.resources.files") as mock_files:
        mock_files.side_effect = FileNotFoundError("Test exception")
        result = _load_version()
        assert result == "0.0.0"


def test_load_version_fallback_on_missing_file():
    """Test that _load_version returns '0.0.0' when version file is missing."""
    # Mock the file open to raise an exception
    with patch("core.version.resources.files") as mock_files:
        mock_res_root = mock_files.return_value
        mock_version_path = mock_res_root.joinpath.return_value
        mock_version_path.open.side_effect = FileNotFoundError("File not found")
        
        result = _load_version()
        assert result == "0.0.0"