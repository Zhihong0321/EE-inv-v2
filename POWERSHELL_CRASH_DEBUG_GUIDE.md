# PowerShell Background Process Crash Debug Guide

## Problem Description

Cursor IDE crashes when running multiple PowerShell processes in the background. The error message typically says "something running in the background is crashed, ask me to restart Cursor IDE".

## Root Causes

Based on analysis, the crashes are likely caused by:

1. **PowerShell Extension Language Server Conflicts**
   - The PowerShell extension spawns a language server for each PowerShell session
   - Multiple background processes trigger multiple language servers
   - Resource exhaustion leads to crashes

2. **Integrated Console Feature**
   - The `powershell.integratedConsole.showOnStartup` setting creates additional processes
   - Conflicts with background jobs and processes

3. **Profile Loading Overhead**
   - Each PowerShell process loads the profile script
   - Multiple processes loading profiles simultaneously cause delays and conflicts

4. **Resource Limits**
   - Too many concurrent PowerShell processes exhaust CPU/Memory
   - Cursor IDE's process limits are exceeded

## Solution Tools

Three scripts have been created to help debug and fix this issue:

### 1. `diagnose_powershell_crash.ps1`
**Purpose**: Comprehensive diagnostic tool to identify the root cause

**What it checks**:
- PowerShell extension status
- Cursor IDE settings (integrated console, profile loading, etc.)
- Current PowerShell processes and language servers
- System resources (CPU, Memory)
- PowerShell profile issues
- Cursor process status
- Background jobs
- Event log crashes

**Usage**:
```powershell
.\diagnose_powershell_crash.ps1
```

**Output**: Lists all issues and warnings found

---

### 2. `fix_powershell_crash.ps1`
**Purpose**: Automatically applies fixes to prevent crashes

**What it fixes**:
- ✅ Disables PowerShell integrated console
- ✅ Disables PowerShell profile loading
- ✅ Sets PowerShell 7 as default
- ✅ Configures terminal profiles properly
- ✅ Limits terminal history
- ✅ Cleans up existing background jobs

**Usage**:
```powershell
.\fix_powershell_crash.ps1
```

**Important**: You MUST restart Cursor IDE after running this script!

**Backup**: Automatically creates a backup of your settings before making changes

---

### 3. `test_powershell_background_crash.ps1`
**Purpose**: Reproduces the crash scenario to test if fixes work

**What it does**:
- Spawns multiple background jobs
- Spawns multiple background processes
- Monitors system resources
- Tracks process/job completion
- Cleans up after test

**Usage**:
```powershell
.\test_powershell_background_crash.ps1
```

**Note**: Run this AFTER applying fixes to verify they work

---

## Step-by-Step Debugging Process

### Step 1: Diagnose the Problem
```powershell
.\diagnose_powershell_crash.ps1
```

Review the output:
- **Critical Issues** (marked with ✗): Must be fixed
- **Warnings** (marked with ⚠): Should be addressed
- **Info** (marked with ✓): Already configured correctly

### Step 2: Apply Fixes
```powershell
.\fix_powershell_crash.ps1
```

The script will:
1. Backup your current settings
2. Apply all necessary fixes
3. Show a summary of changes

### Step 3: Restart Cursor IDE
**CRITICAL**: You must restart Cursor IDE for changes to take effect!

1. Close Cursor IDE completely
2. Check Task Manager to ensure no Cursor processes are running
3. Restart Cursor IDE

### Step 4: Test the Fix
```powershell
.\test_powershell_background_crash.ps1
```

This will simulate running multiple PowerShell processes. If Cursor doesn't crash, the fix worked!

---

## Manual Fixes (If Scripts Don't Work)

### Option 1: Disable PowerShell Extension (Recommended)

If you only use PowerShell for terminal commands, you don't need the extension:

1. Open Extensions: `Ctrl + Shift + X`
2. Search for "PowerShell"
3. Find "PowerShell" by Microsoft
4. Click gear icon → **"Disable"**
5. Restart Cursor IDE

**What you lose**: IntelliSense, debugging, script analysis  
**What you keep**: ✅ Terminal with PowerShell 7 (fully functional)

### Option 2: Configure Settings Manually

Open Cursor settings (`Ctrl + ,`) and add these to `settings.json`:

```json
{
  "powershell.integratedConsole.showOnStartup": false,
  "powershell.enableProfileLoading": false,
  "powershell.powerShellDefaultVersion": "D:\\Program Files\\PowerShell\\7\\pwsh.exe",
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "path": "D:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "args": ["-NoLogo"]
    }
  }
}
```

### Option 3: Limit Background Processes

When running PowerShell scripts in the background, limit concurrent processes:

```powershell
# Instead of spawning unlimited processes
$maxConcurrent = 3
$processes = @()

foreach ($item in $items) {
    # Wait if we've reached the limit
    while ($processes.Count -ge $maxConcurrent) {
        $processes = $processes | Where-Object { -not $_.HasExited }
        Start-Sleep -Milliseconds 500
    }
    
    # Spawn new process
    $proc = Start-Process pwsh.exe -ArgumentList "-File", "script.ps1" -PassThru
    $processes += $proc
}
```

---

## Prevention Best Practices

1. **Limit Concurrent Processes**
   - Don't spawn unlimited background processes
   - Use a queue system or limit to 3-5 concurrent processes

2. **Use Background Jobs Instead of Processes**
   ```powershell
   # Better: Use Start-Job
   $job = Start-Job -ScriptBlock { ... }
   
   # Instead of: Start-Process pwsh.exe
   ```

3. **Clean Up After Yourself**
   ```powershell
   # Always clean up jobs
   Get-Job | Stop-Job
   Get-Job | Remove-Job
   
   # Always clean up processes
   Get-Process pwsh | Where-Object { $_.Id -ne $PID } | Stop-Process
   ```

4. **Monitor Resource Usage**
   - Check CPU/Memory before spawning new processes
   - Don't spawn processes if resources are low

5. **Use PowerShell 7 Directly**
   - If extension causes issues, use PowerShell 7 terminal directly
   - Extension is optional for terminal usage

---

## Troubleshooting

### Issue: Scripts fail with "execution policy" error

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Settings file is locked or can't be written

**Solution**:
1. Close Cursor IDE completely
2. Run the fix script
3. Restart Cursor IDE

### Issue: Cursor still crashes after fixes

**Solution**:
1. Disable PowerShell extension completely
2. Use PowerShell terminal without extension
3. Check Event Viewer for crash details

### Issue: Too many PowerShell processes running

**Solution**:
```powershell
# Kill all PowerShell processes except current
Get-Process pwsh | Where-Object { $_.Id -ne $PID } | Stop-Process -Force
```

---

## Verification

After applying fixes, verify everything works:

```powershell
# 1. Check PowerShell version
pwsh --version
# Should show: PowerShell 7.5.4

# 2. Check settings
code $env:APPDATA\Cursor\User\settings.json
# Verify settings are applied

# 3. Test background process
Start-Job -ScriptBlock { Start-Sleep 5; "Done" } | Out-Null
Get-Job
# Should show job running without crashing Cursor

# 4. Run test script
.\test_powershell_background_crash.ps1
# Should complete without crashing Cursor
```

---

## Additional Resources

- **PowerShell Extension Docs**: https://github.com/PowerShell/vscode-powershell
- **Cursor IDE Settings**: `Ctrl + ,` → Search "powershell"
- **PowerShell Output Panel**: `View > Output` → Select "PowerShell" from dropdown

---

## Summary

The crash is caused by the PowerShell extension trying to manage too many language servers when multiple background processes run simultaneously. The solution is to:

1. ✅ Disable integrated console
2. ✅ Disable profile loading  
3. ✅ Limit concurrent processes
4. ✅ Use proper terminal configuration

Run `fix_powershell_crash.ps1` to apply all fixes automatically, then restart Cursor IDE.



