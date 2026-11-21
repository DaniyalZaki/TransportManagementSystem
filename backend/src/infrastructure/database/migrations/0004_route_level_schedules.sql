-- A weekly timetable row now schedules all buses assigned to its route.
-- The migration runner reapplies idempotent files, so change old weekday data
-- only while the original 0–6 constraint is still installed.
DO $$
DECLARE
    weekday_constraint TEXT;
BEGIN
    SELECT pg_get_constraintdef(c.oid)
    INTO weekday_constraint
    FROM pg_constraint c
    WHERE c.conrelid = 'transport_weekly_departures'::regclass
      AND c.conname = 'transport_weekly_departures_weekday_check';

    IF weekday_constraint LIKE '%weekday >= 0%' THEN
        ALTER TABLE transport_weekly_departures
            DROP CONSTRAINT transport_weekly_departures_weekday_check;
        UPDATE transport_weekly_departures
        SET weekday = weekday + 1
        WHERE weekday BETWEEN 0 AND 6;
        ALTER TABLE transport_weekly_departures
            ADD CONSTRAINT transport_weekly_departures_weekday_check
            CHECK (weekday BETWEEN 1 AND 7);
    END IF;
END $$;

-- Normalize the legacy direction labels used by the initial local dataset.
UPDATE transport_routes
SET direction = CASE upper(direction)
    WHEN 'INBOUND' THEN 'PICK-UP'
    WHEN 'OUTBOUND' THEN 'RETURN'
    ELSE direction
END
WHERE upper(direction) IN ('INBOUND', 'OUTBOUND');
