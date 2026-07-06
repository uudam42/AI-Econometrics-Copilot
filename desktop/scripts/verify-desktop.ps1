# Verify desktop build prerequisites and outputs.
# Run from the repository root: powershell desktop\scripts\verify-desktop.ps1

$ErrorActionPreference = "SilentlyContinue"
$RootDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))

Write-Host "=== Desktop Build Verification ===" -ForegroundColor Cyan
Write-Host ""

$pass = 0
$fail = 0

function Check($label, $condition) {
    if ($condition) {
        Write-Host "  PASS  $label" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "  FAIL  $label" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "Prerequisites:" -ForegroundColor Yellow
Check "Rust installed" ((rustc --version 2>$null) -ne $null)
Check "Cargo installed" ((cargo --version 2>$null) -ne $null)
Check "Node.js installed" ((node --version 2>$null) -ne $null)
Check "npm installed" ((npm --version 2>$null) -ne $null)
Check "Python installed" ((python --version 2>$null) -ne $null)

Write-Host ""
Write-Host "Project structure:" -ForegroundColor Yellow
Check "Tauri config exists" (Test-Path "$RootDir\desktop\src-tauri\tauri.conf.json")
Check "Cargo.toml exists" (Test-Path "$RootDir\desktop\src-tauri\Cargo.toml")
Check "Rust source exists" (Test-Path "$RootDir\desktop\src-tauri\src\main.rs")
Check "PyInstaller spec exists" (Test-Path "$RootDir\backend\ai-econometrics-backend.spec")
Check "Frontend package.json" (Test-Path "$RootDir\frontend\package.json")
Check "Sample data exists" (Test-Path "$RootDir\sample_data\world_bank_panel_sample.xlsx")

Write-Host ""
Write-Host "Build artifacts:" -ForegroundColor Yellow
Check "Backend sidecar built" (Test-Path "$RootDir\desktop\src-tauri\binaries\ai-econometrics-backend.exe")
Check "Frontend static export" (Test-Path "$RootDir\frontend\out\index.html")
$bundleDir = "$RootDir\desktop\src-tauri\target\release\bundle"
$msi = Get-ChildItem "$bundleDir\msi\*.msi" -ErrorAction SilentlyContinue
$nsis = Get-ChildItem "$bundleDir\nsis\*.exe" -ErrorAction SilentlyContinue
Check "MSI installer exists" ($msi -ne $null)
Check "NSIS installer exists" ($nsis -ne $null)

Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host "Results: $pass passed, $fail failed" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Yellow" })
