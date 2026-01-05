# Database Migration Report
## Invoice Page UI Redesign Update
**Date:** 2025-01-30  
**Status:** ✅ NO NEW MIGRATIONS REQUIRED

---

## Summary

The invoice page UI redesign is **purely a frontend/display change** and does NOT require any database schema modifications. All changes are in:
- `app/utils/html_generator.py` - HTML/CSS styling only
- `app/api/public_invoice.py` - Added cache-busting headers (no DB changes)

---

## Existing Migration Status

### Migration Required: `item_type` Column

**Status:** ⚠️ **VERIFY IF ALREADY RUN ON PRODUCTION**

The invoice creation functionality (which the redesigned page displays) requires the `item_type` column in the `invoice_new_item` table. This migration was created earlier but may not have been executed on production yet.

**Migration File:** `migrations/add_item_type_to_invoice_item.sql`

**Purpose:**
- Support discount items (`item_type='discount'`)
- Support voucher items (`item_type='voucher'`)
- Support EPP fee items (`item_type='epp_fee'`)
- Distinguish package items (`item_type='package'`)

**Impact:**
- Required for invoice creation page to work correctly
- Required for displaying discounts, vouchers, and EPP fees as line items
- Non-destructive (adds column with default value)

---

## Verification Steps

### Step 1: Check if Migration Already Applied

Run this query on **PRODUCTION DATABASE**:

```sql
-- Check if item_type column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
AND column_name = 'item_type';
```

**Expected Results:**

**If Migration NOT Applied:**
- Query returns 0 rows
- **Action Required:** Run migration (see Step 2)

**If Migration Already Applied:**
- Query returns 1 row with:
  - `column_name`: `item_type`
  - `data_type`: `character varying` or `varchar`
  - `column_default`: `'package'::character varying`
- **Action Required:** None - migration already done ✅

---

### Step 2: Run Migration (If Needed)

**File:** `migrations/add_item_type_to_invoice_item.sql`

**SQL Script:**
```sql
-- Migration: Add item_type to invoice_new_item table
-- Date: 2025-01-30
-- Purpose: Support creating discount and voucher items with negative prices

-- Check if column exists first (to avoid errors on repeated runs)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'invoice_new_item'
        AND column_name = 'item_type'
    ) THEN
        ALTER TABLE invoice_new_item ADD COLUMN item_type VARCHAR(20) DEFAULT 'package';
    END IF;
END $$;

-- Update existing package items to have item_type
UPDATE invoice_new_item SET item_type = 'package' WHERE item_type IS NULL;

-- Add comment
COMMENT ON COLUMN invoice_new_item.item_type IS 'Item type: package, discount, voucher, adjustment, addon, epp_fee';
```

**How to Run:**

1. **Via Railway Console:**
   - Go to Railway Dashboard
   - Select PostgreSQL service
   - Click "Console" tab
   - Copy/paste SQL script
   - Execute

2. **Via psql:**
   ```bash
   psql -h <host> -U <user> -d <database> -f migrations/add_item_type_to_invoice_item.sql
   ```

3. **Via Database GUI (DBeaver/pgAdmin):**
   - Connect to production database
   - Open SQL editor
   - Open file: `migrations/add_item_type_to_invoice_item.sql`
   - Execute script

---

### Step 3: Verify Migration Success

After running migration, verify:

```sql
-- 1. Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
AND column_name = 'item_type';

-- Expected: 1 row returned

-- 2. Check existing records updated
SELECT 
    bubble_id,
    description,
    item_type,
    unit_price,
    total_price
FROM invoice_new_item
ORDER BY created_at DESC
LIMIT 10;

-- Expected: All existing records should have item_type = 'package'
```

---

## Database Schema Reference

### Tables Used (No Changes Required)

#### `invoice_new`
- **Status:** ✅ No changes needed
- All columns already exist
- Used for storing invoice data

#### `invoice_new_item`
- **Status:** ⚠️ Requires `item_type` column (see migration above)
- Columns:
  - `id` (PK)
  - `bubble_id` (Unique)
  - `invoice_id` (FK to invoice_new.bubble_id)
  - `description` (Text)
  - `qty` (Numeric)
  - `unit_price` (Numeric) - Can be negative for discounts/vouchers
  - `total_price` (Numeric) - Can be negative for discounts/vouchers
  - `item_type` (VARCHAR) - **REQUIRED** - Values: `package`, `discount`, `voucher`, `epp_fee`, `adjustment`, `addon`
  - `sort_order` (Integer)
  - `created_at` (DateTime)

#### `invoice_template`
- **Status:** ✅ No changes needed
- Used for company branding/info

#### `customer`
- **Status:** ✅ No changes needed
- Used for customer data

#### `package`
- **Status:** ✅ No changes needed
- Used for solar package data

---

## Code Changes (No Database Impact)

These are Python/HTML changes only - **NO DATABASE MIGRATIONS NEEDED**:

| File | Change Type | Description |
|------|-------------|-------------|
| `app/utils/html_generator.py` | HTML/CSS | Redesigned invoice page UI (minimalist, mobile-optimized) |
| `app/api/public_invoice.py` | HTTP Headers | Added cache-busting headers |
| `app/api/demo.py` | HTTP Headers | Added cache-busting headers |

---

## Production Deployment Checklist

### Pre-Deployment

- [ ] Verify `item_type` column exists in production `invoice_new_item` table
- [ ] If column doesn't exist, run migration script
- [ ] Test invoice creation with discounts/vouchers/EPP fees
- [ ] Verify invoice display shows correct item types

### Deployment Steps

1. **Code Deployment:**
   - Deploy updated Python files (HTML generator, API endpoints)
   - No database changes required for UI redesign

2. **Database Migration (If Needed):**
   - Run `add_item_type_to_invoice_item.sql` if not already applied
   - Verify migration success

3. **Post-Deployment Verification:**
   - Create test invoice with discount
   - Create test invoice with voucher
   - Create test invoice with EPP fee
   - Verify invoice page displays correctly (new design)
   - Verify items show correct types and formatting

---

## Rollback Plan

### If Migration Needs Rollback:

```sql
-- Step 1: Drop item_type column
ALTER TABLE invoice_new_item DROP COLUMN IF EXISTS item_type;

-- Step 2: Verify column removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'invoice_new_item'
AND column_name = 'item_type';

-- Expected: No results (column removed)
```

**Note:** Rolling back the migration will break invoice creation functionality that uses discounts/vouchers/EPP fees.

---

## Risk Assessment

### Migration Risk: **LOW**

- ✅ Non-destructive (adds column with default)
- ✅ Idempotent (checks if column exists)
- ✅ Backward compatible (default value for existing records)
- ✅ No downtime required (~1 second execution time)

### Code Changes Risk: **VERY LOW**

- ✅ Frontend-only changes (HTML/CSS)
- ✅ No database schema changes
- ✅ No breaking API changes
- ✅ Cache-busting headers prevent stale content

---

## Summary

### ✅ NO NEW MIGRATIONS REQUIRED

The invoice page UI redesign is a **frontend-only change** and does not require any database migrations.

### ⚠️ ONE EXISTING MIGRATION TO VERIFY

The `item_type` column migration (`add_item_type_to_invoice_item.sql`) must be verified/run on production if not already applied. This migration is required for the invoice creation functionality (not specifically for the UI redesign, but for the features the UI displays).

**Action Items:**
1. ✅ Verify `item_type` column exists in production
2. ✅ Run migration if column doesn't exist
3. ✅ Deploy code changes (no DB changes needed)
4. ✅ Test invoice creation and display

---

**Report Generated:** 2025-01-30  
**Next Review:** After production deployment verification















