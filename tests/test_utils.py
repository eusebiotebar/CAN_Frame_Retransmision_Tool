import sys
from pathlib import Path

import pytest

import core.utils as utils_mod
from core.utils import (RuleParsingError, format_can_frame, get_resource_path,
                        parse_rewrite_rules)


def test_parse_valid_rules():
    """Tests parsing a list of valid rule strings."""
    data = [
        ("100", "200"),
        ("1A", "BEEF"),
        ("fff", "0"),
    ]
    expected = {
        0x100: 0x200,
        0x1A: 0xBEEF,
        0xFFF: 0x0,
    }
    assert parse_rewrite_rules(data) == expected


def test_parse_with_empty_and_whitespace_rows():
    """Tests that empty or whitespace-only rows are correctly ignored."""
    data = [
        ("100", "200"),
        ("", ""),  # Should be ignored
        ("   ", "   "),  # Should be ignored
        ("1A", "BEEF"),
        ("   ", "DEAD"),  # Should fail
    ]
    with pytest.raises(RuleParsingError) as excinfo:
        parse_rewrite_rules(data)
    assert excinfo.value.row == 4  # 5th row, index 4

    # Test with only valid and empty rows
    valid_data = [
        ("100", "200"),
        ("", ""),
        ("1A", "BEEF"),
    ]
    expected = {0x100: 0x200, 0x1A: 0xBEEF}
    assert parse_rewrite_rules(valid_data) == expected


def test_parse_invalid_hex_value():
    """Tests that a non-hexadecimal value raises RuleParsingError."""
    data = [
        ("100", "200"),
        ("1A", "GHI"),  # 'G' is not a valid hex character
    ]
    with pytest.raises(RuleParsingError) as excinfo:
        parse_rewrite_rules(data)

    # Check that the exception message contains the correct row number
    assert "row 2" in str(excinfo.value)
    assert excinfo.value.row == 1  # Row index should be 1


def test_parse_empty_list():
    """Tests that parsing an empty list results in an empty dictionary."""
    assert parse_rewrite_rules([]) == {}


def test_one_value_is_empty():
    """Tests a row where one of the values is missing."""
    data = [
        ("100", "200"),
        ("1A", ""),
    ]
    with pytest.raises(RuleParsingError):
        parse_rewrite_rules(data)


def test_malformed_hex_prefix():
    """Tests that '0x' prefixes are handled correctly (or not, as per int(_, 16))."""
    data = [("0x100", "0x200")]
    expected = {0x100: 0x200}
    assert parse_rewrite_rules(data) == expected

    data_malformed = [("0x100", "0xG")]
    with pytest.raises(RuleParsingError):
        parse_rewrite_rules(data_malformed)


def test_get_resource_path_dev_mode(monkeypatch):
    """When not frozen, resources resolve relative to project root (parent of 'core')."""
    # Ensure non-frozen
    monkeypatch.delenv("PYINSTALLER_TEST", raising=False)
    monkeypatch.setattr(sys, "frozen", False, raising=False)

    # Expected base is parent of core package directory
    core_file = Path(utils_mod.__file__).resolve()
    expected_base = core_file.parents[1]

    p = get_resource_path("resources", "images", "app_icon.ico")
    assert str(p).startswith(str(expected_base))
    # Joining behavior should be correct even if file may not exist
    assert p.as_posix().endswith("resources/images/app_icon.ico")


def test_get_resource_path_frozen_mode(monkeypatch, tmp_path):
    """When frozen, path resolves under sys._MEIPASS."""
    # Simulate PyInstaller environment
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    p = get_resource_path("data", "file.txt")
    assert str(p).startswith(str(tmp_path))
    assert p.as_posix().endswith("data/file.txt")


def test_format_can_frame():
    """format_can_frame returns expected string with hex data spacing."""
    frame = {"id": 0x1A2, "data": bytes([0x00, 0xAB, 0x7F])}
    s = format_can_frame(frame)
    assert "ID=0x1A2" in s
    assert "DATA=00 AB 7F" in s
