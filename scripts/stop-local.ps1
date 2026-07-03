# Stop locally running AI Econometrics Copilot services (Windows PowerShell)

foreach ($port in @(8000, 3000)) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($pid in $proc) {
        try {
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "Stopped process on port $port (PID $pid)" -ForegroundColor Green
        } catch {
            Write-Host "Could not stop PID $pid on port $port" -ForegroundColor Yellow
        }
    }
}

Get-Job | Where-Object { $_.Name -like "*econometrics*" -or $_.State -eq "Running" } |
    Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "All services stopped." -ForegroundColor Green
