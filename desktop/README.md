# AI Econometrics Copilot — Desktop Edition

Developer build guide for the Windows standalone desktop application built with [Tauri 2](https://tauri.app/).

---

## Architecture

```
AI Econometrics Copilot.exe  (Tauri shell)
├── Static Next.js frontend  (frontend/out/)       — bundled into the binary
├── Rust Tauri host          (desktop/src-tauri/)  — IPC, startup, menu
├── FastAPI backend sidecar  (ai-econometrics-backend.exe)  — auto-started
└── Local user data          (%LOCALAPPDATA%\AI Econometrics Copilot\)
    ├── database/   — SQLite database
    ├── uploads/    — uploaded datasets
    ├── artifacts/  — analysis artefacts
    ├── exports/    — DOCX, LaTeX, Markdown, PDF exports
    ├── logs/       — backend.log
    └── config/     — user configuration
```

---

## Prerequisites (Developer)

| Tool | Minimum version | Install |
|------|----------------|---------|
| Rust + Cargo | stable (≥ 1.78) | `rustup update stable` |
| Node.js | 20 LTS | [nodejs.org](https://nodejs.org) |
| Python | 3.11 or 3.12 | [python.org](https://www.python.org) |
| Git | any | [git-scm.com](https://git-scm.com) |
| Tauri CLI | 2.x | `npm install -g @tauri-apps/cli@^2` |

On Windows, also install the [WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) (bundled with Windows 11; requires a one-time install on Windows 10).

End users do not need any of these installed.

---

## Repository layout

```
ai-econometrics-copilot/
├── backend/                     # FastAPI Python backend (sidecar source)
│   ├── ai-econometrics-backend.spec   # PyInstaller spec
│   └── app/
├── frontend/                    # Next.js static-export frontend
│   ├── app/
│   ├── components/
│   └── lib/
├── desktop/
│   ├── scripts/                 # PowerShell and batch helpers
│   └── src-tauri/
│       ├── src/
│       │   ├── lib.rs           # Tauri commands and app entry
│       │   ├── menu.rs          # Native app menu builder
│       │   └── sidecar.rs       # Backend lifecycle helpers
│       ├── tauri.conf.json      # Tauri configuration
│       └── Cargo.toml
└── sample_data/                 # Sample dataset for demo
```

---

## Step 1 — Clone and install dependencies

```bash
git clone https://github.com/uudam42/ai-econometrics-copilot.git
cd ai-econometrics-copilot

# Install frontend npm packages
cd frontend && npm install && cd ..
```

---

## Step 2 — Package the Python sidecar

The backend runs as an embedded executable (sidecar). PyInstaller bundles it with all Python dependencies included.

```bash
cd backend
python -m venv .venv

# Windows (Command Prompt / PowerShell)
.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

pyinstaller ai-econometrics-backend.spec ^
  --distpath ..\desktop\src-tauri\binaries ^
  --workpath build -y
```

After packaging, rename the binary with the Rust target triple (required by Tauri's `externalBin`):

```powershell
$triple = (rustc --version --verbose | Select-String "host:").ToString().Split(" ")[1]
Rename-Item `
  "desktop\src-tauri\binaries\ai-econometrics-backend.exe" `
  "desktop\src-tauri\binaries\ai-econometrics-backend-$triple.exe"
```

Verify the sidecar is in place:
```powershell
Get-ChildItem desktop\src-tauri\binaries\ai-econometrics-backend-*.exe
# Expected: ai-econometrics-backend-x86_64-pc-windows-msvc.exe
```

Or use the helper script:
```powershell
.\desktop\scripts\package-backend.ps1
```

---

## Step 3 — Build the static frontend

```bash
cd frontend
npm run build:static
```

The `build:static` script sets `NEXT_PUBLIC_BUILD_TARGET=desktop` which enables Tauri-specific code paths (native file picker, IPC commands). Output is written to `frontend/out/`.

Verify:
```powershell
Test-Path frontend\out\index.html   # must return True
```

---

## Step 4 — Build the Tauri installer

```powershell
cd desktop\src-tauri
tauri build
```

Artifacts are written to `desktop/src-tauri/target/release/bundle/`:

| Format | Path | Use |
|--------|------|-----|
| MSI installer | `bundle/msi/*.msi` | Recommended for enterprise deployment |
| NSIS installer | `bundle/nsis/*.exe` | Recommended for end users |

Or use the all-in-one helper:
```powershell
.\desktop\scripts\build-desktop.ps1
```

---

## Step 5 — Run in development mode

Development mode uses the Next.js dev server (hot-reload) with the Tauri shell. You still need the sidecar binary from Step 2.

```powershell
# From the repo root:
.\desktop\scripts\dev-desktop.ps1
```

Or manually:
```powershell
# Terminal 1 — frontend dev server (auto-started by Tauri's beforeDevCommand)
# Terminal 2 — Tauri dev window
cd desktop\src-tauri
tauri dev
```

---

## Step 6 — Run Rust unit tests

```bash
cd desktop/src-tauri
cargo test
```

Tests in `sidecar.rs` cover:
- `pick_port()` env-var override and numeric parsing
- Health endpoint URL format
- SQLite URL format
- Sidecar binary naming (platform-aware)
- `SUBDIRS` completeness
- `ensure_directories()` actually creates subdirectories

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_ECONOMETRICS_PORT` | auto (portpicker) | Override the backend port |
| `AI_ECONOMETRICS_DATA_DIR` | `%LOCALAPPDATA%\AI Econometrics Copilot` | Override the data root |

---

## Data locations (Windows)

| Artifact | Path |
|----------|------|
| Database | `%LOCALAPPDATA%\AI Econometrics Copilot\database\ai_econometrics.db` |
| Uploads | `%LOCALAPPDATA%\AI Econometrics Copilot\uploads\` |
| Exports | `%LOCALAPPDATA%\AI Econometrics Copilot\exports\` |
| Logs | `%LOCALAPPDATA%\AI Econometrics Copilot\logs\backend.log` |
| Config | `%LOCALAPPDATA%\AI Econometrics Copilot\config\` |

---

## Tauri IPC commands

| Command | Returns | Description |
|---------|---------|-------------|
| `get_backend_base_url` | `string` | Backend API base URL |
| `get_backend_info` | `BackendInfo` | Port, data dir, health status |
| `get_app_info` | `AppInfo` | Versions and directory paths |
| `get_startup_status` | `StartupStatus` | Current startup stage |
| `get_storage_usage` | `StorageUsage` | Byte counts per subdirectory |
| `reset_local_data` | `void` | Wipes uploads, artifacts, exports, database |
| `open_data_folder` | `void` | Opens data root in Explorer |
| `open_exports_folder` | `void` | Opens exports directory in Explorer |
| `open_logs_folder` | `void` | Opens logs directory in Explorer |
| `close_application` | `void` | Stops backend sidecar and exits |

---

## Startup sequence

The Tauri shell emits `startup_status` events during boot:

```
Starting → PreparingWorkspace → StartingEngine → LoadingTools → Ready
                                                              ↘ Failed
```

The frontend `AppShell` shows `DesktopStartupScreen` until the `startup_status` event fires with `status: "ready"`. On failure, a recovery panel is displayed with buttons to Retry, Open Logs, Open Data Folder, Copy Technical Details, and Close Application.

---

## Native app menu

| Menu | Items |
|------|-------|
| **File** | New Project · Analyse My Excel… · — · Open Data Folder · Open Exports Folder · Open Logs Folder · — · Exit |
| **Help** | Quick Start Guide · Troubleshooting (Open Logs) · — · About AI Econometrics Copilot |

Menu events for navigation are emitted as `menu_action` Tauri events and handled in `AppShell.tsx`.

---

## For end users

1. Download the installer (`.msi` for enterprise, `Setup.exe` for personal use)
2. Run the installer and follow the prompts
3. Open **AI Econometrics Copilot** from the Start Menu or Desktop shortcut
4. All data is stored locally — no internet connection required
5. No Docker, Python, Node.js, or web browser required

---

## Known limitations

- **Windows only** — macOS and Linux desktop packages are not built in this release.
- **No auto-update** — updates require downloading and running a new installer.
- **WebView2 required** — Windows 10 users must install the WebView2 Runtime manually if not already present.
- **Unsigned build** — Windows SmartScreen will warn on first launch; click "More info → Run anyway".
- **Single window** — only one application window is supported.
- **Backend cold start** — the FastAPI sidecar takes 3–8 seconds on first launch; the startup screen shows progress.
- **No cloud sync** — all data is local to the machine.
