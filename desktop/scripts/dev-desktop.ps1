# Run the desktop application in development mode.
# Starts the Next.js dev server and Tauri dev window.
# Run from the repository root: powershell desktop\scripts\dev-desktop.ps1

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$TauriDir = Join-Path $RootDir "desktop" "src-tauri"
$BackendDir = Join-Path $RootDir "backend"

Write-Host "=== Desktop Development Mode ===" -ForegroundColor Cyan

# Start backend manually for dev mode
Write-Host "Starting backend on port 8000..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        . .venv\Scripts\Activate.ps1
    }
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $BackendDir

Start-Sleep 3

# Start Tauri dev mode (this will also start the Next.js dev server)
Write-Host "Starting Tauri dev mode..." -ForegroundColor Yellow
Set-Location $TauriDir
cargo tauri dev

# Cleanup
Stop-Job $backendJob -ErrorAction SilentlyContinue
Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
Write-Host "Dev mode stopped." -ForegroundColor Green
