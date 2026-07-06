# AI Econometrics Copilot — Local Startup Script (Windows PowerShell)
# Usage: powershell -ExecutionPolicy Bypass -File scripts\start-local.ps1

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$BackendDir = Join-Path $RootDir "backend"
$FrontendDir = Join-Path $RootDir "frontend"
$LogDir = Join-Path $RootDir "logs"

function Write-Info($msg)  { Write-Host "[INFO] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg)   { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# --- Dependency checks ---
Write-Host ""
Write-Host "AI Econometrics Copilot - Local Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$py = $null
foreach ($cmd in @("python", "python3")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $py = $cmd
                Write-Info "Python: $ver"
                break
            }
        }
    } catch {}
}
if (-not $py) {
    Write-Err "Python 3.10+ is required. Download from https://www.python.org/downloads/"
    exit 1
}

try {
    $nodeVer = node --version 2>&1
    $nodeMajor = [int]($nodeVer -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -lt 18) { throw "too old" }
    Write-Info "Node.js: $nodeVer"
} catch {
    Write-Err "Node.js 18+ is required. Download from https://nodejs.org/"
    exit 1
}

# --- Backend setup ---
Set-Location $BackendDir

if (-not (Test-Path ".venv")) {
    Write-Info "Creating Python virtual environment..."
    & $py -m venv .venv
}

$activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
. $activateScript

$depsMarker = Join-Path ".venv" ".deps_installed"
if (-not (Test-Path $depsMarker) -or (Get-Item "requirements.txt").LastWriteTime -gt (Get-Item $depsMarker -ErrorAction SilentlyContinue).LastWriteTime) {
    Write-Info "Installing backend dependencies..."
    pip install -q -r requirements.txt
    New-Item -Path $depsMarker -ItemType File -Force | Out-Null
} else {
    Write-Info "Backend dependencies up to date."
}

New-Item -Path "data/uploads" -ItemType Directory -Force | Out-Null
New-Item -Path "data/artifacts" -ItemType Directory -Force | Out-Null

# --- Frontend setup ---
Set-Location $FrontendDir

if (-not (Test-Path "node_modules")) {
    Write-Info "Installing frontend dependencies..."
    npm install --silent
} else {
    Write-Info "Frontend dependencies up to date."
}

# --- Launch ---
New-Item -Path $LogDir -ItemType Directory -Force | Out-Null

Set-Location $BackendDir
. $activateScript

Write-Info "Starting backend on http://localhost:8000 ..."
$backendJob = Start-Job -ScriptBlock {
    param($dir, $log)
    Set-Location $dir
    $activate = Join-Path ".venv" "Scripts" "Activate.ps1"
    . $activate
    uvicorn app.main:app --host 127.0.0.1 --port 8000 *> $log
} -ArgumentList $BackendDir, (Join-Path $LogDir "backend.log")

Set-Location $FrontendDir
Write-Info "Starting frontend on http://localhost:3000 ..."
$frontendJob = Start-Job -ScriptBlock {
    param($dir, $log)
    Set-Location $dir
    npm run dev *> $log
} -ArgumentList $FrontendDir, (Join-Path $LogDir "frontend.log")

Write-Info "Waiting for backend..."
for ($i = 0; $i -lt 30; $i++) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
        Write-Info "Backend is ready."
        break
    } catch {
        Start-Sleep 1
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  AI Econometrics Copilot is running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:   http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API docs:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Logs:      $LogDir\" -ForegroundColor Gray
Write-Host "  Stop:      powershell scripts\stop-local.ps1" -ForegroundColor Yellow
Write-Host ""

Start-Process "http://localhost:3000"

Write-Host "Press Ctrl+C to stop..." -ForegroundColor Gray
try {
    while ($true) { Start-Sleep 5 }
} finally {
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -Force -ErrorAction SilentlyContinue
}
