"""Update ``version_info.txt`` using the first release section in CHANGELOG.md. (EOL normalize)

Rules:
1. First heading with pattern ``## [X.Y.Z]`` (excluding Unreleased) determines the version.
2. If it differs from the current file, overwrite the file.
3. If there are no release sections, do nothing.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
CHANGELOG = ROOT / "resources" / "docs" / "CHANGELOG.md"
VERSION_FILE = ROOT / "resources" / "version_info.txt"
PYPROJECT = ROOT / "pyproject.toml"

RE_RELEASE = re.compile(r"^## \[(?P<ver>\d+\.\d+\.\d+)\]", re.MULTILINE)


def read_current_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def extract_latest_release() -> str | None:
    text = CHANGELOG.read_text(encoding="utf-8")
    for match in RE_RELEASE.finditer(text):
        ver = match.group("ver")
        if ver.lower() != "unreleased":  # guard
            return ver
    return None


def update_version_files(new_version: str) -> None:
    VERSION_FILE.write_text(f"{new_version}\n", encoding="utf-8")
    # pyproject stays dynamic; inert rewrite kept for potential future sync.
    py = PYPROJECT.read_text(encoding="utf-8")
    PYPROJECT.write_text(py, encoding="utf-8")


def main() -> int:
    if not CHANGELOG.exists():
        print("Changelog not found, skipping.")
        return 0
    current = read_current_version()
    latest = extract_latest_release()
    if not latest:
        print("No release section found; nothing to do.")
        return 0
    if latest == current or latest in current:
        print(f"Version already at {current}; nothing to do.")
        return 0
    update_version_files(latest)
    print(f"Updated version: {current} -> {latest}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())