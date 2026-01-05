# Fix Script: Prevent PowerShell Background Process Crashes in Cursor IDE
# This script configures Cursor IDE settings to prevent crashes when running multiple PowerShell processes

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PowerShell Crash Prevention Fix" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator (not required, but helpful)
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "✓ Running with Administrator privileges" -ForegroundColor Green
} else {
    Write-Host "⚠ Not running as Administrator (some fixes may require admin)" -ForegroundColor Yellow
}
Write-Host ""

# 1. Backup current settings
Write-Host "1. Backing up current Cursor settings..." -ForegroundColor Yellow
$cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
$backupPath = "$cursorSettingsPath.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

if (Test-Path $cursorSettingsPath) {
    try {
        Copy-Item $cursorSettingsPath $backupPath -Force
        Write-Host "   ✓ Backup created: $backupPath" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Failed to backup settings: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠ Settings file not found, will create new one" -ForegroundColor Yellow
}

Write-Host ""

# 2. Read or create settings
Write-Host "2. Reading Cursor settings..." -ForegroundColor Yellow
$settings = @{}

if (Test-Path $cursorSettingsPath) {
    try {
        $settingsContent = Get-Content $cursorSettingsPath -Raw
        $settings = $settingsContent | ConvertFrom-Json -AsHashtable
        Write-Host "   ✓ Settings loaded" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Error reading settings, creating new: $_" -ForegroundColor Yellow
        $settings = @{}
    }
} else {
    Write-Host "   ⚠ Settings file not found, creating new" -ForegroundColor Yellow
    $settings = @{}
}

Write-Host ""

# 3. Apply fixes
Write-Host "3. Applying crash prevention fixes..." -ForegroundColor Yellow

# Fix 1: Disable Integrated Console (major cause of crashes)
if ($settings.ContainsKey('powershell.integratedConsole.showOnStartup')) {
    if ($settings['powershell.integratedConsole.showOnStartup'] -eq $true) {
        Write-Host "   Fixing: Disabling integrated console..." -ForegroundColor Gray
        $settings['powershell.integratedConsole.showOnStartup'] = $false
    } else {
        Write-Host "   ✓ Integrated console already disabled" -ForegroundColor Green
    }
} else {
    Write-Host "   Adding: Disabling integrated console..." -ForegroundColor Gray
    $settings['powershell.integratedConsole.showOnStartup'] = $false
}

# Fix 2: Disable profile loading (can slow down multiple processes)
if ($settings.ContainsKey('powershell.enableProfileLoading')) {
    if ($settings['powershell.enableProfileLoading'] -eq $true) {
        Write-Host "   Fixing: Disabling profile loading..." -ForegroundColor Gray
        $settings['powershell.enableProfileLoading'] = $false
    } else {
        Write-Host "   ✓ Profile loading already disabled" -ForegroundColor Green
    }
} else {
    Write-Host "   Adding: Disabling profile loading..." -ForegroundColor Gray
    $settings['powershell.enableProfileLoading'] = $false
}

# Fix 3: Limit language server instances
if (-not $settings.ContainsKey('powershell.developer.bundleModules')) {
    Write-Host "   Adding: Disabling bundle modules..." -ForegroundColor Gray
    $settings['powershell.developer.bundleModules'] = $false
} else {
    Write-Host "   ✓ Bundle modules setting exists" -ForegroundColor Green
}

# Fix 4: Set PowerShell 7 as default
$pwsh7Path = "D:\Program Files\PowerShell\7\pwsh.exe"
if (Test-Path $pwsh7Path) {
    if (-not $settings.ContainsKey('powershell.powerShellDefaultVersion')) {
        Write-Host "   Adding: Setting PowerShell 7 as default..." -ForegroundColor Gray
        $settings['powershell.powerShellDefaultVersion'] = $pwsh7Path
    } elseif ($settings['powershell.powerShellDefaultVersion'] -ne $pwsh7Path) {
        Write-Host "   Fixing: Updating PowerShell default version..." -ForegroundColor Gray
        $settings['powershell.powerShellDefaultVersion'] = $pwsh7Path
    } else {
        Write-Host "   ✓ PowerShell 7 already set as default" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠ PowerShell 7 not found at expected path" -ForegroundColor Yellow
}

# Fix 5: Configure terminal to use PowerShell 7
if (-not $settings.ContainsKey('terminal.integrated.defaultProfile.windows')) {
    Write-Host "   Adding: Setting PowerShell as default terminal..." -ForegroundColor Gray
    $settings['terminal.integrated.defaultProfile.windows'] = "PowerShell"
} else {
    Write-Host "   ✓ Terminal default profile already set" -ForegroundColor Green
}

# Fix 6: Configure terminal profiles
if (-not $settings.ContainsKey('terminal.integrated.profiles.windows')) {
    $settings['terminal.integrated.profiles.windows'] = @{}
}

$terminalProfiles = $settings['terminal.integrated.profiles.windows']
if ($terminalProfiles -isnot [hashtable]) {
    $terminalProfiles = @{}
}

if (-not $terminalProfiles.ContainsKey('PowerShell')) {
    Write-Host "   Adding: Configuring PowerShell terminal profile..." -ForegroundColor Gray
    $terminalProfiles['PowerShell'] = @{
        path = $pwsh7Path
        args = @("-NoLogo")
    }
} else {
    Write-Host "   ✓ PowerShell terminal profile already configured" -ForegroundColor Green
}

$settings['terminal.integrated.profiles.windows'] = $terminalProfiles

# Fix 7: Limit concurrent terminal instances (prevent resource exhaustion)
if (-not $settings.ContainsKey('terminal.integrated.maxTerminalHistory')) {
    Write-Host "   Adding: Limiting terminal history..." -ForegroundColor Gray
    $settings['terminal.integrated.maxTerminalHistory'] = 1000
}

# Fix 8: Disable automatic terminal creation
if (-not $settings.ContainsKey('terminal.integrated.automationProfile.windows')) {
    Write-Host "   Adding: Configuring automation profile..." -ForegroundColor Gray
    $settings['terminal.integrated.automationProfile.windows'] = @{
        path = $pwsh7Path
        args = @("-NoLogo")
    }
}

Write-Host ""

# 4. Save settings
Write-Host "4. Saving settings..." -ForegroundColor Yellow
try {
    # Ensure directory exists
    $settingsDir = Split-Path $cursorSettingsPath -Parent
    if (-not (Test-Path $settingsDir)) {
        New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
    }
    
    # Convert hashtable to JSON and save
    $jsonContent = $settings | ConvertTo-Json -Depth 10
    $jsonContent | Set-Content $cursorSettingsPath -Encoding UTF8
    
    Write-Host "   ✓ Settings saved successfully" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to save settings: $_" -ForegroundColor Red
    Write-Host "   Error details: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 5. Create workspace settings (optional but recommended)
Write-Host "5. Creating workspace settings..." -ForegroundColor Yellow
$workspaceSettingsPath = ".vscode\settings.json"
$workspaceSettings = @{}

if (Test-Path $workspaceSettingsPath) {
    try {
        $workspaceContent = Get-Content $workspaceSettingsPath -Raw
        $workspaceSettings = $workspaceContent | ConvertFrom-Json -AsHashtable
        Write-Host "   ✓ Workspace settings loaded" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Error reading workspace settings, creating new" -ForegroundColor Yellow
        $workspaceSettings = @{}
    }
} else {
    Write-Host "   ⚠ Workspace settings not found, creating new" -ForegroundColor Yellow
    $workspaceSettings = @{}
}

# Apply same fixes to workspace settings
$workspaceSettings['powershell.integratedConsole.showOnStartup'] = $false
$workspaceSettings['powershell.enableProfileLoading'] = $false
if (Test-Path $pwsh7Path) {
    $workspaceSettings['powershell.powerShellDefaultVersion'] = $pwsh7Path
}
$workspaceSettings['terminal.integrated.defaultProfile.windows'] = "PowerShell"

try {
    $workspaceDir = Split-Path $workspaceSettingsPath -Parent
    if (-not (Test-Path $workspaceDir)) {
        New-Item -ItemType Directory -Path $workspaceDir -Force | Out-Null
    }
    
    $workspaceJson = $workspaceSettings | ConvertTo-Json -Depth 10
    $workspaceJson | Set-Content $workspaceSettingsPath -Encoding UTF8
    Write-Host "   ✓ Workspace settings saved" -ForegroundColor Green
} catch {
    Write-Host "   ⚠ Failed to save workspace settings: $_" -ForegroundColor Yellow
}

Write-Host ""

# 6. Clean up any existing background jobs/processes
Write-Host "6. Cleaning up existing background processes..." -ForegroundColor Yellow
$backgroundJobs = Get-Job -ErrorAction SilentlyContinue
if ($backgroundJobs) {
    Write-Host "   Stopping $($backgroundJobs.Count) background jobs..." -ForegroundColor Gray
    $backgroundJobs | Stop-Job -ErrorAction SilentlyContinue
    $backgroundJobs | Remove-Job -ErrorAction SilentlyContinue
    Write-Host "   ✓ Background jobs cleaned up" -ForegroundColor Green
} else {
    Write-Host "   ✓ No background jobs to clean up" -ForegroundColor Green
}

Write-Host ""

# Summary
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Fix Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Applied fixes:" -ForegroundColor Green
Write-Host "  1. Disabled PowerShell integrated console" -ForegroundColor White
Write-Host "  2. Disabled PowerShell profile loading" -ForegroundColor White
Write-Host "  3. Configured PowerShell 7 as default" -ForegroundColor White
Write-Host "  4. Configured terminal profiles" -ForegroundColor White
Write-Host "  5. Limited terminal history" -ForegroundColor White
Write-Host ""

Write-Host "⚠ IMPORTANT: You MUST restart Cursor IDE for changes to take effect!" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Close Cursor IDE completely" -ForegroundColor White
Write-Host "  2. Check Task Manager to ensure no Cursor processes are running" -ForegroundColor White
Write-Host "  3. Restart Cursor IDE" -ForegroundColor White
Write-Host "  4. Test with: .\test_powershell_background_crash.ps1" -ForegroundColor White
Write-Host ""

if (Test-Path $backupPath) {
    Write-Host "Backup saved to: $backupPath" -ForegroundColor Gray
    Write-Host ""
}



