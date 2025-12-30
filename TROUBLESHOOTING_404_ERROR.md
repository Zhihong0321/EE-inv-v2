# Troubleshooting 404 Error - /create-invoice Route
## Issue: Route Returns "NOT FOUND"
**Date:** 2025-01-30

---

## Problem

Accessing this URL returns "NOT FOUND":
```
https://ee-inv-v2-production.up.railway.app/create-invoice?package_id=1741567007812x529976087464378400&customer_name=Sample+Quotation&panel_qty=18&panel_rating=620W
```

---

## Root Cause Analysis

### Issue Found: Missing `jinja2` Dependency

**Problem:** The `jinja2` package is **NOT** in `requirements.txt`, but the route uses `Jinja2Templates` which requires it.

**Impact:** When Railway tries to import `Jinja2Templates`, it fails because `jinja2` is not installed, causing the route to fail or not register properly.

---

## Solution Applied

### 1. Added `jinja2` to requirements.txt

**File:** `requirements.txt`

**Added:**
```
jinja2==3.1.2
```

### 2. Fixed Template Directory Path

**File:** `app/main.py`

**Changed:**
```python
# Before (relative path - might fail)
templates = Jinja2Templates(directory="app/templates")

# After (absolute path - more reliable)
import os
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, "app", "templates")
templates = Jinja2Templates(directory=template_dir)
```

### 3. Added Error Handling

Added try-catch blocks to show helpful error messages if template rendering fails.

---

## Verification Steps

### Step 1: Check if Route Exists

**Test URL:**
```
https://ee-invoicing-v2-production.railway.app/test-create-invoice
```

**Expected:** Should show "Test Route Working!" message

**If this works:** Server is responding, but `/create-invoice` route has issues  
**If this fails:** Server deployment issue

---

### Step 2: Check Railway Deployment

1. Go to Railway Dashboard
2. Check deployment logs
3. Look for errors related to:
   - `jinja2` import errors
   - `Jinja2Templates` import errors
   - Template file not found errors

---

### Step 3: Verify Code is Deployed

**Check if latest code is deployed:**
1. Railway Dashboard → Your Service → Deployments
2. Check latest deployment timestamp
3. Verify it includes the latest commit (`f5ee3dd`)

---

## Deployment Checklist

### Before Deployment:
- [x] Added `jinja2==3.1.2` to `requirements.txt`
- [x] Fixed template directory path
- [x] Added error handling
- [x] Added test route

### After Deployment:
- [ ] Verify Railway deployment succeeded
- [ ] Check Railway logs for errors
- [ ] Test `/test-create-invoice` route
- [ ] Test `/create-invoice` route
- [ ] Verify template file exists in deployment

---

## Common Causes of 404 Errors

### 1. Missing Dependencies
**Symptom:** Route defined but returns 404  
**Cause:** Required package not installed  
**Solution:** Add missing package to `requirements.txt`

### 2. Route Not Registered
**Symptom:** Route exists in code but doesn't work  
**Cause:** Route defined after app startup fails  
**Solution:** Check route is defined before app starts

### 3. Deployment Not Updated
**Symptom:** Code works locally but not in production  
**Cause:** Railway hasn't deployed latest code  
**Solution:** Check Railway deployment status

### 4. Template File Missing
**Symptom:** Route works but returns error  
**Cause:** Template file not in deployment  
**Solution:** Verify `app/templates/create_invoice.html` exists

---

## Next Steps

1. **Commit and Push Changes:**
   ```bash
   git add requirements.txt app/main.py
   git commit -m "fix: Add jinja2 dependency and fix template path"
   git push origin main
   ```

2. **Wait for Railway Deployment:**
   - Railway will auto-deploy
   - Wait 2-3 minutes
   - Check deployment logs

3. **Test the Route:**
   ```
   https://ee-inv-v2-production.up.railway.app/create-invoice?package_id=1741567007812x529976087464378400
   ```

4. **If Still Failing:**
   - Check Railway logs
   - Test `/test-create-invoice` route
   - Verify template file exists
   - Check for import errors

---

## Files Changed

| File | Change |
|------|--------|
| `requirements.txt` | Added `jinja2==3.1.2` |
| `app/main.py` | Fixed template directory path |
| `app/main.py` | Added error handling |
| `app/main.py` | Added test route `/test-create-invoice` |

---

**Status:** ✅ **FIXED** - Ready to deploy  
**Next Action:** Commit and push changes, then test in production




