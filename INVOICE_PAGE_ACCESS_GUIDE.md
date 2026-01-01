# Invoice Creation Page - Access Guide
## Where to Access the Invoice Creation Page
**Last Updated:** 2025-01-30

---

## Quick Access URLs

### 🏠 Localhost (Development/Testing)

**Base URL:**
```
http://localhost:8080/create-invoice
```

**With Parameters Example:**
```
http://localhost:8080/create-invoice?package_id=1703833647950x572894707690242050&discount_given=500
```

**How to Access:**
1. Start local server: Run `start_server.bat` or `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080`
2. Wait for server to start (you'll see "Application startup complete")
3. Open browser and go to: `http://localhost:8080/create-invoice`

---

### 🌐 Production (Railway Deployment)

**Base URL Format:**
```
https://quote.atap.solar/create-invoice
```

**How to Find Your Production URL:**

#### Method 1: Railway Dashboard
1. Go to [railway.app](https://railway.app)
2. Login to your account
3. Select your project
4. Click on your **Invoicing Service** (FastAPI app)
5. Go to **Settings** tab
6. Find **Public Domain** section
7. Copy the URL (e.g., `https://quote.atap.solar`)

#### Method 2: Railway Service Settings
1. Railway Dashboard → Your Project
2. Click on your service
3. Look for **"Generate Domain"** or **"Public Domain"** button
4. Copy the generated domain
5. Your full URL: `https://quote.atap.solar/create-invoice`

**Example Production URLs:**
```
https://quote.atap.solar/create-invoice
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050
```

---

## Access Methods

### Method 1: Direct Browser Access

**Steps:**
1. Open web browser (Chrome, Firefox, Safari, Edge)
2. Type or paste the URL in address bar
3. Press Enter
4. Page will load

**Example:**
```
Browser → Address Bar → https://quote.atap.solar/create-invoice?package_id=xxx
```

---

### Method 2: From Admin Dashboard

**If you have admin access:**
1. Login to admin dashboard: `https://quote.atap.solar/admin/login`
2. After login, you can navigate to invoice creation
3. Or directly access: `https://quote.atap.solar/create-invoice`

---

### Method 3: Via Link (Sales Team)

**Sales team generates link and shares:**
1. Sales team creates link with parameters
2. Link shared via WhatsApp, email, or messaging app
3. Sales agent clicks link
4. Browser opens invoice creation page

**Example Link:**
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&discount_given=500&customer_name=John%20Doe
```

---

### Method 4: Mobile Browser

**Works on mobile devices:**
1. Open mobile browser (Chrome, Safari, etc.)
2. Type or paste URL
3. Page is mobile-optimized and responsive

**Mobile URL Example:**
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050
```

---

## Route Information

### Endpoint Details

| Property | Value |
|----------|-------|
| **Route** | `/create-invoice` |
| **Method** | `GET` |
| **Response Type** | `HTMLResponse` |
| **Authentication** | Optional (redirects to login if needed) |
| **Mobile Support** | ✅ Yes (responsive design) |

### Full Route Path

**Localhost:**
```
http://localhost:8080/create-invoice
```

**Production:**
```
https://quote.atap.solar/create-invoice
```

---

## Finding Your Production Domain

### Step-by-Step Guide

1. **Login to Railway**
   - Go to: https://railway.app
   - Login with your credentials

2. **Navigate to Your Project**
   - Click on your project name
   - You'll see your services listed

3. **Select Your Invoicing Service**
   - Click on the FastAPI/Invoicing service
   - This is the service running your app

4. **Check Settings**
   - Click **Settings** tab
   - Look for **"Public Domain"** or **"Networking"** section

5. **Generate/Copy Domain**
   - If no domain exists, click **"Generate Domain"**
   - Copy the domain (e.g., `quote.atap.solar-xxxx`)
   - Your full URL: `https://quote.atap.solar`

6. **Access Invoice Page**
   - Add `/create-invoice` to the domain
   - Full URL: `https://quote.atap.solar/create-invoice`

---

## Access Scenarios

### Scenario 1: Testing Locally

**URL:**
```
http://localhost:8080/create-invoice
```

**Steps:**
1. Ensure server is running (`start_server.bat`)
2. Open browser
3. Navigate to URL above
4. Test with parameters

---

### Scenario 2: Production Access

**URL:**
```
https://quote.atap.solar/create-invoice
```

**Steps:**
1. Find your Railway domain (see above)
2. Replace `your-domain` with actual domain
3. Open in browser
4. Access invoice creation page

---

### Scenario 3: Sales Team Sharing Link

**URL Format:**
```
https://quote.atap.solar/create-invoice?package_id={id}&discount_given={amount}
```

**Steps:**
1. Sales team generates link with parameters
2. Shares link via WhatsApp/email
3. Sales agent clicks link
4. Browser opens invoice creation page
5. Form is pre-filled with parameters

---

## Common Access Issues

### Issue 1: "Cannot Access Page"

**Symptoms:**
- Browser shows "This site can't be reached"
- Connection timeout

**Solutions:**
- ✅ Check if server is running (localhost)
- ✅ Verify Railway deployment is active (production)
- ✅ Check Railway service status
- ✅ Verify domain is correct

---

### Issue 2: "404 Not Found"

**Symptoms:**
- Page shows "404 Not Found"
- Route not found error

**Solutions:**
- ✅ Verify route: `/create-invoice` (not `/createinvoice` or `/create_invoice`)
- ✅ Check if code is deployed (production)
- ✅ Verify server is running (localhost)
- ✅ Check Railway deployment logs

---

### Issue 3: Redirects to Login

**Symptoms:**
- Page redirects to `/admin/login`
- "Please login" message

**Solutions:**
- ✅ This is normal behavior
- ✅ Login with WhatsApp OTP
- ✅ After login, you'll be redirected back
- ✅ Or access directly: `/create-invoice` (works without login)

---

### Issue 4: "Package Not Found"

**Symptoms:**
- Error: "Package with ID 'xxx' not found"
- Form shows error message

**Solutions:**
- ✅ Verify `package_id` is correct
- ✅ Check package exists in database
- ✅ Use valid package_id format
- ✅ Form still allows manual entry

---

## Quick Reference

### Localhost Access
```
http://localhost:8080/create-invoice
```

### Production Access
```
https://quote.atap.solar/create-invoice
```

### With Parameters (Example)
```
https://quote.atap.solar/create-invoice?package_id=1703833647950x572894707690242050&discount_given=500
```

---

## Testing Access

### Test 1: Basic Access

**URL:**
```
http://localhost:8080/create-invoice
```

**Expected:**
- Page loads
- Shows invoice creation form
- Can enter package_id manually

---

### Test 2: With Package ID

**URL:**
```
http://localhost:8080/create-invoice?package_id=1703833647950x572894707690242050
```

**Expected:**
- Page loads
- Package details pre-filled
- Form shows package information

---

### Test 3: Complete Parameters

**URL:**
```
http://localhost:8080/create-invoice?package_id=1703833647950x572894707690242050&discount_given=500&customer_name=Test%20Customer
```

**Expected:**
- Page loads
- All fields pre-filled
- Ready to submit

---

## Security Notes

### Public Access
- ✅ Page is publicly accessible (no login required)
- ✅ Can be accessed via direct URL
- ✅ Can be shared via links

### Authentication
- ⚠️ Invoice creation requires login (when submitting)
- ⚠️ Will redirect to login if not authenticated
- ✅ After login, redirects back to invoice page

---

## Related Documentation

- **Link Generation Guide:** [SALES_TEAM_INVOICE_LINK_GUIDE.md](./SALES_TEAM_INVOICE_LINK_GUIDE.md)
- **Quick Reference:** [INVOICE_LINK_QUICK_REFERENCE.md](./INVOICE_LINK_QUICK_REFERENCE.md)
- **Deployment Guide:** [DEPLOYMENT_INSTRUCTIONS.md](./DEPLOYMENT_INSTRUCTIONS.md)

---

## Summary

| Environment | Base URL | Full Example |
|-------------|----------|--------------|
| **Localhost** | `http://localhost:8080/create-invoice` | `http://localhost:8080/create-invoice?package_id=xxx` |
| **Production** | `https://quote.atap.solar/create-invoice` | `https://quote.atap.solar/create-invoice?package_id=xxx` |

**To Find Production Domain:**
1. Railway Dashboard → Your Project → Your Service → Settings → Public Domain

**Access Method:**
- Direct browser URL
- Click shared link
- Mobile browser
- Any web browser

---

**Last Updated:** 2025-01-30  
**Route:** `/create-invoice` (GET)  
**Status:** ✅ Publicly accessible




