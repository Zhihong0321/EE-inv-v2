# Quick Test: Simulate Multiple PowerShell Background Processes
# This is a safer, shorter version of the full test script

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Quick PowerShell Background Process Test" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This test will spawn 3 background processes for 10 seconds" -ForegroundColor Yellow
Write-Host "Watch Cursor IDE - if it crashes, the issue is confirmed" -ForegroundColor Yellow
Write-Host ""

$processes = @()

try {
    Write-Host "Spawning 3 background PowerShell processes..." -ForegroundColor Yellow
    
    for ($i = 1; $i -le 3; $i++) {
        $proc = Start-Process -FilePath "pwsh.exe" `
            -ArgumentList "-NoLogo", "-Command", "Start-Sleep -Seconds 10; Write-Host 'Process $i completed'" `
            -PassThru -WindowStyle Hidden
        
        $processes += $proc
        Write-Host "  Started process $i (PID: $($proc.Id))" -ForegroundColor Green
        Start-Sleep -Seconds 1
    }
    
    Write-Host ""
    Write-Host "Waiting 12 seconds for processes to complete..." -ForegroundColor Yellow
    Write-Host "If Cursor IDE crashes during this time, the issue is confirmed." -ForegroundColor Red
    Write-Host ""
    
    $elapsed = 0
    while ($elapsed -lt 12) {
        $running = ($processes | Where-Object { -not $_.HasExited }).Count
        Write-Host "  [$elapsed/12] Processes running: $running" -ForegroundColor Gray
        Start-Sleep -Seconds 2
        $elapsed += 2
    }
    
    Write-Host ""
    Write-Host "Checking results..." -ForegroundColor Yellow
    
    $completed = ($processes | Where-Object { $_.HasExited }).Count
    $running = ($processes | Where-Object { -not $_.HasExited }).Count
    
    Write-Host "  Completed: $completed" -ForegroundColor Green
    Write-Host "  Still running: $running" -ForegroundColor $(if ($running -gt 0) { "Yellow" } else { "Green" })
    
    if ($running -gt 0) {
        Write-Host ""
        Write-Host "Cleaning up remaining processes..." -ForegroundColor Yellow
        $processes | Where-Object { -not $_.HasExited } | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host ""
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host "Test Complete" -ForegroundColor Cyan
    Write-Host "===========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($running -eq 0) {
        Write-Host "✓ All processes completed successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "If Cursor IDE did NOT crash, the fixes may have worked!" -ForegroundColor Green
        Write-Host "If Cursor IDE DID crash, run: .\fix_powershell_crash.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "⚠ Some processes were still running and were terminated" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host ""
    Write-Host "✗ Error during test: $_" -ForegroundColor Red
} finally {
    # Cleanup
    Write-Host ""
    Write-Host "Cleaning up..." -ForegroundColor Yellow
    $processes | Where-Object { -not $_.HasExited } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Write-Host ""
Write-Host "Current PowerShell processes: $((Get-Process -Name pwsh -ErrorAction SilentlyContinue | Measure-Object).Count)" -ForegroundColor Gray
Write-Host ""



