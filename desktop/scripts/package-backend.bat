@echo off
REM Package the FastAPI backend as a standalone Windows executable.
REM Run from the repository root: desktop\scripts\package-backend.bat

setlocal

set ROOT_DIR=%~dp0..\..
set BACKEND_DIR=%ROOT_DIR%\backend
set OUTPUT_DIR=%ROOT_DIR%\desktop\src-tauri\binaries

echo === Packaging FastAPI Backend Sidecar ===

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is required for backend packaging.
    exit /b 1
)

cd /d "%BACKEND_DIR%"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
pip install -q pyinstaller

echo Building backend executable...
pyinstaller ai-econometrics-backend.spec --distpath "%OUTPUT_DIR%" --workpath "%BACKEND_DIR%\build" -y

if not exist "%OUTPUT_DIR%\ai-econometrics-backend.exe" (
    echo ERROR: Backend executable not found.
    exit /b 1
)

REM Rename with the Rust target triple - Tauri's externalBin resolves
REM sidecars as name-target-triple.exe at build time.
for /f "tokens=2" %%i in ('rustc --version --verbose ^| findstr "host:"') do set TRIPLE=%%i
move /y "%OUTPUT_DIR%\ai-econometrics-backend.exe" "%OUTPUT_DIR%\ai-econometrics-backend-%TRIPLE%.exe" >nul
echo SUCCESS: Backend sidecar built as ai-econometrics-backend-%TRIPLE%.exe

cd /d "%ROOT_DIR%"
