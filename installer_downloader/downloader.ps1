<#
.SYNOPSIS
    AI Econometrics Copilot — Windows Installer Downloader

.DESCRIPTION
    Downloads the latest Windows installer from GitHub Releases, verifies
    the SHA-256 checksum, and launches the installer.

    No prerequisites required (Git, Docker, Python, Node.js are NOT needed).

.NOTES
    Repository: https://github.com/uudam42/AI-Econometrics-Copilot
#>

param(
    [string]$Repo = "uudam42/AI-Econometrics-Copilot",
    [string]$DownloadDir = "$env:TEMP\ai-econometrics-copilot-installer"
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "  >> $msg" -ForegroundColor Cyan
}

function Write-Ok($msg) {
    Write-Host "     $msg" -ForegroundColor Green
}

function Write-Fail($msg) {
    Write-Host "     $msg" -ForegroundColor Red
}

# ---------------------------------------------------------------------------
# 1. Find the latest release
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "  AI Econometrics Copilot — Installer Downloader" -ForegroundColor White
Write-Host "  ================================================" -ForegroundColor DarkGray

Write-Step "Checking latest release..."

try {
    $releaseUrl = "https://api.github.com/repos/$Repo/releases/latest"
    $release = Invoke-RestMethod -Uri $releaseUrl -Headers @{ "User-Agent" = "AECopilot-Downloader" }
    $tag = $release.tag_name
    Write-Ok "Found version $tag"
} catch {
    Write-Fail "Could not reach GitHub Releases."
    Write-Fail "Please check your internet connection and try again."
    Write-Fail "You can also download manually from: https://github.com/$Repo/releases"
    Read-Host "Press Enter to exit"
    exit 1
}

# ---------------------------------------------------------------------------
# 2. Find the installer asset (prefer .msi, fall back to .exe)
# ---------------------------------------------------------------------------
Write-Step "Looking for Windows installer..."

$installerAsset = $null
$checksumAsset = $null

foreach ($asset in $release.assets) {
    if ($asset.name -match "\.msi$") {
        $installerAsset = $asset
    }
    if ($asset.name -match "SHA256SUMS") {
        $checksumAsset = $asset
    }
}

if (-not $installerAsset) {
    foreach ($asset in $release.assets) {
        if ($asset.name -match "Setup.*\.exe$|Copilot.*\.exe$") {
            $installerAsset = $asset
            break
        }
    }
}

if (-not $installerAsset) {
    Write-Fail "No Windows installer asset was found in release $tag."
    Write-Fail "Available assets:"
    foreach ($asset in $release.assets) {
        Write-Fail "  - $($asset.name)"
    }
    Write-Fail ""
    Write-Fail "The release may not include a Windows build yet."
    Write-Fail "Check: https://github.com/$Repo/releases/tag/$tag"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Ok "Found: $($installerAsset.name) ($([math]::Round($installerAsset.size / 1MB, 1)) MB)"

# ---------------------------------------------------------------------------
# 3. Download
# ---------------------------------------------------------------------------
Write-Step "Downloading installer..."

if (-not (Test-Path $DownloadDir)) {
    New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null
}

$installerPath = Join-Path $DownloadDir $installerAsset.name

try {
    $ProgressPreference = "SilentlyContinue"
    Invoke-WebRequest -Uri $installerAsset.browser_download_url -OutFile $installerPath
    $ProgressPreference = "Continue"
    Write-Ok "Downloaded to $installerPath"
} catch {
    Write-Fail "Download failed: $_"
    Read-Host "Press Enter to exit"
    exit 1
}

# ---------------------------------------------------------------------------
# 4. Verify checksum (if available)
# ---------------------------------------------------------------------------
if ($checksumAsset) {
    Write-Step "Verifying checksum..."
    try {
        $checksumPath = Join-Path $DownloadDir "SHA256SUMS.txt"
        $ProgressPreference = "SilentlyContinue"
        Invoke-WebRequest -Uri $checksumAsset.browser_download_url -OutFile $checksumPath
        $ProgressPreference = "Continue"

        $expectedLine = Get-Content $checksumPath | Where-Object { $_ -match [regex]::Escape($installerAsset.name) }
        if ($expectedLine) {
            $expectedHash = ($expectedLine -split "\s+")[0].Trim().ToLower()
            $actualHash = (Get-FileHash $installerPath -Algorithm SHA256).Hash.ToLower()

            if ($expectedHash -eq $actualHash) {
                Write-Ok "Checksum verified: $actualHash"
            } else {
                Write-Fail "Checksum verification FAILED!"
                Write-Fail "Expected: $expectedHash"
                Write-Fail "Actual:   $actualHash"
                Write-Fail ""
                Write-Fail "The downloaded file may be corrupted. Please try again."
                Remove-Item $installerPath -Force -ErrorAction SilentlyContinue
                Read-Host "Press Enter to exit"
                exit 1
            }
        } else {
            Write-Host "     No checksum found for $($installerAsset.name), skipping verification." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "     Could not verify checksum (non-fatal): $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "     No checksum file available, skipping verification." -ForegroundColor Yellow
}

# ---------------------------------------------------------------------------
# 5. Launch installer
# ---------------------------------------------------------------------------
Write-Step "Launching installer..."

try {
    Start-Process -FilePath $installerPath
    Write-Ok "Installer launched. Follow the on-screen instructions."
} catch {
    Write-Fail "Could not launch installer: $_"
    Write-Fail "You can run it manually from: $installerPath"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "  Done! The installer window should appear shortly." -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close this window"
