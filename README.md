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
- **� Frame Logging**: CSV logging of CAN frames with timestamps and metadata
- **�🚀 Standalone Executable**: No Python installation required for Windows users
- **🐧 Cross-platform**: Windows, Linux, and virtual CAN interface support
- **🛠️ Enhanced Build Scripts**: Comprehensive PowerShell and Bash scripts for development

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

## CAN Frame Logging

The application includes comprehensive CAN frame logging functionality:

### Logging Features

- **CSV Export**: Automatic logging of CAN frames to CSV files
- **Timestamp Precision**: High-precision timestamps (millisecond accuracy)
- **Bidirectional Logging**: Separate tracking of input and output frames
- **Metadata Capture**: Frame ID, DLC, data payload, and direction
- **Error Handling**: Robust file operations with permission and I/O error handling

### CSV Format

The logged CSV files contain the following columns:

| Column    | Description                           | Example        |
|-----------|---------------------------------------|----------------|
| Timestamp | Frame timestamp (seconds.milliseconds) | 1694520123.456 |
| Direction | Frame direction (Input/Output)        | Input          |
| ID        | CAN ID in hexadecimal                | 123            |
| DLC       | Data Length Code                     | 8              |
| Data      | Frame data in hex format             | 1234567890ABCDEF |

## Features (Planned)

- Advanced CAN frame filtering and analysis
- Real-time frame monitoring dashboard

## Project Layout

```text
core/                Library code
├── frame_logger.py  CAN frame CSV logging functionality
├── gui.py          Main PyQt6 GUI interface
├── can_logic.py    CAN communication logic
├── utils.py        Utility functions and parsers
└── ...             Other core modules
resources/           Docs, version, requirements
├── images/         Application icons and assets
└── docs/           Documentation and changelogs
scripts/             Enhanced build/test/install scripts
├── build.ps1/.sh   Cross-platform build automation
└── test.ps1/.sh    Comprehensive testing with linting
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

### Development Scripts

The project includes enhanced PowerShell and Bash scripts for streamlined development:

#### Build Scripts

```powershell
# Windows (PowerShell)
.\scripts\build.ps1                    # Basic build (wheel + sdist)
.\scripts\build.ps1 -WheelOnly         # Build wheel only
.\scripts\build.ps1 -Executable        # Include PyInstaller executable
.\scripts\build.ps1 -Clean -Executable # Clean build with executable
```

```bash
# Linux/macOS (Bash)
./scripts/build.sh                     # Basic build
./scripts/build.sh --wheel-only        # Build wheel only
./scripts/build.sh --executable        # Include executable
./scripts/build.sh --clean --executable # Clean build with executable
```

#### Test Scripts

```powershell
# Windows (PowerShell)
.\scripts\test.ps1                     # Basic tests
.\scripts\test.ps1 -Coverage           # Tests with coverage report
.\scripts\test.ps1 -Linting            # Include linting (black + ruff)
.\scripts\test.ps1 -Typing             # Include type checking (mypy)
.\scripts\test.ps1 -All                # Full test suite
.\scripts\test.ps1 -Filter "pattern"   # Run specific tests
```

```bash
# Linux/macOS (Bash)
./scripts/test.sh                      # Basic tests
./scripts/test.sh --coverage           # Tests with coverage
./scripts/test.sh --linting            # Include linting checks
./scripts/test.sh --typing             # Include type checking
./scripts/test.sh --all                # Full test suite
./scripts/test.sh --filter "pattern"   # Run specific tests
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
