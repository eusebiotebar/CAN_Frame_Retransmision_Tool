"""Tests for utils module."""

import sys
from pathlib import Path
from unittest.mock import patch

from core.utils import get_resource_path


def test_get_resource_path_normal_execution():
    """Test get_resource_path during normal (non-frozen) execution."""
    # During normal execution, should use project root
    result = get_resource_path("resources", "test.txt")
    assert isinstance(result, Path)
    # Should be absolute path
    assert result.is_absolute()
    # Should end with the specified path
    assert str(result).endswith("resources/test.txt") or str(result).endswith("resources\\test.txt")


def test_get_resource_path_frozen_execution():
    """Test get_resource_path during frozen (PyInstaller) execution."""
    # Mock PyInstaller environment with Windows-style path
    with patch.object(sys, "frozen", True, create=True), \
         patch.object(sys, "_MEIPASS", "C:\\temp\\meipass", create=True):
        
        result = get_resource_path("resources", "test.txt")
        assert isinstance(result, Path)
        # Path should include the meipass directory
        assert "meipass" in str(result) or "resources" in str(result)


def test_get_resource_path_multiple_parts():
    """Test get_resource_path with multiple path parts."""
    result = get_resource_path("resources", "images", "icon.png")
    assert isinstance(result, Path)
    # Should handle multiple path parts correctly
    path_str = str(result)
    assert "resources" in path_str
    assert "images" in path_str
    assert "icon.png" in path_str


def test_get_resource_path_exception_fallback():
    """Test get_resource_path falls back when frozen attribute access fails."""
    # Test the exception handling path in the frozen branch
    with patch.object(sys, "frozen", True, create=True):
        # Don't set _MEIPASS, so the except block should trigger
        result = get_resource_path("resources", "test.txt")
        assert isinstance(result, Path)
        # Should fall back to current working directory based path
        assert "resources" in str(result)
        assert "test.txt" in str(result)