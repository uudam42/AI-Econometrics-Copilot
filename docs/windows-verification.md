# Windows Verification Guide

[中文版](windows-verification.zh-CN.md)

Use this guide to verify that AI Econometrics Copilot is working correctly after installation, or to diagnose a startup failure.

---

## Quick verification checklist

After launching the application, verify each of the following:

- [ ] The startup screen appears with a progress indicator
- [ ] The progress indicator advances through all four stages
- [ ] The main application loads within 15 seconds
- [ ] The home page shows "AI Econometrics Copilot" and three action cards
- [ ] Clicking "Analyse My Excel" navigates to the Quick Analyze page
- [ ] File upload works (try `sample_data/world_bank_panel_sample.xlsx`)

If any item fails, follow the relevant diagnostic section below.

---

## Startup stages

The application displays four startup stages. Each stage should complete within a few seconds:

| Stage | Indicator text | What happens |
|-------|---------------|--------------|
| 1 | Preparing local workspace… | Creates data directories |
| 2 | Starting analysis engine… | Launches the backend sidecar |
| 3 | Loading research tools… | Waits for the backend health endpoint |
| 4 | Ready | Frontend loads |

If the application shows **Could not start**, the startup failed. See the [Recovery section](#recovery-from-startup-failure) below.

---

## Verify backend health manually

Open PowerShell and run:

```powershell
# Find the port used by the backend
$proc = Get-Process "ai-econometrics-backend" -ErrorAction SilentlyContinue
if ($proc) {
    Write-Host "Backend process is running (PID: $($proc.Id))"
} else {
    Write-Host "Backend process not found"
}
```

If the backend is running but the app still fails, check the log file:

```powershell
$logPath = "$env:LOCALAPPDATA\AI Econometrics Copilot\logs\backend.log"
if (Test-Path $logPath) {
    Get-Content $logPath -Tail 50
} else {
    Write-Host "Log file not found: $logPath"
}
```

---

## Verify file structure

After first launch, the following directories should exist:

```powershell
$base = "$env:LOCALAPPDATA\AI Econometrics Copilot"
foreach ($sub in @("database", "uploads", "artifacts", "exports", "logs", "config")) {
    $path = Join-Path $base $sub
    if (Test-Path $path) {
        Write-Host "[OK] $path"
    } else {
        Write-Host "[MISSING] $path"
    }
}
```

All six subdirectories should show `[OK]`. Missing directories may indicate a permissions problem.

---

## Verify WebView2

```powershell
$webview2 = Get-ItemProperty `
  "HKLM:\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" `
  -ErrorAction SilentlyContinue
if ($webview2) {
    Write-Host "WebView2 version: $($webview2.pv)"
} else {
    Write-Host "WebView2 not found — install from https://developer.microsoft.com/microsoft-edge/webview2/"
}
```

---

## Test Quick Analyze end-to-end

1. Launch the application
2. On the home page, click **Analyse My Excel**
3. Click **Choose file** and select `sample_data/world_bank_panel_sample.xlsx`
4. Leave the research question blank and click **Upload & Analyse**
5. Wait for the planning stage to complete (a few seconds)
6. Review the proposed plan and click **Confirm & Run Analysis**
7. Verify that results appear, including the plain-English summary and diagnostic table

If any step fails, note which stage and consult the [Troubleshooting section](#troubleshooting).

---

## Recovery from startup failure

When the application shows the red "Could not start" panel:

### 1. Read the error message

The error message under "Could not start" describes what went wrong.

### 2. Copy technical details

Click **Copy Technical Details** to copy a JSON diagnostic payload to the clipboard. Paste it into a text editor or bug report.

### 3. Check the logs

Click **Open Logs Folder** to open `%LOCALAPPDATA%\AI Econometrics Copilot\logs\` in File Explorer. Open `backend.log` and look for error messages near the end of the file.

### 4. Common startup failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "Could not start the analysis engine" | Sidecar binary not found | Reinstall the application |
| "The analysis engine did not respond in time" | Port conflict or slow machine | Retry; if persistent, restart the machine |
| App crashes immediately | WebView2 missing | Install WebView2 (see [Installation guide](windows-installation.md)) |
| Blank white screen | Frontend export missing | Reinstall the application |

### 5. Reset local data

If the database is corrupted:
1. Navigate to `%LOCALAPPDATA%\AI Econometrics Copilot\`
2. Delete the `database\` folder
3. Restart the application (the database will be recreated)

Or use the **Open Data Folder** button on the recovery panel to navigate there directly.

### 6. Retry

Click **Retry** to reload the application without closing and reopening it.

### 7. Close and reopen

Click **Close Application** to shut down cleanly, then reopen from the Start Menu.

---

## Troubleshooting

**Application window is blank / white**
- Reinstall the application (the frontend static files may be missing)
- Check that WebView2 is installed and up to date

**Application opens but shows "Connection refused" errors**
- The backend failed to start; check `backend.log`
- Try restarting the application

**File upload fails with "Network error"**
- The backend may have crashed after starting; check `backend.log`
- Click **Retry** or restart the application

**Analysis results are empty**
- Check that the dataset has at least two numeric columns
- Try with `sample_data/world_bank_panel_sample.xlsx` to rule out a dataset issue

**Application is very slow**
- The backend cold-start can take up to 30 seconds on older machines
- Give the startup screen more time before concluding it has failed

---

## Reporting a bug

Include the following in your bug report:

1. Windows version (`winver` output)
2. The technical details JSON from **Copy Technical Details**
3. The last 50 lines of `%LOCALAPPDATA%\AI Econometrics Copilot\logs\backend.log`
4. Steps to reproduce the issue

Open an issue at: **https://github.com/uudam42/ai-econometrics-copilot/issues**
