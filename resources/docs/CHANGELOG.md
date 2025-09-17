# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.3] - 2025-09-17

### Added (0.9.3)

- Windows: Added a console-only helper executable for CI/automation: `can-id-reframe-cli.exe` (same `--version` / `--help-cli` interface).

### Changed (0.9.3)

- Main GUI executable configured as windowed (`console=False`) to avoid showing a console window on startup.
- `can-id-reframe.spec`: now produces two executables: `can-id-reframe.exe` (GUI) and `can-id-reframe-cli.exe` (CLI).
- `README.md`: added a short note documenting the purpose of `can-id-reframe-cli.exe` for CI/automation.

### CI/CD (0.9.3)

- `test-and-deploy.yml`: Windows job now tests the CLI binary (`can-id-reframe-cli.exe --help-cli`) and publishes both executables as artifacts (`windows-executables`).
- `deploy-staging`: updated to download the `windows-executables` artifact.

---

## [0.9.2] - 2025-09-17

### Fixed (0.9.2)

- **CI/CD Pipeline Improvements**: Resolved critical issues with automated release process
  - Fixed executable icon missing in CI-built releases by using `.spec` file instead of direct PyInstaller command line parameters
  - Fixed `srvp_TR.md` test report not being committed back to repository after generation
  - Ensured consistency between local and CI build processes for Windows executable generation
  - CI-built executables now include application icon (`app_icon.ico`) matching local builds

### Changed (0.9.2)

- **Build Process Standardization**: Unified build approach across environments
  - CI now uses `pyinstaller can-id-reframe.spec --clean --noconfirm` matching local `scripts/build.ps1`
  - All PyInstaller configuration centralized in `.spec` file for better maintainability
  - Automated commit of generated `srvp_TR.md` to repository after CI test execution

### Technical Improvements (0.9.2)

- **Release Workflow Enhancement**: Better automation and artifact management
  - Added automatic commit step for SRVP Test Report in release workflow
  - Improved git configuration and conditional push logic for generated documents
  - Enhanced consistency between release assets and repository content

### Notes (0.9.2)

- This release focuses on CI/CD reliability and build consistency improvements
- No functional changes to application behavior
- Resolves issues where CI artifacts differed from local builds

---

## [0.9.1] - 2025-09-16

### Added (0.9.1)

- **Enhanced Test Coverage**: Comprehensive low-risk tests for GUI and utility functions
  - Added test coverage for `get_resource_path` in both development and frozen modes
  - Added test coverage for `format_can_frame` utility function
  - Added GUI tests for error handling, log path management, and recovery signals
  - Added tests for rewrite rules error handling and status updates
  - Overall test coverage increased to 76% with all quality gates passing

### Changed (0.9.1)

- **Recovery UI Enhancement (REQ-NFR-REL-001)**: Improved connection status feedback
  - GUI now displays "Reconnecting" status during recovery attempts
  - Enhanced recovery lifecycle with proper signal forwarding from CANManager
  - Added recovery success and failure path testing for reliability validation

### Fixed (0.9.1)

- **CI Pipeline Stability**: Resolved critical testing and linting issues
  - Fixed pytest hanging caused by modal QMessageBox.exec() blocking in headless environments
  - Resolved ruff I001 import formatting errors in test files
  - Applied proper monkeypatching to prevent GUI modal dialogs during automated testing
  - Ensured all import statements comply with ruff formatting standards (parenthesized multi-line imports)

### Technical Improvements (0.9.1)

- **Test Infrastructure**: Enhanced test reliability and maintainability
  - Implemented monkeypatching for GUI error dialogs to avoid CI blocking
  - Improved import organization and formatting across test files
  - Added comprehensive test validation for NFR-REL-001 auto-recovery requirements
  - Verified English language compliance in GUI components (gui.ui already compliant)

### Notes (0.9.1)

- All quality gates now pass: 42/42 tests, ruff linting, and mypy type checking
- This release focuses on test coverage improvements and CI reliability enhancements
- No breaking changes to application functionality

---

## [0.9.0] - 2025-09-16

### Added (0.9.0)

- Standalone SRVP Test Report is now published with each release
  - `resources/docs/srvp_TR.md` is attached as a Release asset (auto-release workflow)

### Changed (0.9.0)

- Renamed test report file from `srvp_test.md` to `srvp_TR.md`
- Updated `scripts/update_srvp.py` to write the report to `resources/docs/srvp_TR.md`
- Updated `README.md` link to point to the new report filename
- Updated `release-auto.yml` to include the SRVP Test Report as an additional asset

### Notes (0.9.0)

- This change does not affect application behavior; it improves documentation and release visibility.

---

## [0.8.0] - 2025-09-16

### Added (0.8.0)

- **SRVP Automation Script**: New `scripts/update_srvp.py` for automated test result integration
  - Automatically runs pytest and generates JSON test reports
  - Extracts requirement IDs from test docstrings using flexible regex patterns
  - Updates SRVP document with checkbox format for verified/failed requirements (`\[x] Verified`, `\[x] Failed`)
  - Comprehensive error handling and debug output for traceability
  - Saves updated SRVP document to `resources/docs/srvp_test.md`
- **Comprehensive Functional Testing**: Complete test suite for core CAN functionality
  - Virtual CAN bus testing with `test_can_logic.py` covering all REQ-FUNC-LOG requirements
  - GUI logic testing with `test_gui_logic.py` for interface and utility functions
  - Thread-safe signal testing using `threading.Event` with Qt `DirectConnection`
  - Mock-based testing for hardware detection and channel management

### Changed (0.8.0)

- **Simplified CI Pipeline**: Removed Black formatter from continuous integration
  - Eliminated Black dependency from `pyproject.toml` dev dependencies
  - Removed Black formatting checks from `scripts/test.sh` and `scripts/test.ps1`
  - Updated CI instructions to only require ruff and mypy verification
  - Streamlined linting process with single ruff check instead of dual ruff/Black validation

### Fixed (0.8.0)

- **Code Quality and Formatting**: Resolved all formatting and linting issues
  - Fixed line length violations in `tests/test_can_logic.py` to comply with ruff E501 rule
  - Resolved lambda function issues causing ruff B023 warnings in SRVP script
  - Corrected regex patterns for better docstring extraction and status matching
  - Fixed encoding issues in `scripts/update_srvp.py` for reliable cross-platform execution
- **Test Infrastructure**: Enhanced test reliability and maintainability
  - Removed duplicate test decorators and formatting inconsistencies
  - Fixed signal connection syntax for better Qt compatibility
  - Improved import organization and code structure in test files

### Removed (0.8.0)

- **Black Formatter Dependency**: Complete removal of Black from development workflow
  - Removed Black configuration section from `pyproject.toml`
  - Eliminated Black installation from test scripts
  - Updated development documentation to reflect simplified linting approach

### Technical Improvements (0.8.0)

- **Enhanced Development Experience**: More reliable and faster CI execution
  - Eliminates Black memory safety issues with Python 3.12.5
  - Reduces CI complexity and potential failure points
  - Maintains code quality standards with ruff linting alone
  - Faster CI execution without redundant formatting checks
- **Test Coverage**: Comprehensive functional requirement verification
  - All REQ-FUNC-LOG and REQ-FUNC-INT requirements now have automated tests
  - Virtual CAN hardware simulation for isolated testing environment
  - Robust error handling and signal delivery verification

### Benefits (0.8.0)

- **Simplified Maintenance**: Reduced tool complexity while maintaining code quality
- **Improved Reliability**: Elimination of CI failures due to Black formatting conflicts
- **Enhanced Traceability**: Automated SRVP document updates link tests to requirements
- **Better Testing**: Comprehensive functional test coverage for all core features

---

## [0.7.0] - 2025-09-15

### Added (0.7.0)

- Application and window icons integrated into the GUI (PyQt6)
  - New high-quality CAN relay icon (`can_relay_icon.{png,svg}`)
  - App icon bundled and applied (`app_icon.ico`)
- Dual frame visualization in the GUI for clear RX/TX separation
- PyInstaller bundling of icons and UI file via updated spec

### Changed (0.7.0)

- Improved GUI layout and elements in `core/gui.ui`
- Organized and formatted GUI module imports and code style (`core/gui.py`)
- README updated with features and usage refinements

### Technical Improvements (0.7.0)

- Streamlined application spec (`can-id-reframe.spec`) to include required assets
- Minor utilities enhancements in `core/utils.py`

---

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
