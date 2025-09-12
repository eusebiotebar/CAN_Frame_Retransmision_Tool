# CAN_ID_Reframe

[![CI](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/test-and-deploy.yml)
[![Auto Release](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml/badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/actions/workflows/release-auto.yml)
![Release](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/resources/assets/release-badge.svg)
[![Download](https://raw.githubusercontent.com/eusebiotebar/CAN_Frame_Retransmision_Tool/main/resources/assets/download-badge.svg)](https://github.com/eusebiotebar/CAN_Frame_Retransmision_Tool/releases/latest)

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
- **🔧 Physical CAN Device Support**: Auto-detection of Kvaser, PCAN, Vector, and SocketCAN devices
- **🎯 Frame Rewriting**: Advanced rule-based CAN ID transformation
- **📊 Session Management**: Export and manage CAN communication sessions
- **🚀 Standalone Executable**: No Python installation required for Windows users
- **🐧 Cross-platform**: Windows, Linux, and virtual CAN interface support

## Usage

### GUI Application (Primary Mode)

```bash
# Start the graphical interface
can-id-reframe
```

Or run the Windows executable directly: `can-id-reframe.exe`

The application will automatically detect available CAN devices:

- **Kvaser devices** (requires Kvaser drivers)
- **PCAN devices** (Windows - USB channels)
- **Vector devices** (Windows - with Vector drivers)
- **SocketCAN interfaces** (Linux - can0, can1, etc.)
- **Virtual channels** (vcan0, vcan1 for testing)

### Command Line Options

```bash
# Show version information
can-id-reframe --version

# Display help (for automation/CI)
can-id-reframe --help-cli
```

## Supported CAN Hardware

The application automatically detects and supports various CAN interfaces:

### Windows

- **Kvaser** - Professional CAN interfaces (requires Kvaser CANlib)
- **PCAN** - Peak-System USB CAN adapters (PCAN_USBBUS1-8)
- **Vector** - Vector CANoe/CANalyzer hardware

### Linux

- **SocketCAN** - Native Linux CAN interfaces (can0, can1, etc.)
- Requires CAN utilities: `sudo apt-get install can-utils`

### Testing/Development

- **Virtual CAN** - Software-only channels for testing (vcan0, vcan1)

### Hardware Setup

For **Kvaser devices** on Windows:

1. Install Kvaser drivers from [kvaser.com](https://www.kvaser.com)
2. Connect your Kvaser device
3. The application will auto-detect available channels

For **Linux SocketCAN**:

```bash
# Set up virtual CAN for testing
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0

# For real hardware (example)
sudo ip link set can0 up type can bitrate 500000
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
