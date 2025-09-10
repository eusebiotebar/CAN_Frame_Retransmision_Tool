# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2025-09-10

### Added (0.1.1)

- Integrated `create_git_tag_from_changelog.py` script into CI/CD workflow
- Automatic git tag creation when CHANGELOG.md is updated
- Improved version management system with automated tagging
- Added comprehensive documentation for automated tagging system

### Fixed (0.1.1)

- Fixed path references in bump-version workflow to use correct `core/version_info.txt` location
- Updated changelog path in create_git_tag_from_changelog.py script
- Standardized git configuration across all workflows (unified user/email)
- Optimized bump-version workflow by centralizing git config setup

## [0.1.0] - 2025-09-09

### Added (0.1.0)

- Initial project scaffolding with modern Python packaging (`pyproject.toml`)
- Console command `can-retransmit` for CAN frame retransmission tool
- **Windows executable (.exe) generation with PyInstaller**
- Complete CI/CD pipeline with GitHub Actions (lint, test, build, deploy)
- Multi-platform release builds (Python packages + Windows executable)
- Code quality tools: Ruff, Black, Mypy, Pytest
- Dynamic versioning from `version_info.txt`
- Automated version bumping from changelog
- Development environment with editable install and dev dependencies
- Basic module structure with `core.main`, `core.version`, `core.utils`
- Test suite with pytest configuration
- Documentation structure with README and changelog
