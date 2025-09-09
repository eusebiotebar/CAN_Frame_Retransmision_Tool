# CAN Frame Retransmision Tool

[![CI](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml)
[![Auto Release](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml)
![Release](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/assets/release-badge.svg)
[![Download](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/assets/download-badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/releases/latest)

Tool for capturing and retransmitting CAN frames (scaffolding stage).

## Installation

### 🖥️ Windows Users (Recommended)

Download the latest `can-retransmit.exe` from [Releases](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/releases/latest) - no Python installation required!

### 🐍 Python Users

```bash
pip install can-frame-retransmision-tool
# or install from source
pip install git+https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool.git
```

## Features (Planned)

- Load and parse CAN frames
- Replay / retransmit frames to a CAN interface
- Basic GUI
- Export sessions

## Project Layout

```text
core/                Library code
resources/           Docs, version, requirements
scripts/             Helper scripts (build/test/install)
tests/               Pytest suite
.github/workflows/   CI pipelines
```

## Quick Start

```powershell
# Create/activate virtual env (example)
python -m venv .venv
./.venv/Scripts/Activate.ps1

pip install -e .[dev]
pytest -q
can-retransmit --help
```

### Build (PEP 517)

```powershell
pip install build
python -m build
```

The project now uses `pyproject.toml` (PEP 621). Development dependencies are installed via extras `[dev]`.

## Versioning

Semantic Versioning. See [`CHANGELOG.md`](resources/docs/CHANGELOG.md) for more details.

## License

[Apache 2.0](LICENSE)
