"""Utility functions for the CAN ID Reframe tool."""

class RuleParsingError(ValueError):
    """Custom exception for errors during rule parsing."""
    def __init__(self, message, row):
        super().__init__(message)
        self.row = row

def parse_rewrite_rules(table_data: list[tuple[str, str]]) -> dict[int, int]:
    """
    Parses a list of string tuples representing rewrite rules into a dictionary.

    Args:
        table_data: A list of tuples, where each tuple is (original_id_hex, rewritten_id_hex).

    Returns:
        A dictionary mapping integer original IDs to integer rewritten IDs.

    Raises:
        RuleParsingError: If any ID is not a valid hexadecimal string.
    """
    rules = {}
    for i, (original_text, rewritten_text) in enumerate(table_data):
        try:
            # Skip empty or whitespace-only entries
            if not original_text.strip() and not rewritten_text.strip():
                continue

            original_id = int(original_text, 16)
            rewritten_id = int(rewritten_text, 16)
            rules[original_id] = rewritten_id
        except (ValueError, TypeError) as e:
            # Raise a custom error with the problematic row number
            raise RuleParsingError(f"ID inválido en la fila {i + 1}. Los IDs deben ser valores hexadecimales.", row=i) from e
    return rules

def format_can_frame(frame: dict) -> str:
    """This function is not currently used by the GUI but is kept for potential CLI use."""
    frame_id = frame.get("id")
    data = frame.get("data", b"")
    hex_data = " ".join(f"{b:02X}" for b in data)
    return f"ID=0x{frame_id:X} DATA={hex_data}"
