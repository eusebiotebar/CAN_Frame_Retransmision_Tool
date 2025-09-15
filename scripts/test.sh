#!/usr/bin/env bash
set -euo pipefail

# Default values
COVERAGE=false
VERBOSE=false
FAST_FAIL=false
FILTER=""
LINTING=false
TYPING=false
ALL=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --fast-fail)
            FAST_FAIL=true
            shift
            ;;
        --filter)
            FILTER="$2"
            shift 2
            ;;
        --linting)
            LINTING=true
            shift
            ;;
        --typing)
            TYPING=true
            shift
            ;;
        --all)
            ALL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--coverage] [--verbose] [--fast-fail] [--filter PATTERN] [--linting] [--typing] [--all]"
            exit 1
            ;;
    esac
done

echo "🧪 Running CAN_ID_Reframe tests..."

# Install test dependencies if not present
echo "📦 Installing test dependencies..."
python -m pip install --upgrade pytest pytest-cov

# Build pytest command
pytest_args=()

if [[ "$COVERAGE" == true ]] || [[ "$ALL" == true ]]; then
    echo "📊 Running tests with coverage..."
    pytest_args+=(--cov=core --cov-report=term-missing --cov-report=html --cov-report=xml)
fi

if [[ "$VERBOSE" == true ]]; then
    pytest_args+=(-v)
else
    pytest_args+=(-q)
fi

if [[ "$FAST_FAIL" == true ]]; then
    pytest_args+=(-x)
fi

if [[ -n "$FILTER" ]]; then
    pytest_args+=(-k "$FILTER")
fi

# Run tests
echo "🏃 Running pytest..."
python -m pytest "${pytest_args[@]}"

# Run linting if requested
if [[ "$LINTING" == true ]] || [[ "$ALL" == true ]]; then
    echo "🧹 Running linting checks..."
    
    # Install linting dependencies
    python -m pip install --upgrade black ruff
    
    echo "  📝 Checking code formatting with black..."
    python -m black --check . || (echo 'Black formatting differences:' && python -m black --diff . && exit 1)
    
    echo "  🔍 Running ruff linter..."
    python -m ruff check .
fi

# Run type checking if requested
if [[ "$TYPING" == true ]] || [[ "$ALL" == true ]]; then
    echo "🔍 Running type checking..."
    
    # Install mypy
    python -m pip install --upgrade mypy
    
    python -m mypy core/ || echo "⚠️ Type checking found issues but continuing..."
fi

echo "✅ All tests passed!"

if [[ "$COVERAGE" == true ]] || [[ "$ALL" == true ]]; then
    echo "📊 Coverage report generated in htmlcov/"
fi
