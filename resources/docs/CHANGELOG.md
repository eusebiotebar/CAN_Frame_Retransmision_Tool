# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2025-09-12

### Added (0.6.0)

- **CAN Frame CSV Logging**: New `FrameLogger` class for comprehensive frame tracking
  - High-precision timestamp logging (millisecond accuracy)
  - Bidirectional logging (Input/Output frame direction tracking)
  - CSV format with columns: Timestamp, Direction, ID, DLC, Data
  - Robust error handling for file operations and permissions
- **Enhanced Development Scripts**: Comprehensive PowerShell and Bash automation
  - Multi-option build scripts with executable, wheel-only, and clean modes
  - Advanced test scripts with coverage, linting, typing, and filtering options
  - Cross-platform script compatibility for Windows and Linux/macOS
- **Application Icon**: Added custom application icon (`app_icon.ico`)
- **Comprehensive Documentation**: Extensive README updates with new features

### Changed (0.6.0)

- **Logging Architecture**: Replaced Python standard logging with specialized CAN frame logging
  - Removed application status logging in favor of communication data logging
  - Updated GUI to remove log level selection (no longer needed)
  - Streamlined main application initialization
- **Build System Enhancement**: Updated development workflow with modern tooling
  - Enhanced PowerShell scripts with parameter support and error handling
  - Improved test automation with multiple verification modes
  - Better integration with CI/CD pipeline requirements

### Removed (0.6.0)

- **Standard Application Logging**: Eliminated `logger_setup.py` module
  - Removed log level configuration from GUI
  - Simplified application startup without logging complexity

### Fixed (0.6.0)

- **Code Quality**: Resolved linting issues in `frame_logger.py`
  - Fixed SIM115 violation with proper noqa comment and justification
  - Improved code formatting for better maintainability
- **Frame Timestamp Accuracy**: Corrected timestamp precision in transmitted frames

### Technical Improvements (0.6.0)

- **Enhanced Scripts**: Complete rewrite of build and test automation
  - Support for PyInstaller executable generation
  - Coverage reporting with HTML output
  - Integrated linting with ruff and black
  - Type checking with mypy integration
- **Development Experience**: Improved developer workflow
  - Comprehensive documentation of script options
  - Better error messages and user feedback
  - Cross-platform compatibility enhancements

---

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
