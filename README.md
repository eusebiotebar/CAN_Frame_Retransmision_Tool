# CAN_ID_Reframe

[![CI](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml)
[![Auto Release](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml)
![Release](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/assets/release-badge.svg)
[![Download](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/assets/download-badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/releases/latest)

Tool for reframing / retransmitting CAN IDs (renamed from CAN Frame Retransmision Tool at v0.2.0).

## Installation

### 🖥️ Windows Users (Recommended)

Download the latest `can-id-reframe.exe` from [Releases](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/releases/latest) - no Python installation required!

### 🐍 Python Users

```bash
pip install can-id-reframe  # future published name
# or install from source
pip install git+https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool.git
```

## Features

- **🖥️ Cross-platform GUI**: PyQt6-based interface for CAN frame analysis
- **⚡ Real-time CAN Communication**: Load, parse, and retransmit CAN frames  
- **🔧 Command-line Support**: Built-in help and version information via CLI
- **📊 Session Management**: Export and manage CAN communication sessions
- **🎯 Frame Rewriting**: Advanced rule-based CAN ID transformation
- **🚀 Standalone Executable**: No Python installation required for Windows users

## Usage

### GUI Application (Primary Mode)

```bash
# Start the graphical interface
can-id-reframe
```

Or run the Windows executable directly: `can-id-reframe.exe`

### Command Line Options

```bash
# Show version information
can-id-reframe --version

# Display help (for automation/CI)
can-id-reframe --help-cli
```

## Features (Planned)

- Advanced CAN frame filtering and analysis
- Multiple CAN interface support  
- Session recording and playback
- Real-time frame monitoring dashboard

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

# Start the GUI application
can-id-reframe

# Or get command line help  
can-id-reframe --help-cli
```

### Build (PEP 517)

```powershell
pip install build
python -m build
```

The project now uses `pyproject.toml` (PEP 621). Development dependencies are installed via extras `[dev]`.

## Versioning

Semantic Versioning. Project renamed at v0.2.0 (backward compatible CLI alias until v0.3.0). See [`CHANGELOG.md`](resources/docs/CHANGELOG.md) for more details.

## License

[Apache 2.0](LICENSE)
