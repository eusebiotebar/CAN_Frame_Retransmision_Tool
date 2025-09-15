"""Utility functions for the CAN ID Reframe tool."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import cast


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
            raise RuleParsingError(
                f"Invalid ID in row {i + 1}. IDs must be hexadecimal values.", row=i
            ) from e
    return rules


def format_can_frame(frame: dict) -> str:
    """This function is not currently used by the GUI but is kept for potential CLI use."""
    frame_id = frame.get("id")
    data = frame.get("data", b"")
    hex_data = " ".join(f"{b:02X}" for b in data)
    return f"ID=0x{frame_id:X} DATA={hex_data}"


# ---------------------------------------------------------------------------
# Resource helpers
# ---------------------------------------------------------------------------
def get_resource_path(*parts: str | Path) -> Path:
    """Return an absolute path to a resource bundled with the app.

    Works both in development and when frozen with PyInstaller.

    - When frozen (``sys.frozen``), resources are looked up under ``sys._MEIPASS``.
    - In development, resources are resolved relative to the project root
      (the parent directory of the ``core`` package).
    """
    # Base directory for resources when frozen by PyInstaller
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # mypy: sys._MEIPASS is injected by PyInstaller at runtime
        try:
            meipass_obj = cast(object, sys)
            meipass = object.__getattribute__(meipass_obj, "_MEIPASS")
            base = Path(cast(str, meipass))
        except Exception:
            base = Path.cwd()
    else:
        # core/utils.py -> parent is 'core', parent of that is the project root
        base = Path(__file__).resolve().parents[1]
    return base.joinpath(*map(str, parts))
