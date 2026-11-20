-- Versioned Transport Data records. Only rows in the current published set are
-- read by the public API; Slice 2 owns draft creation and publication writes.
CREATE TABLE IF NOT EXISTS transport_change_sets (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired', 'expired')),
    version INTEGER NOT NULL CHECK (version > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS published_change_sets (
    change_set_id UUID PRIMARY KEY REFERENCES transport_change_sets(id),
    published_at TIMESTAMPTZ NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE UNIQUE INDEX IF NOT EXISTS published_change_sets_one_current_idx
    ON published_change_sets (is_current) WHERE is_current;

CREATE TABLE IF NOT EXISTS transport_routes (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    route_code TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    direction TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired')),
    version INTEGER NOT NULL CHECK (version > 0),
    UNIQUE (change_set_id, route_code)
);

CREATE TABLE IF NOT EXISTS transport_buses (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    bus_identifier TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired')),
    version INTEGER NOT NULL CHECK (version > 0),
    UNIQUE (change_set_id, bus_identifier)
);

CREATE TABLE IF NOT EXISTS transport_assignments (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    route_code TEXT NOT NULL,
    bus_identifier TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired')),
    version INTEGER NOT NULL CHECK (version > 0),
    UNIQUE (change_set_id, route_code, bus_identifier)
);

CREATE TABLE IF NOT EXISTS transport_weekly_departures (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 0 AND 6),
    local_departure_time TIME NOT NULL,
    route_code TEXT NOT NULL,
    bus_identifier TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired')),
    version INTEGER NOT NULL CHECK (version > 0),
    UNIQUE (change_set_id, weekday, route_code, bus_identifier, local_departure_time)
);

CREATE TABLE IF NOT EXISTS transport_date_overrides (
    id UUID PRIMARY KEY,
    change_set_id UUID NOT NULL REFERENCES transport_change_sets(id),
    service_date DATE NOT NULL,
    is_full_day_no_service BOOLEAN NOT NULL DEFAULT FALSE,
    operation TEXT CHECK (operation IN ('add', 'remove')),
    route_code TEXT,
    bus_identifier TEXT,
    local_departure_time TIME,
    status TEXT NOT NULL CHECK (status IN ('draft', 'published', 'retired')),
    version INTEGER NOT NULL CHECK (version > 0),
    CHECK (
        (is_full_day_no_service = TRUE AND operation IS NULL
         AND route_code IS NULL AND bus_identifier IS NULL
         AND local_departure_time IS NULL)
        OR
        (is_full_day_no_service = FALSE AND operation IS NOT NULL
         AND route_code IS NOT NULL AND bus_identifier IS NOT NULL
         AND local_departure_time IS NOT NULL)
    )
);
CREATE INDEX IF NOT EXISTS transport_published_snapshot_idx
    ON transport_weekly_departures (change_set_id, status, weekday);
