# Package the FastAPI backend as a standalone Windows executable using PyInstaller.
# Run from the repository root: powershell desktop\scripts\package-backend.ps1

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$BackendDir = Join-Path $RootDir "backend"
$DesktopDir = Join-Path $RootDir "desktop"
$OutputDir = Join-Path $DesktopDir "src-tauri" "binaries"

Write-Host "=== Packaging FastAPI Backend Sidecar ===" -ForegroundColor Cyan

# Check Python
try {
    $pyVer = python --version 2>&1
    Write-Host "Python: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is required for backend packaging." -ForegroundColor Red
    exit 1
}

# Install PyInstaller if needed
pip show pyinstaller > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing PyInstaller..."
    pip install pyinstaller
}

# Install backend dependencies
Set-Location $BackendDir
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}
. .venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
pip install -q pyinstaller

# Build
Write-Host "Building backend executable..." -ForegroundColor Yellow
pyinstaller ai-econometrics-backend.spec --distpath "$OutputDir" --workpath "$BackendDir\build" -y

# Verify
$ExeName = Join-Path $OutputDir "ai-econometrics-backend.exe"
if (Test-Path $ExeName) {
    $size = (Get-Item $ExeName).Length / 1MB
    Write-Host "SUCCESS: $ExeName ({0:N1} MB)" -f $size -ForegroundColor Green
} else {
    Write-Host "ERROR: Backend executable not found at $ExeName" -ForegroundColor Red
    exit 1
}

Set-Location $RootDir
