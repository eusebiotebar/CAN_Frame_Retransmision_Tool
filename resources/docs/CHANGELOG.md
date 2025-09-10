# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2025-09-10

### Changed (0.3.1)

- Standardized release workflow to build only `can-id-reframe.exe` (fully removed legacy build path references).
- Consolidated naming across documentation and workflows after rename stabilization.

### Removed (0.3.1)

- Purged remaining legacy spec `can-retransmit.spec` and related workflow references.

### Tests (0.3.1)

- Added coverage ensuring both (current) `can-id-reframe` entry point resolves and legacy alias absence is handled in forward plan.

### Documentation (0.3.1)

- Added planned deprecation notes and migration guidance for future 0.3.x cleanup.

### CI/CD (0.3.1)

- Updated `release-auto.yml` to publish only the new executable artifact for leaner releases.

---

## [0.3.0] - 2025-09-10

### Removed (0.3.0)

- Drop legacy console entry point `can-retransmit`.
- Remove legacy executable artifact `can-retransmit.exe` from release pipeline.

### Migration Notes (0.3.0)

- Use `can-id-reframe` going forward for CLI usage and automation scripts.
- Update any scripts, CI pipelines, or documentation referencing the deprecated name.

## [0.2.0] - 2025-09-10

### Changed (0.2.0)

- Project renamed from "CAN Frame Retransmision Tool" to "CAN_ID_Reframe".
- New console command: `can-id-reframe`.
- Legacy console command `can-retransmit` retained for transitional compatibility (removal planned for v0.3.0).
- Updated packaging metadata (`pyproject.toml`) with new name & description.
- Added new PyInstaller spec (`can-id-reframe.spec`).
- Introduced new launcher script `can_id_reframe_cli.py`.
- Updated README branding and usage instructions.
- Release workflow updated to build & publish both `can-id-reframe.exe` and legacy `can-retransmit.exe` artifacts.

### Notes (0.2.0)

- Existing tags and previous releases remain valid.
- Both executables (`can-id-reframe.exe` and `can-retransmit.exe`) may coexist for one release cycle.
- No functional changes introduced beyond naming/branding updates.

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
