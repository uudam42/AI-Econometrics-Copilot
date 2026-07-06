# Desktop Application Build Guide

This directory contains the Tauri 2.x desktop shell and build scripts for packaging AI Econometrics Copilot as a standalone Windows application.

## Architecture

```
AI Econometrics Copilot.exe (Tauri)
├── Static Next.js frontend (frontend/out/)
├── Rust Tauri host (desktop/src-tauri/)
├── FastAPI backend sidecar (ai-econometrics-backend.exe)
└── Local user data (%LOCALAPPDATA%\AI Econometrics Copilot\)
    ├── database/   — SQLite database
    ├── uploads/    — uploaded datasets
    ├── artifacts/  — generated analysis artifacts
    ├── exports/    — DOCX, LaTeX, Markdown exports
    ├── logs/       — application logs
    └── config/     — user configuration
```

## Prerequisites (Developer)

- **Rust** — `rustup default stable`
- **Node.js 18+** — for frontend build
- **Python 3.10+** — for backend sidecar packaging
- **PyInstaller** — `pip install pyinstaller`
- **Tauri CLI** — `cargo install tauri-cli`

End users do not need any of these installed.

## Build Steps

### 1. Package Backend Sidecar

```powershell
.\desktop\scripts\package-backend.ps1
# or
desktop\scripts\package-backend.bat
```

This creates `desktop/src-tauri/binaries/ai-econometrics-backend-<target-triple>.exe`
(e.g. `ai-econometrics-backend-x86_64-pc-windows-msvc.exe`) — Tauri's `externalBin`
resolves sidecars by target triple at build time and bundles them next to the
main executable with the suffix stripped.

### 2. Build Desktop Installer

```powershell
.\desktop\scripts\build-desktop.ps1
# or
desktop\scripts\build-desktop.bat
```

This runs the full pipeline:
1. Packages the backend sidecar (PyInstaller)
2. Builds the static frontend (`npm run build:static`)
3. Builds the Tauri installer (`cargo tauri build`)

Output: `desktop/src-tauri/target/release/bundle/msi/` and `nsis/`

### 3. Development Mode

```powershell
.\desktop\scripts\dev-desktop.ps1
# or
desktop\scripts\dev-desktop.bat
```

Starts the backend in dev mode and opens a Tauri dev window with hot-reload.

### 4. Verify Build

```powershell
.\desktop\scripts\verify-desktop.ps1
```

Checks prerequisites, project structure, and build artifacts.

## For End Users

1. Download the installer (`.msi` or `Setup.exe`)
2. Run the installer
3. Open **AI Econometrics Copilot** from the Start Menu
4. All data stays on the local computer
5. No Docker, Python, Node.js, or browser required

## Notes

- **Windows only** — macOS and Linux desktop packages are not yet built
- **Unsigned build** — Windows SmartScreen may show a warning for unsigned builds
- **No auto-update** — updates require downloading a new installer
- **No cloud sync** — all data is local to the machine
