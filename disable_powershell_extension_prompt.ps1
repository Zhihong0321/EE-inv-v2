# Disable PowerShell Extension Recommendation Prompt in Cursor IDE
# This script stops Cursor from asking you to install the PowerShell extension

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Disable PowerShell Extension Prompt" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure .vscode directory exists
$vscodeDir = ".vscode"
if (-not (Test-Path $vscodeDir)) {
    New-Item -ItemType Directory -Path $vscodeDir -Force | Out-Null
    Write-Host "Created .vscode directory" -ForegroundColor Green
}

# Create or update extensions.json to explicitly ignore PowerShell extension
Write-Host "1. Creating extension recommendations file..." -ForegroundColor Yellow
$extensionsJsonPath = "$vscodeDir\extensions.json"
$extensionsConfig = @{
    recommendations = @()
    unwantedRecommendations = @(
        "ms-vscode.PowerShell"
    )
}

try {
    $extensionsJson = $extensionsConfig | ConvertTo-Json -Depth 10
    $extensionsJson | Set-Content $extensionsJsonPath -Encoding UTF8
    Write-Host "   ✓ Created extensions.json with PowerShell extension ignored" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to create extensions.json: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Update workspace settings to disable extension recommendations
Write-Host "2. Updating workspace settings..." -ForegroundColor Yellow
$workspaceSettingsPath = "$vscodeDir\settings.json"
$workspaceSettings = @{}

if (Test-Path $workspaceSettingsPath) {
    try {
        $workspaceContent = Get-Content $workspaceSettingsPath -Raw
        $workspaceSettings = $workspaceContent | ConvertFrom-Json -AsHashtable
        Write-Host "   ✓ Loaded existing workspace settings" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Error reading workspace settings, creating new" -ForegroundColor Yellow
        $workspaceSettings = @{}
    }
} else {
    Write-Host "   ⚠ Workspace settings not found, creating new" -ForegroundColor Yellow
    $workspaceSettings = @{}
}

# Add settings to suppress extension recommendations
$workspaceSettings['extensions.ignoreRecommendations'] = $false  # Keep false to allow other recommendations
$workspaceSettings['extensions.showRecommendationsOnlyOnDemand'] = $true  # Only show when explicitly requested

# Also ensure PowerShell settings are configured (from previous fix)
$workspaceSettings['powershell.integratedConsole.showOnStartup'] = $false
$workspaceSettings['powershell.enableProfileLoading'] = $false

$pwsh7Path = "D:\Program Files\PowerShell\7\pwsh.exe"
if (Test-Path $pwsh7Path) {
    $workspaceSettings['powershell.powerShellDefaultVersion'] = $pwsh7Path
}
$workspaceSettings['terminal.integrated.defaultProfile.windows'] = "PowerShell"

try {
    $workspaceJson = $workspaceSettings | ConvertTo-Json -Depth 10
    $workspaceJson | Set-Content $workspaceSettingsPath -Encoding UTF8
    Write-Host "   ✓ Updated workspace settings" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to update workspace settings: $_" -ForegroundColor Red
}

Write-Host ""

# Update user settings to suppress PowerShell extension prompts globally
Write-Host "3. Updating user settings..." -ForegroundColor Yellow
$userSettingsPath = "$env:APPDATA\Cursor\User\settings.json"
$userSettings = @{}

if (Test-Path $userSettingsPath) {
    try {
        $userContent = Get-Content $userSettingsPath -Raw
        $userSettings = $userContent | ConvertFrom-Json -AsHashtable
        Write-Host "   ✓ Loaded existing user settings" -ForegroundColor Green
    } catch {
        Write-Host "   ⚠ Error reading user settings, creating new" -ForegroundColor Yellow
        $userSettings = @{}
    }
} else {
    Write-Host "   ⚠ User settings not found, creating new" -ForegroundColor Yellow
    $userSettings = @{}
}

# Add setting to suppress extension recommendations globally
$userSettings['extensions.showRecommendationsOnlyOnDemand'] = $true

try {
    $settingsDir = Split-Path $userSettingsPath -Parent
    if (-not (Test-Path $settingsDir)) {
        New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
    }
    
    $userJson = $userSettings | ConvertTo-Json -Depth 10
    $userJson | Set-Content $userSettingsPath -Encoding UTF8
    Write-Host "   ✓ Updated user settings" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Failed to update user settings: $_" -ForegroundColor Red
}

Write-Host ""

# Summary
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✓ Created .vscode/extensions.json" -ForegroundColor Green
Write-Host "  - PowerShell extension marked as unwanted recommendation" -ForegroundColor Gray
Write-Host ""

Write-Host "✓ Updated workspace settings" -ForegroundColor Green
Write-Host "  - Extension recommendations only shown on demand" -ForegroundColor Gray
Write-Host ""

Write-Host "✓ Updated user settings" -ForegroundColor Green
Write-Host "  - Extension recommendations only shown on demand globally" -ForegroundColor Gray
Write-Host ""

Write-Host "⚠ IMPORTANT: Restart Cursor IDE for changes to take effect!" -ForegroundColor Yellow
Write-Host ""

Write-Host "What this does:" -ForegroundColor Cyan
Write-Host "  1. Marks PowerShell extension as 'unwanted' in workspace" -ForegroundColor White
Write-Host "  2. Hides extension recommendations unless you explicitly request them" -ForegroundColor White
Write-Host "  3. Cursor will stop prompting you to install PowerShell extension" -ForegroundColor White
Write-Host ""

Write-Host "Note: You can still install the extension manually if you want it later." -ForegroundColor Gray
Write-Host "      Just go to Extensions (Ctrl+Shift+X) and search for 'PowerShell'" -ForegroundColor Gray
Write-Host ""


