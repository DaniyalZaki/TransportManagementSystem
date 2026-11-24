ALTER TABLE announcements
    DROP COLUMN IF EXISTS is_operational,
    DROP COLUMN IF EXISTS confirmed_at;
