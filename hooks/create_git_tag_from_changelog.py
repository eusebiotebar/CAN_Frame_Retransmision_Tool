#!/usr/bin/env python3
"""
Create Git Tag from Changelog

This script parses the CHANGELOG.md file and creates a git tag
based on the latest version entry.
"""

import re
import subprocess
import sys
from pathlib import Path


def get_latest_version_from_changelog(changelog_path: Path) -> str:
    """
    Extract the latest version from CHANGELOG.md.
    
    Args:
        changelog_path: Path to the CHANGELOG.md file
        
    Returns:
        Version string (e.g., "1.0.0")
    """
    if not changelog_path.exists():
        raise FileNotFoundError(f"Changelog file not found: {changelog_path}")
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for version headers like "## [1.0.0] - 2023-01-01"
    version_pattern = r'##\s*\[(\d+\.\d+\.\d+)\]'
    matches = re.findall(version_pattern, content)
    
    if not matches:
        raise ValueError("No version found in changelog")
    
    # Return the first (most recent) version
    return matches[0]


def check_if_tag_exists(tag: str) -> bool:
    """
    Check if a git tag already exists.
    
    Args:
        tag: Tag name to check
        
    Returns:
        True if tag exists, False otherwise
    """
    try:
        result = subprocess.run(
            ['git', 'tag', '-l', tag],
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def create_git_tag(version: str, message: str = None) -> bool:
    """
    Create a git tag for the given version.
    
    Args:
        version: Version string
        message: Tag message (optional)
        
    Returns:
        True if tag was created successfully or already exists
    """
    if message is None:
        message = f"Release version {version}"
    
    tag_name = f"v{version}"
    
    if check_if_tag_exists(tag_name):
        print(f"Tag {tag_name} already exists. No action needed.")
        return True
    
    try:
        # Create annotated tag
        subprocess.run(
            ['git', 'tag', '-a', tag_name, '-m', message],
            check=True
        )
        
        print(f"Created tag: {tag_name}")
        
        # Push the tag to origin
        subprocess.run(
            ['git', 'push', 'origin', tag_name],
            check=True
        )
        
        print(f"Pushed tag: {tag_name}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error creating tag: {e}")
        return False


def main():
    """Main function."""
    try:
        # Get project root directory
        project_root = Path(__file__).parent.parent
        changelog_path = project_root / "CHANGELOG.md"
        
        print(f"Reading changelog from: {changelog_path}")
        
        # Get latest version from changelog
        version = get_latest_version_from_changelog(changelog_path)
        print(f"Latest version from changelog: {version}")
        
        # Create git tag
        if create_git_tag(version):
            print("Tagging process completed successfully.")
            sys.exit(0)
        else:
            print("Failed to create tag")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
