-- Create user matching Auth Hub's userId=1
-- Run this in Railway PostgreSQL Query tab

INSERT INTO auth_user (
    user_id,
    whatsapp_number,
    whatsapp_formatted,
    name,
    role,
    active,
    app_permissions,
    created_at
) VALUES (
    '1',  -- Match Auth Hub's userId
    '1121000099',  -- From token payload
    '1121000099',
    'GAN ZHI HONG',  -- From token payload
    'admin',  -- isAdmin: true in token
    true,
    ARRAY['all'],  -- Admin permissions
    NOW()
)
ON CONFLICT (user_id) DO UPDATE SET
    whatsapp_number = EXCLUDED.whatsapp_number,
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    active = true;

