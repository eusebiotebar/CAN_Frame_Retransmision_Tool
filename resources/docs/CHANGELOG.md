# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-09-11

### Added (0.5.0)

- **Physical CAN Device Support**: Auto-detection of real CAN hardware interfaces
- **Kvaser Device Detection**: Full support for Kvaser CAN devices with automatic channel detection
- **PCAN Device Support**: Detection of Peak-System USB CAN adapters on Windows (PCAN_USBBUS1-8)
- **Vector Device Support**: Integration with Vector CANoe/CANalyzer hardware on Windows
- **SocketCAN Support**: Native Linux CAN interface detection (can0, can1, etc.)
- **Cross-platform Hardware Detection**: Platform-specific device discovery for Windows and Linux
- **Enhanced Device Information**: Detailed device naming and interface identification

### Enhanced (0.5.0)

- **CAN Channel Detection**: Expanded from virtual-only to comprehensive physical device scanning
- **Error Handling**: Robust detection with graceful fallback when drivers are unavailable
- **Documentation**: Complete hardware setup guide with driver installation instructions
- **README**: Comprehensive documentation of supported CAN hardware and setup procedures

### Technical Improvements (0.5.0)

- **Type Safety**: Enhanced type annotations using modern Python syntax (`list[dict[str, str]]`)
- **Code Architecture**: Fixed thread naming conflicts by renaming `thread` to `_thread`
- **Import Organization**: Added `platform` module for cross-platform device detection
- **Error Logging**: Improved logging for device detection failures and warnings
- **Interface Abstraction**: Separated device detection logic into dedicated methods per platform

### Breaking Changes (0.5.0)

- **Hardware Requirements**: Physical CAN devices now require appropriate drivers to be detected
- **Platform Dependencies**: Some features now require platform-specific CAN libraries

---

## [0.4.0] - 2025-09-11

### Added (0.4.0)

- **Command-line argument support**: Added `--version` and `--help-cli` flags for better automation and CI integration
- **Improved startup handling**: Application now properly parses command-line arguments before initializing GUI components
- **Enhanced Windows executable**: Better compatibility with headless environments and CI systems

### Changed (0.4.0)

- **Optimized import structure**: GUI dependencies now load only when needed, improving startup performance for CLI operations
- **Better error handling**: More robust executable behavior in different runtime environments
- **Enhanced user experience**: Cleaner separation between CLI and GUI functionality

### Technical Improvements (0.4.0)

- Comprehensive code quality improvements with full English localization
- Enhanced CI/CD pipeline with comprehensive testing and coverage reporting
- Improved code formatting and linting compliance across entire codebase
- Better type safety with mypy integration
- Optimized release automation with improved Windows executable building

---

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
