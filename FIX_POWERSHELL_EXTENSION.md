# Fix PowerShell Extension Issues in Cursor IDE

## Problem
After installing the PowerShell extension, PowerShell becomes unusable in Cursor IDE.

## Solution Applied

### ✅ Configuration Files Created

1. **Workspace Settings** (`.vscode/settings.json`)
   - Forces PowerShell 7 as default terminal
   - Configures PowerShell extension to use PowerShell 7
   - Sets proper terminal profiles

2. **User Settings** (`%APPDATA%\Cursor\User\settings.json`)
   - Global Cursor IDE settings updated
   - PowerShell extension configured to use PowerShell 7

### 🔧 Steps to Fix (If Still Not Working)

#### Step 1: Restart Cursor IDE
1. **Completely close Cursor IDE** (not just the window)
2. Check Task Manager to ensure no Cursor processes are running
3. Restart Cursor IDE

#### Step 2: Reset Terminal
1. Open a new terminal: `Ctrl + `` (backtick) or `Terminal > New Terminal`
2. If it opens Windows PowerShell 5.1, click the dropdown arrow next to `+` in terminal
3. Select **"PowerShell"** (should show PowerShell 7.5.4)

#### Step 3: Check PowerShell Extension Output
1. Open Output panel: `View > Output` or `Ctrl + Shift + U`
2. In the dropdown, select **"PowerShell"**
3. Look for any error messages
4. Common errors:
   - "PowerShell not found" → Extension can't find PowerShell 7
   - "Profile loading failed" → Profile script has errors
   - "Execution policy" → Need to set execution policy

#### Step 4: Disable Problematic Extension Features
If PowerShell extension is causing issues, you can disable specific features:

**Option A: Disable Integrated Console**
Add to Cursor settings:
```json
{
  "powershell.integratedConsole.showOnStartup": false,
  "powershell.enableProfileLoading": false
}
```

**Option B: Temporarily Disable Extension**
1. Go to Extensions: `Ctrl + Shift + X`
2. Search for "PowerShell"
3. Click the gear icon → "Disable"
4. Restart Cursor
5. Test if PowerShell works without extension
6. If it works, re-enable and configure properly

#### Step 5: Fix Execution Policy (If Needed)
If you see execution policy errors:
```powershell
# Run in Administrator PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 6: Check PowerShell Profile
The extension might be trying to load a profile with errors:
```powershell
# Check if profile exists and has errors
Test-Path $PROFILE
Get-Content $PROFILE -ErrorAction SilentlyContinue
```

If profile has errors, you can:
- Fix the errors in the profile
- Or disable profile loading: `"powershell.enableProfileLoading": false`

### 🎯 Quick Fixes

#### Fix 1: Force Terminal to Use PowerShell 7
1. Open Command Palette: `Ctrl + Shift + P`
2. Type: `Terminal: Select Default Profile`
3. Choose: **"PowerShell"** (should point to PowerShell 7)

#### Fix 2: Manually Set Terminal
1. Open terminal dropdown (next to `+`)
2. Click `Select Default Profile`
3. Choose **"PowerShell"**

#### Fix 3: Use Direct Path
If nothing works, create a custom terminal profile:
1. Open Settings: `Ctrl + ,`
2. Search: `terminal.integrated.profiles.windows`
3. Click "Edit in settings.json"
4. Ensure it has:
```json
"PowerShell": {
  "path": "D:\\Program Files\\PowerShell\\7\\pwsh.exe",
  "args": ["-NoLogo"]
}
```

### 🔍 Diagnostic Tools

Run the diagnostic script:
```powershell
.\debug_powershell_extension.ps1
```

This will check:
- PowerShell 7 installation
- PATH configuration
- Cursor settings
- Extension configuration
- Common issues

### 📋 Current Configuration

**PowerShell 7 Path:** `D:\Program Files\PowerShell\7\pwsh.exe`
**Version:** PowerShell 7.5.4
**Extension:** ms-vscode.powershell-2025.4.0-universal

**Settings Applied:**
- ✅ Terminal default profile: PowerShell 7
- ✅ PowerShell extension default version: PowerShell 7
- ✅ Terminal automation profile: PowerShell 7
- ✅ Profile loading: Enabled
- ✅ Integrated console: Disabled (to prevent conflicts)

### 🚨 If Nothing Works

1. **Uninstall and Reinstall PowerShell Extension**
   - Extensions → PowerShell → Uninstall
   - Restart Cursor
   - Reinstall extension
   - Restart again

2. **Reset Cursor Settings**
   - Close Cursor
   - Backup: `%APPDATA%\Cursor\User\settings.json`
   - Delete or rename settings.json
   - Restart Cursor
   - Re-apply settings from `.vscode/settings.json`

3. **Use PowerShell 7 Directly**
   - Open external PowerShell 7: `Win + X` → Windows Terminal
   - Or create a shortcut to: `D:\Program Files\PowerShell\7\pwsh.exe`

### ✅ Verification

After applying fixes, verify:
```powershell
# In Cursor terminal, run:
pwsh --version
# Should show: PowerShell 7.5.4

$PSVersionTable.PSVersion
# Should show: 7.5.4
```

### 📞 Still Having Issues?

Check:
1. Cursor Output panel → PowerShell dropdown for errors
2. Windows Event Viewer for PowerShell errors
3. Cursor Developer Tools: `Help > Toggle Developer Tools` → Console tab




