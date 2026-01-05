# Quick Fix: PowerShell Background Process Crashes in Cursor IDE

## The Problem
Cursor IDE crashes when running multiple PowerShell processes in the background with error: *"something running in the background is crashed, ask me to restart Cursor IDE"*

## Quick Solution (3 Steps)

### Step 1: Run the Fix Script
```powershell
.\fix_powershell_crash.ps1
```

### Step 2: Restart Cursor IDE
1. Close Cursor IDE completely
2. Check Task Manager - ensure no Cursor processes are running
3. Restart Cursor IDE

### Step 3: Test It
```powershell
.\quick_test_powershell_crash.ps1
```

If Cursor doesn't crash, you're fixed! ✅

---

## What the Fix Does

The fix script automatically:
- ✅ Disables PowerShell integrated console (major crash cause)
- ✅ Disables PowerShell profile loading (speeds up processes)
- ✅ Configures PowerShell 7 as default
- ✅ Sets proper terminal profiles
- ✅ Creates backup of your settings

---

## If It Still Crashes

### Option 1: Disable PowerShell Extension
1. `Ctrl + Shift + X` (Extensions)
2. Search "PowerShell"
3. Click gear → **Disable**
4. Restart Cursor

**Note**: You'll lose IntelliSense but terminal still works perfectly.

### Option 2: Limit Background Processes
Instead of spawning unlimited processes, limit to 3-5:

```powershell
$maxConcurrent = 3
$processes = @()

foreach ($item in $items) {
    # Wait if limit reached
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

## Diagnostic Tools

### Check Current Status
```powershell
.\diagnose_powershell_crash.ps1
```

### Full Test (More Aggressive)
```powershell
.\test_powershell_background_crash.ps1
```

---

## Prevention Tips

1. **Always clean up processes**
   ```powershell
   Get-Process pwsh | Where-Object { $_.Id -ne $PID } | Stop-Process
   ```

2. **Use background jobs instead of processes when possible**
   ```powershell
   Start-Job -ScriptBlock { ... }  # Better than Start-Process
   ```

3. **Limit concurrent processes to 3-5 maximum**

4. **Monitor resources before spawning**
   ```powershell
   $mem = (Get-Counter '\Memory\Available MBytes').CounterSamples[0].CookedValue
   if ($mem -lt 1000) {
       Write-Warning "Low memory - waiting..."
       Start-Sleep -Seconds 5
   }
   ```

---

## Files Created

- `fix_powershell_crash.ps1` - Applies all fixes automatically
- `diagnose_powershell_crash.ps1` - Diagnoses the problem
- `test_powershell_background_crash.ps1` - Full test (30 seconds)
- `quick_test_powershell_crash.ps1` - Quick test (12 seconds)
- `POWERSHELL_CRASH_DEBUG_GUIDE.md` - Full documentation

---

## Need More Help?

See `POWERSHELL_CRASH_DEBUG_GUIDE.md` for comprehensive troubleshooting.



