param(
    [switch]$Coverage,
    [switch]$Verbose,
    [switch]$FastFail,
    [string]$Filter = "",
    [switch]$Linting,
    [switch]$Typing,
    [switch]$All
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Running CAN_ID_Reframe tests..." -ForegroundColor Green

# Install test dependencies if not present
Write-Host "Installing test dependencies..." -ForegroundColor Blue
py -m pip install --upgrade pytest pytest-cov

# Build pytest command
$pytestArgs = @()

if ($Coverage -or $All) {
    Write-Host "Running tests with coverage..." -ForegroundColor Blue
    $pytestArgs += "--cov=core"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=html"
}

if ($Verbose) {
    $pytestArgs += "-v"
} else {
    $pytestArgs += "-q"
}

if ($FastFail) {
    $pytestArgs += "-x"
}

if ($Filter) {
    $pytestArgs += "-k"
    $pytestArgs += $Filter
}

# Run tests
Write-Host "Running pytest..." -ForegroundColor Blue
& py -m pytest @pytestArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Run linting if requested
if ($Linting -or $All) {
    Write-Host "Running linting checks..." -ForegroundColor Blue
    
    # Install linting dependencies
    py -m pip install --upgrade ruff
    
    Write-Host "  Running ruff linter..." -ForegroundColor Cyan
    py -m ruff check .
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Linting failed" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Run type checking if requested
if ($Typing -or $All) {
    Write-Host "Running type checking..." -ForegroundColor Blue
    
    # Install mypy
    py -m pip install --upgrade mypy
    
    py -m mypy core/
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Type checking failed" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "All tests passed!" -ForegroundColor Green

if ($Coverage -or $All) {
    Write-Host "Coverage report generated in htmlcov/" -ForegroundColor Cyan
}
