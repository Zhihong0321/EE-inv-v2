# Stop PowerShell Extension Installation Prompt

## Why Cursor Keeps Asking

Cursor IDE automatically detects PowerShell files (`.ps1`) in your workspace and recommends the PowerShell extension. You have **8 PowerShell scripts** in this project, so Cursor keeps prompting you.

**This is normal behavior** - Cursor is trying to be helpful by suggesting relevant extensions.

## Quick Fix (3 Steps)

### Step 1: Run the Fix Script
```powershell
.\disable_powershell_extension_prompt.ps1
```

### Step 2: Restart Cursor IDE
- Close Cursor completely
- Restart Cursor

### Step 3: Verify
- The prompt should no longer appear ✅

---

## What the Script Does

The script creates/updates three configuration files:

1. **`.vscode/extensions.json`**
   - Marks PowerShell extension as "unwanted recommendation"
   - Tells Cursor: "Don't recommend this extension for this workspace"

2. **`.vscode/settings.json`** (workspace settings)
   - Sets `extensions.showRecommendationsOnlyOnDemand = true`
   - Extension recommendations only show when you explicitly request them

3. **User Settings** (`%APPDATA%\Cursor\User\settings.json`)
   - Applies the same setting globally
   - Stops prompts in all workspaces

---

## Manual Fix (If Script Doesn't Work)

### Option 1: Create `.vscode/extensions.json` Manually

Create `.vscode/extensions.json` with:
```json
{
  "recommendations": [],
  "unwantedRecommendations": [
    "ms-vscode.PowerShell"
  ]
}
```

### Option 2: Disable Extension Recommendations Globally

1. Open Settings: `Ctrl + ,`
2. Search: `extensions.showRecommendationsOnlyOnDemand`
3. Check the box: **"Show Recommendations Only On Demand"**
4. Restart Cursor

### Option 3: Install and Disable Extension

If you want to stop the prompt but keep the option available:

1. Install the extension: `Ctrl + Shift + X` → Search "PowerShell" → Install
2. Immediately disable it: Click gear icon → **Disable**
3. Restart Cursor

This way, Cursor knows you've "handled" the extension and won't prompt again.

---

## Why You Don't Need the Extension

The PowerShell extension provides:
- ❌ IntelliSense (code completion)
- ❌ Script debugging
- ❌ Script analysis
- ❌ Advanced syntax highlighting

**But you already have:**
- ✅ PowerShell terminal (fully functional)
- ✅ Running PowerShell commands
- ✅ Running PowerShell scripts
- ✅ Basic syntax highlighting

**For terminal usage, the extension is optional!**

---

## If You Change Your Mind Later

If you decide you want the PowerShell extension later:

1. Go to Extensions: `Ctrl + Shift + X`
2. Search for "PowerShell"
3. Install it manually
4. The prompt won't appear again because you've explicitly installed it

---

## Files Created

- `disable_powershell_extension_prompt.ps1` - Script to disable the prompt
- `.vscode/extensions.json` - Marks PowerShell as unwanted
- `.vscode/settings.json` - Workspace settings (updated)
- User settings - Global settings (updated)

---

## Summary

**Problem**: Cursor detects 8 PowerShell files and keeps recommending the extension.

**Solution**: Run `.\disable_powershell_extension_prompt.ps1` and restart Cursor.

**Result**: No more prompts! ✅


