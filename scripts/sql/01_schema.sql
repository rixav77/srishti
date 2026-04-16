-- =============================================================================
-- Srishti — Supabase (PostgreSQL) Schema
-- Run this once in the Supabase SQL Editor to initialise all tables.
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. EVENTS
-- =============================================================================
CREATE TABLE IF NOT EXISTS events (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identity
    name                 TEXT NOT NULL,
    domain               TEXT NOT NULL CHECK (domain IN ('conference', 'music_festival', 'sporting_event')),
    category             TEXT,
    subcategory          TEXT,
    description          TEXT,

    -- Schedule
    start_date           DATE,
    end_date             DATE,
    year                 INTEGER GENERATED ALWAYS AS (EXTRACT(YEAR FROM start_date)::INTEGER) STORED,

    -- Location
    city                 TEXT,
    country              TEXT,
    continent            TEXT,
    venue_name           TEXT,

    -- Audience
    estimated_attendance INTEGER,
    actual_attendance    INTEGER,

    -- Pricing
    ticket_price_min     NUMERIC(12, 2),
    ticket_price_max     NUMERIC(12, 2),
    currency             TEXT DEFAULT 'USD',

    -- Links
    website_url          TEXT,

    -- Provenance
    data_source          TEXT,
    extraction_method    TEXT,
    scraped_at           TIMESTAMPTZ DEFAULT NOW(),

    -- Full raw payload kept for reference / future enrichment
    raw_data             JSONB DEFAULT '{}'::JSONB,

    -- Enrichment metadata (method applied, fields added)
    enrichment           JSONB DEFAULT '{}'::JSONB,

    created_at           TIMESTAMPTZ DEFAULT NOW(),
    updated_at           TIMESTAMPTZ DEFAULT NOW(),

    -- Natural dedup key: same event won't be inserted twice
    CONSTRAINT events_natural_key UNIQUE (name, start_date, city)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_events_domain       ON events (domain);
CREATE INDEX IF NOT EXISTS idx_events_year         ON events (year);
CREATE INDEX IF NOT EXISTS idx_events_city         ON events (city);
CREATE INDEX IF NOT EXISTS idx_events_country      ON events (country);
CREATE INDEX IF NOT EXISTS idx_events_start_date   ON events (start_date);
CREATE INDEX IF NOT EXISTS idx_events_data_source  ON events (data_source);
CREATE INDEX IF NOT EXISTS idx_events_domain_year  ON events (domain, year);
CREATE INDEX IF NOT EXISTS idx_events_raw_data     ON events USING GIN (raw_data);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- 2. SPONSORS
-- =============================================================================
CREATE TABLE IF NOT EXISTS sponsors (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name          TEXT NOT NULL UNIQUE,
    industry              TEXT,
    company_size          TEXT CHECK (company_size IN ('startup', 'mid', 'enterprise', NULL)),
    headquarters_city     TEXT,
    headquarters_country  TEXT,
    linkedin_url          TEXT,
    website_url           TEXT,
    estimated_revenue     TEXT,
    data_source           TEXT,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sponsors_name    ON sponsors (company_name);
CREATE INDEX IF NOT EXISTS idx_sponsors_country ON sponsors (headquarters_country);

-- =============================================================================
-- 3. EVENT ↔ SPONSOR (junction)
-- =============================================================================
CREATE TABLE IF NOT EXISTS event_sponsors (
    event_id         UUID NOT NULL REFERENCES events(id)   ON DELETE CASCADE,
    sponsor_id       UUID NOT NULL REFERENCES sponsors(id) ON DELETE CASCADE,
    tier             TEXT,   -- 'title' | 'gold' | 'silver' | 'bronze' | 'partner' | NULL
    estimated_amount NUMERIC(14, 2),
    currency         TEXT DEFAULT 'USD',
    PRIMARY KEY (event_id, sponsor_id)
);

CREATE INDEX IF NOT EXISTS idx_event_sponsors_event   ON event_sponsors (event_id);
CREATE INDEX IF NOT EXISTS idx_event_sponsors_sponsor ON event_sponsors (sponsor_id);

-- =============================================================================
-- 4. TALENTS  (speakers · artists · athletes · judges)
-- =============================================================================
CREATE TABLE IF NOT EXISTS talents (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT NOT NULL UNIQUE,
    type                 TEXT CHECK (type IN ('speaker', 'artist', 'athlete', 'judge', 'other', NULL)),
    title                TEXT,
    organization         TEXT,
    linkedin_url         TEXT,
    twitter_url          TEXT,
    spotify_url          TEXT,
    topics               TEXT[],
    follower_count       INTEGER,
    publications_count   INTEGER,
    monthly_listeners    INTEGER,
    data_source          TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_talents_name ON talents (name);
CREATE INDEX IF NOT EXISTS idx_talents_type ON talents (type);

-- =============================================================================
-- 5. EVENT ↔ TALENT (junction)
-- =============================================================================
CREATE TABLE IF NOT EXISTS event_talents (
    event_id      UUID NOT NULL REFERENCES events(id)  ON DELETE CASCADE,
    talent_id     UUID NOT NULL REFERENCES talents(id) ON DELETE CASCADE,
    role          TEXT,   -- 'keynote' | 'speaker' | 'panelist' | 'headliner' | 'opener' | 'athlete'
    session_title TEXT,
    PRIMARY KEY (event_id, talent_id)
);

CREATE INDEX IF NOT EXISTS idx_event_talents_event  ON event_talents (event_id);
CREATE INDEX IF NOT EXISTS idx_event_talents_talent ON event_talents (talent_id);

-- =============================================================================
-- 6. VENUES
-- =============================================================================
CREATE TABLE IF NOT EXISTS venues (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                TEXT NOT NULL,
    city                TEXT,
    country             TEXT,
    type                TEXT,   -- 'convention_center' | 'stadium' | 'club' | 'outdoor' | 'hotel' | 'arena'
    max_capacity        INTEGER,
    address             TEXT,
    latitude            NUMERIC(10, 6),
    longitude           NUMERIC(10, 6),
    website_url         TEXT,
    amenities           TEXT[],
    daily_rate_estimate NUMERIC(14, 2),
    currency            TEXT DEFAULT 'USD',
    past_event_count    INTEGER,
    data_source         TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT venues_natural_key UNIQUE (name, city)
);

CREATE INDEX IF NOT EXISTS idx_venues_city    ON venues (city);
CREATE INDEX IF NOT EXISTS idx_venues_country ON venues (country);

-- =============================================================================
-- 7. COMMUNITIES
-- =============================================================================
CREATE TABLE IF NOT EXISTS communities (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL,
    platform       TEXT,   -- 'linkedin' | 'discord' | 'slack' | 'reddit' | 'meetup' | 'whatsapp'
    url            TEXT,
    member_count   INTEGER,
    activity_level TEXT CHECK (activity_level IN ('high', 'medium', 'low', NULL)),
    topics         TEXT[],
    geography      TEXT,
    data_source    TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT communities_natural_key UNIQUE (name, platform)
);

-- =============================================================================
-- 8. ROW LEVEL SECURITY (enable, allow public read for the demo)
-- =============================================================================
ALTER TABLE events          ENABLE ROW LEVEL SECURITY;
ALTER TABLE sponsors        ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_sponsors  ENABLE ROW LEVEL SECURITY;
ALTER TABLE talents         ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_talents   ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues          ENABLE ROW LEVEL SECURITY;
ALTER TABLE communities     ENABLE ROW LEVEL SECURITY;

-- Public read-only (anon key can SELECT)
CREATE POLICY "public_read_events"         ON events         FOR SELECT USING (true);
CREATE POLICY "public_read_sponsors"       ON sponsors       FOR SELECT USING (true);
CREATE POLICY "public_read_event_sponsors" ON event_sponsors FOR SELECT USING (true);
CREATE POLICY "public_read_talents"        ON talents        FOR SELECT USING (true);
CREATE POLICY "public_read_event_talents"  ON event_talents  FOR SELECT USING (true);
CREATE POLICY "public_read_venues"         ON venues         FOR SELECT USING (true);
CREATE POLICY "public_read_communities"    ON communities    FOR SELECT USING (true);

-- Service-role key can do everything (used by the seed script)
CREATE POLICY "service_all_events"         ON events         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_sponsors"       ON sponsors       FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_event_sponsors" ON event_sponsors FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_talents"        ON talents        FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_event_talents"  ON event_talents  FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_venues"         ON venues         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_all_communities"    ON communities    FOR ALL USING (true) WITH CHECK (true);
