# Comprehensive PowerShell Crash Diagnostic Script for Cursor IDE
# This script diagnoses why Cursor IDE crashes when running multiple PowerShell processes

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PowerShell Crash Diagnostic Tool" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$warnings = @()
$info = @()

# 1. Check PowerShell Extension Status
Write-Host "1. Checking PowerShell Extension Status..." -ForegroundColor Yellow
$extensionPath = "$env:USERPROFILE\.cursor\extensions"
$psExtensionFound = $false

if (Test-Path $extensionPath) {
    $psExtensions = Get-ChildItem $extensionPath -Filter "*powershell*" -Directory -ErrorAction SilentlyContinue
    if ($psExtensions) {
        $psExtensionFound = $true
        Write-Host "   ✓ PowerShell extension installed" -ForegroundColor Green
        foreach ($ext in $psExtensions) {
            Write-Host "      - $($ext.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠ PowerShell extension not found" -ForegroundColor Yellow
        $warnings += "PowerShell extension not installed"
    }
} else {
    Write-Host "   ⚠ Extensions folder not found" -ForegroundColor Yellow
}

Write-Host ""

# 2. Check Cursor Settings
Write-Host "2. Checking Cursor IDE Settings..." -ForegroundColor Yellow
$cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
$settingsIssues = @()

if (Test-Path $cursorSettingsPath) {
    try {
        $settings = Get-Content $cursorSettingsPath -Raw | ConvertFrom-Json
        
        # Check integrated console setting
        $integratedConsole = $settings.'powershell.integratedConsole.showOnStartup'
        if ($integratedConsole -eq $true) {
            Write-Host "   ✗ Integrated Console is ENABLED (can cause crashes)" -ForegroundColor Red
            $issues += "powershell.integratedConsole.showOnStartup is enabled"
        } else {
            Write-Host "   ✓ Integrated Console is disabled" -ForegroundColor Green
        }
        
        # Check profile loading
        $profileLoading = $settings.'powershell.enableProfileLoading'
        if ($profileLoading -eq $true) {
            Write-Host "   ⚠ Profile loading is enabled (can slow down multiple processes)" -ForegroundColor Yellow
            $warnings += "Profile loading enabled - may cause delays with multiple processes"
        } else {
            Write-Host "   ✓ Profile loading is disabled" -ForegroundColor Green
        }
        
        # Check language server settings
        $bundleModules = $settings.'powershell.bundleModules'
        if ($bundleModules -eq $true) {
            Write-Host "   ⚠ Bundle modules enabled (can increase memory usage)" -ForegroundColor Yellow
        } else {
            Write-Host "   ✓ Bundle modules disabled" -ForegroundColor Green
        }
        
        # Check default version
        $defaultVersion = $settings.'powershell.powerShellDefaultVersion'
        if ($defaultVersion) {
            Write-Host "   ✓ PowerShell default version set: $defaultVersion" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ PowerShell default version not set" -ForegroundColor Yellow
            $warnings += "PowerShell default version not configured"
        }
        
    } catch {
        Write-Host "   ✗ Error reading settings: $_" -ForegroundColor Red
        $issues += "Cannot read Cursor settings file"
    }
} else {
    Write-Host "   ⚠ Settings file not found" -ForegroundColor Yellow
    $warnings += "Cursor settings file not found"
}

Write-Host ""

# 3. Check Current PowerShell Processes
Write-Host "3. Checking Current PowerShell Processes..." -ForegroundColor Yellow
$pwshProcesses = Get-Process -Name pwsh -ErrorAction SilentlyContinue
$ps5Processes = Get-Process -Name powershell -ErrorAction SilentlyContinue

$totalProcesses = ($pwshProcesses | Measure-Object).Count + ($ps5Processes | Measure-Object).Count

Write-Host "   PowerShell 7 (pwsh) processes: $(($pwshProcesses | Measure-Object).Count)" -ForegroundColor Gray
Write-Host "   Windows PowerShell 5.1 processes: $(($ps5Processes | Measure-Object).Count)" -ForegroundColor Gray
Write-Host "   Total PowerShell processes: $totalProcesses" -ForegroundColor Gray

if ($totalProcesses -gt 10) {
    Write-Host "   ⚠ WARNING: High number of PowerShell processes ($totalProcesses)" -ForegroundColor Yellow
    $warnings += "High number of PowerShell processes running ($totalProcesses)"
}

# Check for language server processes
$languageServers = $pwshProcesses | Where-Object { 
    $_.CommandLine -like "*powershell-editor-services*" -or 
    $_.CommandLine -like "*OmniSharp*" 
}

if ($languageServers) {
    $lsCount = ($languageServers | Measure-Object).Count
    Write-Host "   ⚠ Language server processes detected: $lsCount" -ForegroundColor Yellow
    $warnings += "Multiple language server processes detected ($lsCount)"
}

Write-Host ""

# 4. Check System Resources
Write-Host "4. Checking System Resources..." -ForegroundColor Yellow
try {
    $cpu = (Get-Counter '\Processor(_Total)\% Processor Time').CounterSamples[0].CookedValue
    $mem = [math]::Round((Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue, 2)
    $totalMem = [math]::Round((Get-Counter '\Memory\Committed Bytes').CounterSamples[0].CookedValue / 1MB, 2)
    
    Write-Host "   CPU Usage: $cpu%" -ForegroundColor Gray
    Write-Host "   Available Memory: $mem MB" -ForegroundColor Gray
    Write-Host "   Committed Memory: $totalMem MB" -ForegroundColor Gray
    
    if ($cpu -gt 80) {
        Write-Host "   ⚠ WARNING: High CPU usage" -ForegroundColor Yellow
        $warnings += "High CPU usage ($cpu%)"
    }
    
    if ($mem -lt 1000) {
        Write-Host "   ⚠ WARNING: Low available memory" -ForegroundColor Yellow
        $warnings += "Low available memory ($mem MB)"
    }
} catch {
    Write-Host "   ⚠ Could not retrieve system resources: $_" -ForegroundColor Yellow
}

Write-Host ""

# 5. Check PowerShell Profile
Write-Host "5. Checking PowerShell Profile..." -ForegroundColor Yellow
$profilePath = $PROFILE.CurrentUserAllHosts
if (Test-Path $profilePath) {
    try {
        $profileContent = Get-Content $profilePath -ErrorAction Stop
        $profileSize = ($profileContent | Measure-Object -Line).Lines
        Write-Host "   ✓ Profile exists ($profileSize lines)" -ForegroundColor Green
        
        # Check for common problematic patterns
        $profileText = $profileContent -join "`n"
        if ($profileText -match "Start-Process.*pwsh") {
            Write-Host "   ⚠ Profile contains Start-Process commands (can spawn multiple processes)" -ForegroundColor Yellow
            $warnings += "Profile contains Start-Process commands"
        }
        if ($profileText -match "Start-Job") {
            Write-Host "   ⚠ Profile contains Start-Job commands" -ForegroundColor Yellow
            $warnings += "Profile contains Start-Job commands"
        }
    } catch {
        Write-Host "   ✗ Error reading profile: $_" -ForegroundColor Red
        $issues += "PowerShell profile has errors"
    }
} else {
    Write-Host "   ✓ No profile found (this is fine)" -ForegroundColor Green
}

Write-Host ""

# 6. Check Cursor Process Status
Write-Host "6. Checking Cursor IDE Process Status..." -ForegroundColor Yellow
$cursorProcesses = Get-Process -Name "Cursor" -ErrorAction SilentlyContinue
if ($cursorProcesses) {
    $cursorCount = ($cursorProcesses | Measure-Object).Count
    Write-Host "   Cursor processes running: $cursorCount" -ForegroundColor Gray
    
    foreach ($proc in $cursorProcesses) {
        $memUsage = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        Write-Host "      PID $($proc.Id): $memUsage MB" -ForegroundColor Gray
        
        if ($memUsage -gt 2000) {
            Write-Host "         ⚠ High memory usage" -ForegroundColor Yellow
            $warnings += "Cursor process using high memory ($memUsage MB)"
        }
    }
} else {
    Write-Host "   ⚠ Cursor IDE not running (or process name different)" -ForegroundColor Yellow
}

Write-Host ""

# 7. Check for Background Jobs
Write-Host "7. Checking Background Jobs..." -ForegroundColor Yellow
$backgroundJobs = Get-Job -ErrorAction SilentlyContinue
if ($backgroundJobs) {
    $jobCount = ($backgroundJobs | Measure-Object).Count
    Write-Host "   ⚠ Background jobs found: $jobCount" -ForegroundColor Yellow
    $warnings += "Background jobs running ($jobCount)"
    
    foreach ($job in $backgroundJobs) {
        Write-Host "      Job $($job.Id): $($job.State)" -ForegroundColor Gray
    }
} else {
    Write-Host "   ✓ No background jobs" -ForegroundColor Green
}

Write-Host ""

# 8. Check Event Logs for Crashes
Write-Host "8. Checking Recent Crashes..." -ForegroundColor Yellow
try {
    $recentErrors = Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        Level = 2,3  # Error and Warning
        StartTime = (Get-Date).AddHours(-24)
    } -ErrorAction SilentlyContinue | Where-Object {
        $_.Message -like "*Cursor*" -or 
        $_.Message -like "*PowerShell*" -or
        $_.Message -like "*pwsh*"
    } | Select-Object -First 5
    
    if ($recentErrors) {
        Write-Host "   ⚠ Recent errors found in Event Log:" -ForegroundColor Yellow
        foreach ($error in $recentErrors) {
            Write-Host "      [$($error.TimeCreated)] $($error.LevelDisplayName): $($error.Message.Substring(0, [Math]::Min(100, $error.Message.Length)))..." -ForegroundColor Gray
        }
        $warnings += "Recent errors found in Event Log"
    } else {
        Write-Host "   ✓ No recent crashes found in Event Log" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠ Could not check Event Log: $_" -ForegroundColor Yellow
}

Write-Host ""

# Summary
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Diagnostic Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✓ No major issues detected!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If crashes still occur, possible causes:" -ForegroundColor Yellow
    Write-Host "  1. PowerShell extension spawning too many language servers" -ForegroundColor White
    Write-Host "  2. Resource limits being exceeded during peak usage" -ForegroundColor White
    Write-Host "  3. Extension conflicts with Cursor's internal processes" -ForegroundColor White
    Write-Host ""
    Write-Host "Recommendation: Run fix_powershell_crash.ps1 to apply preventive settings" -ForegroundColor Cyan
} else {
    if ($issues.Count -gt 0) {
        Write-Host "✗ CRITICAL ISSUES FOUND:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "   - $issue" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠ WARNINGS:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
    
    Write-Host "Recommended Actions:" -ForegroundColor Cyan
    Write-Host "  1. Run: .\fix_powershell_crash.ps1" -ForegroundColor White
    Write-Host "  2. Restart Cursor IDE" -ForegroundColor White
    Write-Host "  3. Test with: .\test_powershell_background_crash.ps1" -ForegroundColor White
}

Write-Host ""



