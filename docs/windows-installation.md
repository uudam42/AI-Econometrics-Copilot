# Windows Installation Guide

[中文版](windows-installation.zh-CN.md)

This guide covers installing AI Econometrics Copilot Desktop Edition on Windows 10 and Windows 11.

---

## System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10 (64-bit, version 1903+) | Windows 11 |
| RAM | 4 GB | 8 GB |
| Disk space | 500 MB free | 2 GB free |
| WebView2 | Required | Required |
| Internet | Not required after install | Not required |

---

## Step 1 — Check WebView2

AI Econometrics Copilot requires the **Microsoft Edge WebView2 Runtime**.

- **Windows 11**: WebView2 is already installed.
- **Windows 10**: You may need to install it manually.

To check if WebView2 is installed:
1. Open **Settings → Apps → Installed apps**
2. Search for "WebView2"
3. If "Microsoft Edge WebView2 Runtime" appears, you are ready to proceed

If WebView2 is not installed, download it from:
**https://developer.microsoft.com/en-us/microsoft-edge/webview2/**

Select **Evergreen Standalone Installer (x64)**, download, and run it.

---

## Step 2 — Download the installer

Download the latest release from the GitHub Releases page:

**https://github.com/uudam42/ai-econometrics-copilot/releases/latest**

Two installer formats are available:

| File | Format | Use |
|------|--------|-----|
| `AI.Econometrics.Copilot_x.x.x_x64_en-US.msi` | MSI | Enterprise / IT deployment |
| `AI.Econometrics.Copilot_x.x.x_x64-setup.exe` | NSIS | Personal / home use |

Download the `.exe` installer unless you need MSI for enterprise deployment.

Verify the SHA256 checksum against the `checksums.sha256` file published alongside the installer:

```powershell
(Get-FileHash "AI.Econometrics.Copilot_x.x.x_x64-setup.exe" -Algorithm SHA256).Hash.ToLower()
# Compare the output to the value in checksums.sha256
```

---

## Step 3 — Run the installer

### NSIS installer (Setup.exe)

1. Double-click the downloaded `*-setup.exe`
2. If Windows SmartScreen shows a warning, click **More info → Run anyway**
   (The installer is unsigned in this release.)
3. Follow the installation wizard
4. The application is installed to `C:\Users\<username>\AppData\Local\AI Econometrics Copilot\`

### MSI installer

```powershell
msiexec /i "AI.Econometrics.Copilot_x.x.x_x64_en-US.msi" /qn
```

Or double-click the `.msi` file and follow the wizard.

---

## Step 4 — Launch the application

After installation, launch AI Econometrics Copilot from:
- **Start Menu → AI Econometrics Copilot**
- **Desktop shortcut** (if created during installation)

The application will show a startup screen while the backend analysis engine initialises (typically 3–8 seconds on first launch).

---

## What gets installed

| Component | Location |
|-----------|---------|
| Application files | `%LOCALAPPDATA%\AI Econometrics Copilot\` |
| Start Menu shortcut | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\` |
| User data | `%LOCALAPPDATA%\AI Econometrics Copilot\` (created on first run) |

The installer does **not** modify system-wide settings, registry entries outside the user hive, or install any services.

---

## Uninstalling

**Via Settings:**
1. Open **Settings → Apps → Installed apps**
2. Search for "AI Econometrics Copilot"
3. Click **Uninstall**

**Via Control Panel:**
1. Open **Control Panel → Programs → Uninstall a program**
2. Select **AI Econometrics Copilot**
3. Click **Uninstall**

User data (database, uploads, exports) in `%LOCALAPPDATA%\AI Econometrics Copilot\` is **not** removed by the uninstaller. Delete this folder manually if you want to remove all data.

---

## Firewall and network

The application binds a local HTTP server on a random port (`127.0.0.1` only). No inbound or outbound internet connections are made. If your firewall prompts for permission, **deny** external access — the local port is only used for IPC between the Tauri shell and the backend.

---

## Antivirus and SmartScreen

Because the installer is currently unsigned, Windows SmartScreen and some antivirus products may flag it. This is expected behaviour for unsigned executables. You can verify the integrity using the SHA256 checksum (Step 2) before running.

If your antivirus quarantines the installer:
1. Verify the SHA256 checksum matches the published value
2. Add an exception for the installer and application directory

---

## Troubleshooting installation

**"Windows protected your PC" (SmartScreen)**
Click **More info → Run anyway**. This appears because the installer is currently unsigned.

**"This app can't run on your PC"**
Ensure you downloaded the `x64` installer and that your Windows is 64-bit.

**Application fails to start after installation**
Check that WebView2 is installed (Step 1). See [Windows Verification](windows-verification.md) for diagnostics.

**Installation hangs or fails**
Try running the installer as Administrator: right-click the installer → **Run as administrator**.
