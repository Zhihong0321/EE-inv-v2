# FINALIZED MIGRATION LIST
# EE Invoicing System - Invoice Creation Feature
# Date: 2025-01-30
# Target: Production Database

---

## Summary

Total Migrations: 1

Database Type: PostgreSQL
Migration Files: migrations/add_item_type_to_invoice_item.sql

IMPORTANT: This migration has NOT been executed yet.
SQL script is ready to run on production database.

---

## MIGRATION #1: Add item_type to invoice_new_item

Purpose:
- Support creating discount and voucher items as visible invoice line items
- Distinguish between package, discount, voucher, adjustment, addon items

Table: invoice_new_item

Action: Add column

### Changes Made

Column | Type | Default | Description
item_type | VARCHAR(20) | package | Item type identifier

Possible Values:
- package - Solar package items
- discount - Discount items (negative price)
- voucher - Voucher items (negative price)
- adjustment - Price adjustments (future)
- addon - Additional items (future)

### SQL Script

File: migrations/add_item_type_to_invoice_item.sql

-- Migration: Add item_type to invoice_new_item table
-- Date: 2025-01-30
-- Purpose: Support creating discount and voucher items with negative prices

-- Check if column exists first (to avoid errors on repeated runs)
DO BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = invoice_new_item
        AND column_name = item_type
    ) THEN
        ALTER TABLE invoice_new_item ADD COLUMN item_type VARCHAR(20) DEFAULT package;
    END IF;
END ;

-- Update existing package items to have item_type
UPDATE invoice_new_item SET item_type = package WHERE item_type IS NULL;

-- Add comment
COMMENT ON COLUMN invoice_new_item.item_type IS Item type: package, discount, voucher, adjustment, addon;

### Verification Queries

After running migration, verify:

-- 1. Check column exists
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = invoice_new_item
AND column_name = item_type;

-- Expected:
-- column_name | data_type    | column_default
---------------|--------------|---------------
-- item_type   | character varying| package::character varying


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

-- Expected:
-- All existing records should have item_type = package


-- 3. Test with sample data (optional)
INSERT INTO invoice_new_item (
    bubble_id, invoice_id, description, qty, unit_price, total_price, item_type
) VALUES (
    test_item_001,
    test_invoice_id,
    Test Discount (10%),
    1,
    -100.00,
    -100.00,
    discount
);

-- Verify discount item
SELECT * FROM invoice_new_item WHERE bubble_id = test_item_001;

-- Clean up test data
DELETE FROM invoice_new_item WHERE bubble_id = test_item_001;

---

## Code Changes (Not Database Migrations)

These are Python code changes, NOT SQL migrations:

File | Change | Type
app/models/invoice.py | Added item_type column to model | Python
app/repositories/invoice_repo.py | Updated create_on_the_fly() to create discount/voucher items | Python
app/repositories/invoice_repo.py | Updated _calculate_invoice_totals() to handle negative prices | Python
app/utils/html_generator.py | Updated to show negative prices in red | Python

---

## Rollback Plan (If Needed)

To rollback Migration #1:

-- Step 1: Drop item_type column
ALTER TABLE invoice_new_item DROP COLUMN IF EXISTS item_type;

-- Step 2: Verify column removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = invoice_new_item
AND column_name = item_type;

-- Expected: No results (column removed)

---

## Impact Analysis

### Tables Affected
- invoice_new_item (1 table)

### Rows Affected
- Depends on existing invoice_new_item records
- Migration sets default package for all existing records

### Downtime Required
- ~1 second (single ALTER TABLE statement)
- Safe to run during business hours

### Risk Level
- LOW
- Non-destructive (adds column with default)
- Idempotent (checks if column exists)

---

## Production Migration Steps

### Step 1: Backup Database (RECOMMENDED)

-- Create backup table
CREATE TABLE invoice_new_item_backup_2025_01_30 AS
SELECT * FROM invoice_new_item;

-- Verify backup count
SELECT COUNT(*) AS backup_count FROM invoice_new_item_backup_2025_01_30;

### Step 2: Run Migration

Option A: Using psql (Command Line)
psql -h <host> -U <user> -d <database> -f migrations/add_item_type_to_invoice_item.sql

Option B: Using Railway Console
1. Go to Railway Dashboard
2. Select PostgreSQL service
3. Click Console tab
4. Copy and paste SQL script
5. Click Run or press Enter

Option C: Using DBeaver/pgAdmin GUI
1. Connect to production database
2. Open SQL editor
3. Open file: migrations/add_item_type_to_invoice_item.sql
4. Execute script

### Step 3: Verify Migration

-- Verify column exists
SELECT column_name FROM information_schema.columns
WHERE table_name = invoice_new_item AND column_name = item_type;

-- Expected: 1 row with item_type

### Step 4: Test Invoice Creation

-- Create test invoice (via API or UI)
-- Verify items created with item_type

SELECT 
    i.invoice_number,
    ii.description,
    ii.unit_price,
    ii.total_price,
    ii.item_type
FROM invoice_new i
LEFT JOIN invoice_new_item ii ON i.bubble_id = ii.invoice_id
ORDER BY i.created_at DESC
LIMIT 5;

-- Expected results:
-- discount/voucher items should have:
-- - item_type = discount or voucher
-- - unit_price < 0 (negative)
-- - total_price < 0 (negative)

### Step 5: Clean Up (Optional)

-- Remove backup table after successful testing (7 days later)
DROP TABLE IF EXISTS invoice_new_item_backup_2025_01_30;

---

## Pre-Migration Checklist

Before running on production:

- [ ] Database backup created
- [ ] Migration script reviewed
- [ ] Test database updated successfully
- [ ] Code changes deployed (Python files)
- [ ] Application restarted
- [ ] Test invoice created with discount
- [ ] Test invoice created with voucher
- [ ] Verify invoice display (red negative prices)
- [ ] Verify totals calculation correct

---

## Notes

Migration ID: MIG_2025_01_30_001
Status: Finalized, Ready to Execute
Execution Date: TBD (When you run on production DB)
Executed By: [Your Name]
Database: Production PostgreSQL

IMPORTANT REMINDER:
- This migration has NOT been executed yet on any database
- Run on test database first to verify
- Then run on production database
- Remember to backup production database before migration
