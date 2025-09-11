#!/usr/bin/env bash
set -euo pipefail

# Parse command line arguments
EXECUTABLE=false
WHEEL_ONLY=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --executable)
            EXECUTABLE=true
            shift
            ;;
        --wheel-only)
            WHEEL_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--executable] [--wheel-only] [--clean]"
            exit 1
            ;;
    esac
done

echo "🔨 Building CAN_ID_Reframe..."

# Clean previous builds if requested
if [[ "$CLEAN" == true ]]; then
    echo "🧹 Cleaning previous builds..."
    rm -rf dist/ build/ CAN_ID_Reframe.egg-info/
fi

# Install build dependencies if not present
echo "📦 Checking build dependencies..."
python -m pip install --upgrade build wheel

# Build wheel and source distribution
if [[ "$WHEEL_ONLY" == true ]]; then
    echo "🎯 Building wheel only..."
    python -m build --wheel
else
    echo "📦 Building wheel and source distribution..."
    python -m build
fi

# Build standalone executable if requested
if [[ "$EXECUTABLE" == true ]]; then
    echo "🚀 Building standalone executable..."
    
    # Install PyInstaller if not present
    python -m pip install --upgrade pyinstaller
    
    # Build executable using spec file
    pyinstaller can-id-reframe.spec --clean --noconfirm
    
    if [[ -f "dist/can-id-reframe" ]]; then
        echo "✅ Executable built successfully: dist/can-id-reframe"
    else
        echo "❌ Failed to build executable"
        exit 1
    fi
fi

echo "✅ Build completed successfully!"
echo "📁 Artifacts in: $(realpath dist)"
