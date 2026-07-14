# AI Econometrics Copilot — Installer Downloader

A lightweight PowerShell script that downloads the latest Windows installer
from GitHub Releases, verifies its SHA-256 checksum, and launches it.

## For end users

Open PowerShell and run:

```powershell
irm https://raw.githubusercontent.com/uudam42/AI-Econometrics-Copilot/main/installer_downloader/downloader.ps1 | iex
```

Or download `downloader.ps1`, right-click → **Run with PowerShell**.

No Git, Docker, Python, Node.js, or Rust is required.

## What it does

1. Checks the latest GitHub Release for `uudam42/AI-Econometrics-Copilot`
2. Downloads the Windows installer (`.msi` or Setup `.exe`)
3. Verifies the SHA-256 checksum (if `SHA256SUMS.txt` is attached to the release)
4. Launches the installer

## Error messages

| Message | Meaning |
|---|---|
| Could not reach GitHub Releases | No internet or GitHub is down |
| No Windows installer asset was found | The release doesn't include a Windows build |
| Checksum verification FAILED | Downloaded file is corrupted — retry |
| Could not launch installer | Windows blocked execution — run manually |

## Prerequisites

- Windows 10/11
- PowerShell 5.1+ (built into Windows)
- Internet connection
