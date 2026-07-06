@echo off
REM Run the desktop application in development mode.
REM Run from the repository root: desktop\scripts\dev-desktop.bat

setlocal

set ROOT_DIR=%~dp0..\..
set TAURI_DIR=%ROOT_DIR%\desktop\src-tauri
set BACKEND_DIR=%ROOT_DIR%\backend

echo === Desktop Development Mode ===

echo Starting backend on port 8000...
start /b cmd /c "cd /d %BACKEND_DIR% && .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo Starting Tauri dev mode...
cd /d "%TAURI_DIR%"
cargo tauri dev

cd /d "%ROOT_DIR%"
