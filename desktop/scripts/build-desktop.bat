@echo off
REM Build the complete Windows desktop installer.
REM Run from the repository root: desktop\scripts\build-desktop.bat

setlocal

set ROOT_DIR=%~dp0..\..
set DESKTOP_DIR=%ROOT_DIR%\desktop
set FRONTEND_DIR=%ROOT_DIR%\frontend
set TAURI_DIR=%DESKTOP_DIR%\src-tauri

echo === Building AI Econometrics Copilot Desktop ===
echo.

echo [1/5] Checking prerequisites...
rustc --version >nul 2>&1 || (echo ERROR: Rust is required. && exit /b 1)
node --version >nul 2>&1 || (echo ERROR: Node.js is required. && exit /b 1)
python --version >nul 2>&1 || (echo ERROR: Python is required. && exit /b 1)
echo   All prerequisites found.

echo [2/5] Packaging backend sidecar...
call "%DESKTOP_DIR%\scripts\package-backend.bat"
if errorlevel 1 exit /b 1

echo [3/5] Building static frontend...
cd /d "%FRONTEND_DIR%"
call npm ci --silent
set NEXT_PUBLIC_BUILD_TARGET=desktop
call npm run build:static
if not exist "out" (
    echo ERROR: Frontend static export failed.
    exit /b 1
)
echo   Frontend exported to out/.

echo [4/5] Building Tauri installer...
cd /d "%TAURI_DIR%"
cargo tauri build
if errorlevel 1 (
    echo ERROR: Tauri build failed.
    exit /b 1
)

echo.
echo [5/5] Build complete.
echo.
echo Check %TAURI_DIR%\target\release\bundle\ for installer files.

cd /d "%ROOT_DIR%"
