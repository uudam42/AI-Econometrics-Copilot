# Build the complete Windows desktop installer.
# Prerequisites: Rust, Node.js, Python (for backend packaging).
# Run from the repository root: powershell desktop\scripts\build-desktop.ps1

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$DesktopDir = Join-Path $RootDir "desktop"
$FrontendDir = Join-Path $RootDir "frontend"
$TauriDir = Join-Path $DesktopDir "src-tauri"

Write-Host "=== Building AI Econometrics Copilot Desktop ===" -ForegroundColor Cyan
Write-Host ""

# --- Check prerequisites ---
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

foreach ($cmd in @("rustc", "cargo", "node", "npm", "python")) {
    try { & $cmd --version > $null 2>&1 } catch {
        Write-Host "ERROR: $cmd is required but not found." -ForegroundColor Red
        exit 1
    }
}
Write-Host "  All prerequisites found." -ForegroundColor Green

# --- Package backend sidecar ---
Write-Host "[2/5] Packaging backend sidecar..." -ForegroundColor Yellow
& (Join-Path $DesktopDir "scripts" "package-backend.ps1")

# --- Build static frontend ---
Write-Host "[3/5] Building static frontend..." -ForegroundColor Yellow
Set-Location $FrontendDir
npm ci --silent
$env:NEXT_PUBLIC_BUILD_TARGET = "desktop"
npm run build:static

if (-not (Test-Path "out")) {
    Write-Host "ERROR: Frontend static export failed — out/ directory not found." -ForegroundColor Red
    exit 1
}
Write-Host "  Frontend exported to out/." -ForegroundColor Green

# --- Build Tauri installer ---
Write-Host "[4/5] Building Tauri installer..." -ForegroundColor Yellow
Set-Location $TauriDir
cargo tauri build

# --- Report output ---
Write-Host ""
Write-Host "[5/5] Build complete." -ForegroundColor Green
Write-Host ""

$bundleDir = Join-Path $TauriDir "target" "release" "bundle"
if (Test-Path $bundleDir) {
    Write-Host "Installer output:" -ForegroundColor Cyan
    Get-ChildItem $bundleDir -Recurse -Include "*.msi","*.exe" | ForEach-Object {
        $size = $_.Length / 1MB
        Write-Host "  $($_.FullName) ({0:N1} MB)" -f $size
    }
} else {
    Write-Host "WARNING: Bundle directory not found. Check build output above." -ForegroundColor Yellow
}

Set-Location $RootDir
