#!/usr/bin/env python3
"""Create a git tag from the first version section in CHANGELOG.md."""

import re
import subprocess
import sys
from pathlib import Path


def get_latest_version_from_changelog(changelog_path: Path) -> str:
    """Return the first found version header (## [X.Y.Z])."""
    if not changelog_path.exists():
        raise FileNotFoundError(f"Changelog file not found: {changelog_path}")
    with open(changelog_path, encoding="utf-8") as fh:
        content = fh.read()
    version_pattern = r"##\s*\[(\d+\.\d+\.\d+)\]"
    matches = re.findall(version_pattern, content)
    if not matches:
        raise ValueError("No version found in changelog")
    return matches[0]


def check_if_tag_exists(tag: str) -> bool:
    """Return True if the tag already exists."""
    try:
        result = subprocess.run(
            ["git", "tag", "-l", tag], capture_output=True, text=True, check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def create_git_tag(version: str, message: str | None = None) -> bool:
    """Create and push an annotated tag."""
    if message is None:
        message = f"Release version {version}"
    tag_name = f"v{version}"
    if check_if_tag_exists(tag_name):
        print(f"Tag {tag_name} already exists. No action needed.")
        return True
    try:
        subprocess.run(["git", "tag", "-a", tag_name, "-m", message], check=True)
        print(f"Created tag: {tag_name}")
        subprocess.run(["git", "push", "origin", tag_name], check=True)
        print(f"Pushed tag: {tag_name}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"Error creating tag: {exc}")
        return False


def main() -> None:
    try:
        project_root = Path(__file__).parent.parent
        changelog_path = project_root / "CHANGELOG.md"
        print(f"Reading changelog from: {changelog_path}")
        version = get_latest_version_from_changelog(changelog_path)
        print(f"Latest version from changelog: {version}")
        if create_git_tag(version):
            print("Tagging process completed successfully.")
            sys.exit(0)
        print("Failed to create tag")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 broad for CLI robustness
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
