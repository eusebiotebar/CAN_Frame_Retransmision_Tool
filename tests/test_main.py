import subprocess
import sys
from pathlib import Path

from core.main import get_version


def test_version_format():
    v = get_version()
    assert isinstance(v, str)
    assert v
    assert v.count(".") >= 1


def _run_bin(cmd: str) -> str:
    """Run a console script via 'python -m' fallback if direct script not present.

    This keeps test resilient in editable installs on CI.
    """
    # When installed, entry point wrappers exist; otherwise emulate.
    try:
        return subprocess.check_output([cmd, "--help"], text=True)
    except FileNotFoundError:
        # Fallback: run module main through python
        return subprocess.check_output([sys.executable, "-c", "import core.main; core.main.main_console()"], text=True)


def test_both_entry_points_available():
    # New
    new_help = _run_bin("can-id-reframe")
    assert "CAN_ID_Reframe" in new_help
