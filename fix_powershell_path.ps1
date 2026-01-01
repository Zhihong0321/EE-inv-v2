# Script to reorder PATH to prioritize PowerShell 7 over Windows PowerShell 5.1
# This script requires Administrator privileges

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PowerShell 7 PATH Configuration Script" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges!" -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Current PATH order (PowerShell entries):" -ForegroundColor Yellow
$machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine") -split ';'
$userPath = [Environment]::GetEnvironmentVariable("Path", "User") -split ';'
$allPath = $machinePath + $userPath

$pwsh7 = $allPath | Where-Object { $_ -eq "D:\Program Files\PowerShell\7" }
$pwsh5 = $allPath | Where-Object { $_ -eq "C:\WINDOWS\System32\WindowsPowerShell\v1.0" }

Write-Host "  Windows PowerShell 5.1: $pwsh5" -ForegroundColor Gray
Write-Host "  PowerShell 7: $pwsh7" -ForegroundColor Gray
Write-Host ""

# Reorder Machine PATH
Write-Host "Reordering Machine PATH..." -ForegroundColor Yellow
$newMachinePath = @()
$pwsh7InMachine = $machinePath | Where-Object { $_ -eq "D:\Program Files\PowerShell\7" }
$pwsh5InMachine = $machinePath | Where-Object { $_ -eq "C:\WINDOWS\System32\WindowsPowerShell\v1.0" }

# Add PowerShell 7 first (if it exists in Machine PATH)
if ($pwsh7InMachine) {
    $newMachinePath += $pwsh7InMachine
}

# Add all other paths except PowerShell entries
$newMachinePath += $machinePath | Where-Object { 
    $_ -ne "D:\Program Files\PowerShell\7" -and 
    $_ -ne "C:\WINDOWS\System32\WindowsPowerShell\v1.0" -and
    $_ -ne ""
}

# Add Windows PowerShell 5.1 last (if it exists in Machine PATH)
if ($pwsh5InMachine) {
    $newMachinePath += $pwsh5InMachine
}

# Update Machine PATH
$newMachinePathString = ($newMachinePath | Where-Object { $_ -ne "" }) -join ';'
[Environment]::SetEnvironmentVariable("Path", $newMachinePathString, "Machine")

Write-Host "✓ Machine PATH updated successfully!" -ForegroundColor Green
Write-Host ""

# Reorder User PATH (if PowerShell 7 is there)
$newUserPath = @()
$pwsh7InUser = $userPath | Where-Object { $_ -eq "D:\Program Files\PowerShell\7" }
$pwsh5InUser = $userPath | Where-Object { $_ -eq "C:\WINDOWS\System32\WindowsPowerShell\v1.0" }

if ($pwsh7InUser -or $pwsh5InUser) {
    Write-Host "Reordering User PATH..." -ForegroundColor Yellow
    
    if ($pwsh7InUser) {
        $newUserPath += $pwsh7InUser
    }
    
    $newUserPath += $userPath | Where-Object { 
        $_ -ne "D:\Program Files\PowerShell\7" -and 
        $_ -ne "C:\WINDOWS\System32\WindowsPowerShell\v1.0" -and
        $_ -ne ""
    }
    
    if ($pwsh5InUser) {
        $newUserPath += $pwsh5InUser
    }
    
    $newUserPathString = ($newUserPath | Where-Object { $_ -ne "" }) -join ';'
    [Environment]::SetEnvironmentVariable("Path", $newUserPathString, "User")
    
    Write-Host "✓ User PATH updated successfully!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PATH reordering complete!" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: You need to:" -ForegroundColor Yellow
Write-Host "  1. Restart Cursor IDE" -ForegroundColor Yellow
Write-Host "  2. Restart any open terminal windows" -ForegroundColor Yellow
Write-Host "  3. Or log out and log back in for changes to take effect" -ForegroundColor Yellow
Write-Host ""
Write-Host "After restarting, verify with: pwsh --version" -ForegroundColor Cyan
Write-Host ""









