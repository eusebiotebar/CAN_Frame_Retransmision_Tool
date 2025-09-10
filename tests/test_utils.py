import pytest
from core.utils import parse_rewrite_rules, RuleParsingError

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
        ("", ""),          # Should be ignored
        ("   ", "   "),    # Should be ignored
        ("1A", "BEEF"),
        ("   ", "DEAD"),   # Should fail
    ]
    with pytest.raises(RuleParsingError) as excinfo:
        parse_rewrite_rules(data)
    assert excinfo.value.row == 4 # 5th row, index 4

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
    assert "fila 2" in str(excinfo.value)
    assert excinfo.value.row == 1 # Row index should be 1

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
