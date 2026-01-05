# PowerShell Extension Debugging Script for Cursor IDE
# This script helps diagnose and fix PowerShell extension issues

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "PowerShell Extension Debugging Tool" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check PowerShell 7 installation
Write-Host "1. Checking PowerShell 7 Installation..." -ForegroundColor Yellow
$pwsh7Path = "D:\Program Files\PowerShell\7\pwsh.exe"
if (Test-Path $pwsh7Path) {
    $version = & $pwsh7Path --version
    Write-Host "   ✓ PowerShell 7 found: $version" -ForegroundColor Green
    Write-Host "   Path: $pwsh7Path" -ForegroundColor Gray
} else {
    Write-Host "   ✗ PowerShell 7 NOT found at: $pwsh7Path" -ForegroundColor Red
}
Write-Host ""

# Check Windows PowerShell 5.1
Write-Host "2. Checking Windows PowerShell 5.1..." -ForegroundColor Yellow
$pwsh5Path = "C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe"
if (Test-Path $pwsh5Path) {
    Write-Host "   ✓ Windows PowerShell 5.1 found" -ForegroundColor Green
    Write-Host "   Path: $pwsh5Path" -ForegroundColor Gray
} else {
    Write-Host "   ✗ Windows PowerShell 5.1 NOT found" -ForegroundColor Red
}
Write-Host ""

# Check PATH order
Write-Host "3. Checking PATH order..." -ForegroundColor Yellow
$envPath = $env:PATH -split ';'
$pwsh7Index = -1
$pwsh5Index = -1

for ($i = 0; $i -lt $envPath.Length; $i++) {
    if ($envPath[$i] -eq "D:\Program Files\PowerShell\7") {
        $pwsh7Index = $i
    }
    if ($envPath[$i] -eq "C:\WINDOWS\System32\WindowsPowerShell\v1.0") {
        $pwsh5Index = $i
    }
}

if ($pwsh7Index -ge 0 -and $pwsh5Index -ge 0) {
    if ($pwsh7Index -lt $pwsh5Index) {
        Write-Host "   ✓ PowerShell 7 comes BEFORE Windows PowerShell 5.1 in PATH" -ForegroundColor Green
        Write-Host "   PowerShell 7 index: $pwsh7Index" -ForegroundColor Gray
        Write-Host "   PowerShell 5.1 index: $pwsh5Index" -ForegroundColor Gray
    } else {
        Write-Host "   ✗ WARNING: Windows PowerShell 5.1 comes BEFORE PowerShell 7 in PATH" -ForegroundColor Red
        Write-Host "   PowerShell 7 index: $pwsh7Index" -ForegroundColor Gray
        Write-Host "   PowerShell 5.1 index: $pwsh5Index" -ForegroundColor Gray
        Write-Host "   Run fix_powershell_path.ps1 as Administrator to fix this" -ForegroundColor Yellow
    }
} else {
    if ($pwsh7Index -lt 0) {
        Write-Host "   ✗ PowerShell 7 NOT in PATH" -ForegroundColor Red
    }
    if ($pwsh5Index -lt 0) {
        Write-Host "   ✗ Windows PowerShell 5.1 NOT in PATH" -ForegroundColor Red
    }
}
Write-Host ""

# Check Cursor settings
Write-Host "4. Checking Cursor IDE Settings..." -ForegroundColor Yellow
$cursorSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
if (Test-Path $cursorSettingsPath) {
    try {
        $settings = Get-Content $cursorSettingsPath -Raw | ConvertFrom-Json
        
        $defaultVersion = $settings.'powershell.powerShellDefaultVersion'
        $defaultProfile = $settings.'terminal.integrated.defaultProfile.windows'
        
        if ($defaultVersion) {
            Write-Host "   ✓ PowerShell Extension Default Version: $defaultVersion" -ForegroundColor Green
            if ($defaultVersion -eq $pwsh7Path) {
                Write-Host "      Correctly set to PowerShell 7" -ForegroundColor Green
            } else {
                Write-Host "      ✗ Should be: $pwsh7Path" -ForegroundColor Red
            }
        } else {
            Write-Host "   ✗ PowerShell Extension Default Version NOT set" -ForegroundColor Red
        }
        
        if ($defaultProfile) {
            Write-Host "   ✓ Terminal Default Profile: $defaultProfile" -ForegroundColor Green
        } else {
            Write-Host "   ✗ Terminal Default Profile NOT set" -ForegroundColor Red
        }
        
        $profilePath = $settings.'terminal.integrated.profiles.windows'.PowerShell.path
        if ($profilePath) {
            Write-Host "   ✓ Terminal PowerShell Profile Path: $profilePath" -ForegroundColor Green
            if ($profilePath -eq $pwsh7Path) {
                Write-Host "      Correctly set to PowerShell 7" -ForegroundColor Green
            } else {
                Write-Host "      ✗ Should be: $pwsh7Path" -ForegroundColor Red
            }
        }
        
    } catch {
        Write-Host "   ✗ Error reading settings: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ✗ Cursor settings file not found at: $cursorSettingsPath" -ForegroundColor Red
}
Write-Host ""

# Check workspace settings
Write-Host "5. Checking Workspace Settings..." -ForegroundColor Yellow
$workspaceSettingsPath = ".vscode\settings.json"
if (Test-Path $workspaceSettingsPath) {
    try {
        $settings = Get-Content $workspaceSettingsPath -Raw | ConvertFrom-Json
        Write-Host "   ✓ Workspace settings file exists" -ForegroundColor Green
        
        $defaultVersion = $settings.'powershell.powerShellDefaultVersion'
        if ($defaultVersion) {
            Write-Host "   ✓ PowerShell Extension Default Version: $defaultVersion" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ✗ Error reading workspace settings: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   ⚠ Workspace settings file not found (optional)" -ForegroundColor Yellow
}
Write-Host ""

# Test PowerShell 7 execution
Write-Host "6. Testing PowerShell 7 Execution..." -ForegroundColor Yellow
try {
    $testResult = & $pwsh7Path -Command '$PSVersionTable.PSVersion'
    Write-Host "   ✓ PowerShell 7 executes successfully" -ForegroundColor Green
    Write-Host "   Version: $testResult" -ForegroundColor Gray
} catch {
    Write-Host "   ✗ PowerShell 7 execution failed: $_" -ForegroundColor Red
}
Write-Host ""

# Check for common issues
Write-Host "7. Common Issues Check..." -ForegroundColor Yellow
$issues = @()

# Check if pwsh command works
try {
    $null = Get-Command pwsh -ErrorAction Stop
    Write-Host "   ✓ 'pwsh' command is available" -ForegroundColor Green
} catch {
    Write-Host "   ✗ 'pwsh' command NOT available (not in PATH)" -ForegroundColor Red
    $issues += "pwsh command not in PATH"
}

# Check PowerShell extension installation
$extensionPath = "$env:USERPROFILE\.cursor\extensions"
if (Test-Path $extensionPath) {
    $psExtensions = Get-ChildItem $extensionPath -Filter "*powershell*" -Directory -ErrorAction SilentlyContinue
    if ($psExtensions) {
        Write-Host "   ✓ PowerShell extension found" -ForegroundColor Green
        foreach ($ext in $psExtensions) {
            Write-Host "      - $($ext.Name)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   ⚠ PowerShell extension not found in extensions folder" -ForegroundColor Yellow
    }
}

Write-Host ""

# Summary and recommendations
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Summary & Recommendations" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

if ($issues.Count -eq 0) {
    Write-Host "✓ No major issues detected!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If PowerShell is still not working in Cursor:" -ForegroundColor Yellow
    Write-Host "  1. Restart Cursor IDE completely" -ForegroundColor White
    Write-Host "  2. Close all terminal windows and open a new one" -ForegroundColor White
    Write-Host "  3. Check the Output panel (View > Output) and select 'PowerShell' from dropdown" -ForegroundColor White
    Write-Host "  4. Try running: pwsh --version in a new terminal" -ForegroundColor White
} else {
    Write-Host "Issues found:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor Yellow
    Write-Host "  1. Run fix_powershell_path.ps1 as Administrator" -ForegroundColor White
    Write-Host "  2. Restart Cursor IDE" -ForegroundColor White
}

Write-Host ""













