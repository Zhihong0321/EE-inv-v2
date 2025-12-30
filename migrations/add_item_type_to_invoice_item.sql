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
COMMENT ON COLUMN invoice_new_item.item_type IS 'Item type: package, discount, voucher, adjustment, addon';
