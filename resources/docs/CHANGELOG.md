# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-09-09

### Added

- Initial project scaffolding with modern Python packaging (`pyproject.toml`)
- Console command `can-retransmit` for CAN frame retransmission tool
- Complete CI/CD pipeline with GitHub Actions (lint, test, build, deploy)
- Code quality tools: Ruff, Black, Mypy, Pytest
- Dynamic versioning from `version_info.txt`
- Automated version bumping from changelog
- Development environment with editable install and dev dependencies
- Basic module structure with `core.main`, `core.version`, `core.utils`
- Test suite with pytest configuration
- Documentation structure with README and changelog
