# EE Invoicing v2 - Deployment Instructions

## Quick Deployment to Railway

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/Zhihong0321/EE-inv-v2.git
git push -u origin main
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" -> "Deploy from GitHub repo"
3. Select repository `Zhihong0321/EE-inv-v2`
4. Click "Deploy Now"

### 3. Add PostgreSQL Service

1. Click "+ New Service" in Railway project
2. Select "Database" -> "PostgreSQL"
3. Railway will create PostgreSQL instance
4. Note: `DATABASE_URL` will be automatically linked to your app

### 4. Configure Environment Variables

Go to your Invoicing service -> "Variables" tab

Add these variables:

| Variable | Value | Description |
|----------|---------|-------------|
| JWT_SECRET_KEY | Click "Generate" | JWT signing secret |
| WHATSAPP_API_URL | `https://quote.atap.solar/api` | Your WhatsApp API |
| OTP_EXPIRE_SECONDS | `1800` | 30 minutes |
| OTP_LENGTH | `6` | 6-digit OTP |
| INVOICE_NUMBER_PREFIX | `INV` | Invoice prefix |
| INVOICE_NUMBER_LENGTH | `6` | Padding zeros |
| DEFAULT_SST_RATE | `8` | 8% SST |
| SHARE_LINK_EXPIRY_DAYS | `7` | 7 days |
| CORS_ORIGINS | `*` | All origins (update in production) |

**Important:** Railway will automatically link `DATABASE_URL` from PostgreSQL service.

### 5. Deploy

Railway will auto-redeploy after configuring variables.
Wait 2-3 minutes for deployment.

### 6. Access Application

Your app URL will be: `https://quote.atap.solar`

## First-Time Setup

### 1. Create Admin User

After deployment:

**Option A: Login via WhatsApp**
1. Visit `https://quote.atap.solar/admin/login`
2. Enter your WhatsApp number
3. Enter OTP received on WhatsApp
4. Login successfully

**Option B: Set Admin Role via Database**
1. Go to Railway -> PostgreSQL service
2. Click "Query" tab
3. Run this SQL (replace with your user ID or search by authentication):
```sql
UPDATE "user"
SET access_level = ARRAY['admin'],
    user_signed_up = true
WHERE id = 1; -- Or your user ID
```

### 2. Setup Default Template

1. Login as admin
2. Go to Templates (via API or admin UI)
3. Create template with:
   - Template Name: "Default"
   - Company Name: "Your Company Sdn Bhd"
   - Company Address: "Your Address"
   - SST Registration No: "ST00123456789"
   - Bank Details: (optional)
   - Check "Set as Default"

### 3. Test System

1. **Test Login:** Visit `/admin/login` and login with WhatsApp
2. **Test Create Customer:** Use API or admin UI
3. **Test Create Invoice:** Use API or admin UI
4. **Test Migration:** Use API endpoint `/api/v1/migration/migrate-old-invoices`

## Migration Guide

### Migrate Old Invoices

After deploying and setting up admin user:

```bash
# Get migration status
curl https://quote.atap.solar/api/v1/migration/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Migrate 100 invoices
curl -X POST https://quote.atap.solar/api/v1/migration/migrate-old-invoices?limit=100 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Repeat migration until all old invoices are processed.

### What Gets Migrated

- ✅ Invoice details (number, dates, amounts)
- ✅ Invoice items
- ✅ Customer info (from SEDA registration)
- ✅ Agent info (from old agent table)
- ✅ Package info (from old package table)
- ✅ Status mapping

## API Documentation

After deployment, visit:
- **Swagger UI:** `https://quote.atap.solar/docs`
- **ReDoc:** `https://quote.atap.solar/redoc`

## Quick API Test

### Test WhatsApp Login

```bash
# Step 1: Send OTP
curl -X POST https://quote.atap.solar/api/v1/auth/whatsapp/send-otp \
  -H "Content-Type: application/json" \
  -d '{"whatsapp_number": "60123456789"}'

# Step 2: Verify OTP (replace with actual OTP)
curl -X POST https://quote.atap.solar/api/v1/auth/whatsapp/verify \
  -H "Content-Type: application/json" \
  -d '{"whatsapp_number": "60123456789", "otp_code": "123456"}'

# Save the token for next requests
```

### Test Create Invoice

```bash
curl -X POST https://quote.atap.solar/api/v1/invoices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "customer_phone": "60123456789",
    "customer_name": "Test Customer",
    "items": [{
      "description": "Test Item",
      "qty": 1,
      "unit_price": 100.00
    }]
  }'
```

### Test Migration Status

```bash
curl https://quote.atap.solar/api/v1/migration/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Troubleshooting

### WhatsApp Service Not Ready

**Error:** "WhatsApp service not ready"

**Solution:**
1. Check your WhatsApp API server is running
2. Ensure WhatsApp account is authenticated (QR code scanned)
3. Verify WHATSAPP_API_URL is correct

### Database Connection Error

**Error:** "Could not connect to database"

**Solution:**
1. Check if PostgreSQL service is running
2. Verify DATABASE_URL is correctly linked
3. Check Railway service logs

### Migration Fails

**Error:** "Migration failed"

**Solution:**
1. Check if old invoices exist in database
2. Verify database schema is correct
3. Check migration service logs
4. Try smaller batch size (e.g., limit=10)

### CORS Errors

**Error:** "CORS policy blocked request"

**Solution:**
1. Add your domain to CORS_ORIGINS
2. Ensure it includes protocol (http:// or https://)
3. For local testing, use CORS_ORIGINS=*

## Security Checklist

- [ ] Changed JWT_SECRET_KEY to strong random value
- [ ] Set up monitoring on Railway
- [ ] Review and restrict CORS_ORIGINS in production
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS (Railway does this automatically)

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure environment variables
3. ✅ Create admin user
4. ✅ Setup default template
5. ✅ Test authentication
6. ✅ Test migration
7. ✅ Create first invoice
8. ✅ Generate share link and test

## Support

- Railway Dashboard: [railway.app](https://railway.app)
- API Docs: Visit `/docs` on your deployed app
- GitHub Repository: [github.com/Zhihong0321/EE-inv-v2](https://github.com/Zhihong0321/EE-inv-v2)

## License

MIT License - Free for commercial and personal use.
