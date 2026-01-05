# Test Script: Reproduce PowerShell Background Process Crash in Cursor IDE
# This script simulates running multiple PowerShell processes in the background
# to identify what causes Cursor IDE to crash

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PowerShell Background Process Crash Test" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Test Configuration
$TestDuration = 30  # seconds
$MaxConcurrentProcesses = 5
$ProcessInterval = 2  # seconds between spawning processes

Write-Host "Test Configuration:" -ForegroundColor Yellow
Write-Host "  Duration: $TestDuration seconds" -ForegroundColor Gray
Write-Host "  Max Concurrent Processes: $MaxConcurrentProcesses" -ForegroundColor Gray
Write-Host "  Process Interval: $ProcessInterval seconds" -ForegroundColor Gray
Write-Host ""

# Check current PowerShell processes
Write-Host "1. Checking Current PowerShell Processes..." -ForegroundColor Yellow
$currentProcesses = Get-Process -Name pwsh,powershell -ErrorAction SilentlyContinue | Measure-Object
Write-Host "   Current PowerShell processes: $($currentProcesses.Count)" -ForegroundColor Gray
Write-Host ""

# Monitor system resources
Write-Host "2. Monitoring System Resources..." -ForegroundColor Yellow
$cpuBefore = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
$memBefore = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue, 2)
Write-Host "   CPU Usage: $cpuBefore%" -ForegroundColor Gray
Write-Host "   Available Memory: $memBefore MB" -ForegroundColor Gray
Write-Host ""

# Test 1: Spawn multiple background jobs
Write-Host "3. Test 1: Spawning Multiple Background Jobs..." -ForegroundColor Yellow
$jobs = @()
$startTime = Get-Date

for ($i = 1; $i -le $MaxConcurrentProcesses; $i++) {
    $job = Start-Job -ScriptBlock {
        param($jobNumber)
        Start-Sleep -Seconds 10
        Write-Output "Job $jobNumber completed"
        return $jobNumber
    } -ArgumentList $i
    
    $jobs += $job
    Write-Host "   Started job $i (ID: $($job.Id))" -ForegroundColor Gray
    Start-Sleep -Seconds $ProcessInterval
}

Write-Host "   Total jobs started: $($jobs.Count)" -ForegroundColor Green
Write-Host ""

# Test 2: Spawn multiple background processes using Start-Process
Write-Host "4. Test 2: Spawning Multiple Background Processes..." -ForegroundColor Yellow
$processes = @()

for ($i = 1; $i -le $MaxConcurrentProcesses; $i++) {
    $proc = Start-Process -FilePath "pwsh.exe" -ArgumentList "-NoLogo", "-Command", "Start-Sleep -Seconds 15; Write-Host 'Process $i completed'" -PassThru -WindowStyle Hidden
    $processes += $proc
    Write-Host "   Started process $i (PID: $($proc.Id))" -ForegroundColor Gray
    Start-Sleep -Seconds $ProcessInterval
}

Write-Host "   Total processes started: $($processes.Count)" -ForegroundColor Green
Write-Host ""

# Monitor during test
Write-Host "5. Monitoring During Test (waiting $TestDuration seconds)..." -ForegroundColor Yellow
$monitorInterval = 5
$elapsed = 0

while ($elapsed -lt $TestDuration) {
    Start-Sleep -Seconds $monitorInterval
    $elapsed += $monitorInterval
    
    $activeJobs = ($jobs | Where-Object { $_.State -eq 'Running' }).Count
    $activeProcesses = ($processes | Where-Object { -not $_.HasExited }).Count
    $allPwshProcesses = (Get-Process -Name pwsh,powershell -ErrorAction SilentlyContinue).Count
    
    $cpuCurrent = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
    $memCurrent = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue, 2)
    
    Write-Host "   [$elapsed/$TestDuration] Jobs: $activeJobs, Processes: $activeProcesses, Total Pwsh: $allPwshProcesses, CPU: $cpuCurrent%, Mem: $memCurrent MB" -ForegroundColor Gray
}

Write-Host ""

# Check results
Write-Host "6. Checking Results..." -ForegroundColor Yellow
$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

$completedJobs = ($jobs | Where-Object { $_.State -eq 'Completed' }).Count
$failedJobs = ($jobs | Where-Object { $_.State -eq 'Failed' }).Count
$runningJobs = ($jobs | Where-Object { $_.State -eq 'Running' }).Count

$completedProcesses = ($processes | Where-Object { $_.HasExited }).Count
$runningProcesses = ($processes | Where-Object { -not $_.HasExited }).Count

$cpuAfter = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
$memAfter = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue, 2)

Write-Host "   Test Duration: $duration seconds" -ForegroundColor Gray
Write-Host "   Jobs - Completed: $completedJobs, Failed: $failedJobs, Running: $runningJobs" -ForegroundColor Gray
Write-Host "   Processes - Completed: $completedProcesses, Running: $runningProcesses" -ForegroundColor Gray
Write-Host "   CPU Usage Change: $cpuBefore% -> $cpuAfter%" -ForegroundColor Gray
Write-Host "   Memory Change: $memBefore MB -> $memAfter MB (Freed: $([math]::Round($memBefore - $memAfter, 2)) MB)" -ForegroundColor Gray
Write-Host ""

# Cleanup
Write-Host "7. Cleaning Up..." -ForegroundColor Yellow
Write-Host "   Stopping remaining jobs..." -ForegroundColor Gray
$jobs | Stop-Job -ErrorAction SilentlyContinue
$jobs | Remove-Job -ErrorAction SilentlyContinue

Write-Host "   Stopping remaining processes..." -ForegroundColor Gray
foreach ($proc in $processes) {
    if (-not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 2

# Final check
$finalPwshProcesses = (Get-Process -Name pwsh,powershell -ErrorAction SilentlyContinue).Count
Write-Host "   Remaining PowerShell processes: $finalPwshProcesses" -ForegroundColor Gray
Write-Host ""

# Summary
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

if ($failedJobs -gt 0) {
    Write-Host "⚠ WARNING: $failedJobs jobs failed!" -ForegroundColor Red
}

if ($runningProcesses -gt 0) {
    Write-Host "⚠ WARNING: $runningProcesses processes still running!" -ForegroundColor Yellow
}

if (($memBefore - $memAfter) -gt 500) {
    Write-Host "⚠ WARNING: Significant memory usage detected!" -ForegroundColor Yellow
    Write-Host "   Memory freed: $([math]::Round($memBefore - $memAfter, 2)) MB" -ForegroundColor Gray
}

Write-Host ""
Write-Host "If Cursor IDE crashed during this test, the issue is likely:" -ForegroundColor Yellow
Write-Host "  1. Too many PowerShell language servers being spawned" -ForegroundColor White
Write-Host "  2. Resource exhaustion (CPU/Memory)" -ForegroundColor White
Write-Host "  3. PowerShell extension conflicts with background processes" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run: .\diagnose_powershell_crash.ps1" -ForegroundColor White
Write-Host "  2. Apply fixes from: .\fix_powershell_crash.ps1" -ForegroundColor White
Write-Host ""



