param(
    [switch]$Executable,
    [switch]$WheelOnly,
    [switch]$Clean
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "Building CAN_ID_Reframe..." -ForegroundColor Green

# Clean previous builds if requested
if ($Clean) {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "CAN_ID_Reframe.egg-info") { Remove-Item -Recurse -Force "CAN_ID_Reframe.egg-info" }
}

# Install build dependencies if not present
Write-Host "Checking build dependencies..." -ForegroundColor Blue
py -m pip install --upgrade build wheel

# Build wheel and source distribution
if ($WheelOnly) {
    Write-Host "Building wheel only..." -ForegroundColor Blue
    py -m build --wheel
} else {
    Write-Host "Building wheel and source distribution..." -ForegroundColor Blue
    py -m build
}

# Build standalone executable if requested
if ($Executable) {
    Write-Host "Building standalone executable..." -ForegroundColor Blue
    
    # Install PyInstaller if not present
    py -m pip install --upgrade pyinstaller
    # Ensure project and its dependencies are installed (so hidden/optional deps are present)
    py -m pip install -e .
    
    # Get version from version_info.txt
    $version = Get-Content "core\version_info.txt" -Raw | ForEach-Object { $_.Trim() }
    Write-Host "Building executable for version: $version" -ForegroundColor Cyan
    
    # Build executable using spec file
    py -m PyInstaller can-id-reframe.spec --clean --noconfirm
    
    $executableName = "can-id-reframe-$version.exe"
    if (Test-Path "dist\$executableName") {
        Write-Host "Executable built successfully: dist\$executableName" -ForegroundColor Green
    } else {
        Write-Host "Failed to build executable: dist\$executableName" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "Artifacts in: $(Resolve-Path 'dist')" -ForegroundColor Cyan
