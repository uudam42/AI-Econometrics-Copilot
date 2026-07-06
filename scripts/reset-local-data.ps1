# Reset local data — removes SQLite database, uploaded files, and generated artifacts.
# WARNING: This is destructive.

$RootDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host ""
Write-Host "WARNING: This will delete all local project data including:" -ForegroundColor Red
Write-Host "  - SQLite database"
Write-Host "  - Uploaded datasets"
Write-Host "  - Generated artifacts and exports"
Write-Host ""

$confirm = Read-Host "Are you sure? (y/N)"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    Remove-Item -Path (Join-Path $RootDir "backend\data") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path (Join-Path $RootDir "logs") -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Local data has been reset." -ForegroundColor Green
    Write-Host "Restart the application to create fresh directories."
} else {
    Write-Host "Cancelled."
}
