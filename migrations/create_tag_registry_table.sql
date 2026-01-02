-- Migration: Create tag_registry table for user access control tags
-- Date: 2025-01-30
-- Description: Creates tag_registry table to store valid tags that can be assigned to users
--              Tags are categorized as: app, function, or department

CREATE TABLE IF NOT EXISTS tag_registry (
    id SERIAL PRIMARY KEY,
    tag VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL CHECK (category IN ('app', 'function', 'department')),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on tag for fast lookups
CREATE INDEX IF NOT EXISTS idx_tag_registry_tag ON tag_registry(tag);

-- Create index on category for filtering
CREATE INDEX IF NOT EXISTS idx_tag_registry_category ON tag_registry(category);

-- Add comment to table
COMMENT ON TABLE tag_registry IS 'Registry of valid tags that can be assigned to users for access control';
COMMENT ON COLUMN tag_registry.tag IS 'Unique tag string (e.g., "quote", "voucher", "package")';
COMMENT ON COLUMN tag_registry.category IS 'Tag category: app (application name), function (function name), or department (department name)';
COMMENT ON COLUMN tag_registry.description IS 'Optional description of what this tag allows';



