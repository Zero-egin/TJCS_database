-- Extensions for TimescaleDB (time-series) and PostGIS (spatial)
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  email VARCHAR(120),
  role_id INTEGER REFERENCES roles(id),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE areas (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(50),
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6),
  -- spatial point (WGS84) generated from lon/lat
  geom geometry(Point, 4326) GENERATED ALWAYS AS (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
  ) STORED,
  CHECK (latitude BETWEEN -90 AND 90),
  CHECK (longitude BETWEEN -180 AND 180)
);
-- spatial index for areas
CREATE INDEX IF NOT EXISTS idx_areas_geom ON areas USING GIST (geom);

CREATE TABLE devices (
  id SERIAL PRIMARY KEY,
  serial_no VARCHAR(100) UNIQUE NOT NULL,
  model VARCHAR(100),
  installed_at TIMESTAMPTZ,
  status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE monitoring_points (
  id SERIAL PRIMARY KEY,
  area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
  device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
  name VARCHAR(100) NOT NULL,
  latitude DECIMAL(9,6),
  longitude DECIMAL(9,6),
  geom geometry(Point, 4326) GENERATED ALWAYS AS (
    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
  ) STORED,
  threshold_db NUMERIC(5,2) DEFAULT 65.00,
  status VARCHAR(20) DEFAULT 'active',
  CHECK (latitude BETWEEN -90 AND 90),
  CHECK (longitude BETWEEN -180 AND 180),
  CHECK (threshold_db BETWEEN 0 AND 200)
);
CREATE INDEX IF NOT EXISTS idx_points_geom ON monitoring_points USING GIST (geom);

CREATE TABLE noise_readings (
  id BIGSERIAL PRIMARY KEY,
  point_id INTEGER NOT NULL REFERENCES monitoring_points(id) ON DELETE CASCADE,
  device_id INTEGER REFERENCES devices(id),
  measured_at TIMESTAMPTZ NOT NULL,
  db_value NUMERIC(5,2) NOT NULL,
  temperature NUMERIC(4,1),
  humidity NUMERIC(4,1),
  battery_pct NUMERIC(4,1),
  is_exceed BOOLEAN GENERATED ALWAYS AS (
    CASE WHEN db_value > (
      SELECT COALESCE(mp.threshold_db, 65.00) FROM monitoring_points mp WHERE mp.id = point_id
    ) THEN TRUE ELSE FALSE END
  ) STORED,
  CHECK (db_value BETWEEN 0 AND 200)
);

-- Convert to TimescaleDB hypertable for efficient time-series operations
SELECT create_hypertable('noise_readings', 'measured_at', if_not_exists => TRUE);

-- TimescaleDB policies: chunk interval, compression, retention
SELECT set_chunk_time_interval('noise_readings', INTERVAL '7 days');
ALTER TABLE noise_readings SET (
  timescaledb.compress = true,
  timescaledb.compress_segmentby = 'point_id'
);
SELECT add_compression_policy('noise_readings', INTERVAL '30 days');
SELECT add_retention_policy('noise_readings', INTERVAL '24 months');

CREATE INDEX idx_noise_readings_point_time ON noise_readings(point_id, measured_at);
CREATE INDEX idx_noise_readings_time ON noise_readings(measured_at);
CREATE INDEX idx_points_area ON monitoring_points(area_id);

CREATE TABLE alerts (
  id SERIAL PRIMARY KEY,
  point_id INTEGER NOT NULL REFERENCES monitoring_points(id) ON DELETE CASCADE,
  triggered_at TIMESTAMPTZ NOT NULL,
  db_value NUMERIC(5,2) NOT NULL,
  threshold_db NUMERIC(5,2) NOT NULL,
  level VARCHAR(20) NOT NULL,
  status VARCHAR(20) DEFAULT 'open'
);
CREATE INDEX idx_alerts_point_time ON alerts(point_id, triggered_at);

CREATE TABLE threshold_rules (
  id SERIAL PRIMARY KEY,
  area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
  point_id INTEGER REFERENCES monitoring_points(id) ON DELETE SET NULL,
  day_of_week SMALLINT,
  time_range VARCHAR(20),
  threshold_db NUMERIC(5,2) NOT NULL,
  CHECK (threshold_db BETWEEN 0 AND 200),
  CHECK (day_of_week BETWEEN 0 AND 6)
);
-- indexes to accelerate rule lookup
CREATE INDEX IF NOT EXISTS idx_threshold_rules_point ON threshold_rules(point_id, day_of_week);
CREATE INDEX IF NOT EXISTS idx_threshold_rules_area ON threshold_rules(area_id, day_of_week);

CREATE TABLE actions (
  id SERIAL PRIMARY KEY,
  alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  action_type VARCHAR(50) NOT NULL,
  action_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action_at TIMESTAMPTZ DEFAULT NOW(),
  notes TEXT
);

CREATE TABLE ingestion_jobs (
  id SERIAL PRIMARY KEY,
  source VARCHAR(100),
  status VARCHAR(20) DEFAULT 'pending',
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  records_count INTEGER DEFAULT 0
);

CREATE TABLE audit_logs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(50) NOT NULL,
  resource VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Continuous aggregate for daily point stats (TimescaleDB)
CREATE MATERIALIZED VIEW mv_daily_point_stats
WITH (timescaledb.continuous) AS
SELECT
  point_id,
  time_bucket('1 day', measured_at) AS day,
  COUNT(*) AS samples,
  AVG(db_value) AS avg_db,
  MIN(db_value) AS min_db,
  MAX(db_value) AS max_db,
  SUM(CASE WHEN is_exceed THEN 1 ELSE 0 END) AS exceed_count
FROM noise_readings
GROUP BY point_id, time_bucket('1 day', measured_at);

CREATE INDEX idx_mv_daily_point_stats ON mv_daily_point_stats(point_id, day);
-- auto refresh policy (optional): last 30 days, hourly schedule
SELECT add_continuous_aggregate_policy(
  'mv_daily_point_stats',
  start_offset => INTERVAL '30 days',
  end_offset   => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour'
);

-- Effective threshold lookup considering rules (point > area > default)
CREATE OR REPLACE FUNCTION fn_effective_threshold(p_point_id INTEGER, p_measured_at TIMESTAMPTZ)
RETURNS NUMERIC LANGUAGE plpgsql AS $$
DECLARE
  v_area_id INTEGER;
  v_dow SMALLINT;
  v_time TIME;
  v_thr NUMERIC(5,2);
BEGIN
  v_dow := EXTRACT(DOW FROM p_measured_at);
  v_time := p_measured_at::TIME;
  SELECT area_id INTO v_area_id FROM monitoring_points WHERE id = p_point_id;

  -- point-level rule
  SELECT tr.threshold_db INTO v_thr
  FROM threshold_rules tr
  WHERE tr.point_id = p_point_id AND tr.day_of_week = v_dow
    AND (
      tr.time_range IS NULL OR (
        (split_part(tr.time_range, '-', 1))::time <= v_time AND v_time <= (split_part(tr.time_range, '-', 2))::time
      )
    )
  ORDER BY tr.id DESC
  LIMIT 1;
  IF v_thr IS NOT NULL THEN
    RETURN v_thr;
  END IF;

  -- area-level rule
  SELECT tr.threshold_db INTO v_thr
  FROM threshold_rules tr
  WHERE tr.area_id = v_area_id AND tr.point_id IS NULL AND tr.day_of_week = v_dow
    AND (
      tr.time_range IS NULL OR (
        (split_part(tr.time_range, '-', 1))::time <= v_time AND v_time <= (split_part(tr.time_range, '-', 2))::time
      )
    )
  ORDER BY tr.id DESC
  LIMIT 1;
  IF v_thr IS NOT NULL THEN
    RETURN v_thr;
  END IF;

  -- fallback to monitoring point threshold
  SELECT COALESCE(mp.threshold_db, 65.00) INTO v_thr FROM monitoring_points mp WHERE mp.id = p_point_id;
  RETURN v_thr;
END;
$$;

-- Dynamic computation of is_exceed before insert/update
CREATE OR REPLACE FUNCTION fn_compute_is_exceed()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_thr NUMERIC(5,2);
BEGIN
  v_thr := fn_effective_threshold(NEW.point_id, NEW.measured_at);
  NEW.is_exceed := (NEW.db_value > v_thr);
  RETURN NEW;
END;
$$;

-- Switch generated column to trigger-based computation to support time/rule variability
ALTER TABLE noise_readings ALTER COLUMN is_exceed DROP EXPRESSION;
ALTER TABLE noise_readings ALTER COLUMN is_exceed SET DEFAULT FALSE;
UPDATE noise_readings SET is_exceed = (db_value > fn_effective_threshold(point_id, measured_at)) WHERE TRUE;

CREATE TRIGGER trg_noise_exceed_compute
BEFORE INSERT OR UPDATE ON noise_readings
FOR EACH ROW
EXECUTE FUNCTION fn_compute_is_exceed();

-- Trigger: auto-insert alert records for exceed readings
CREATE OR REPLACE FUNCTION fn_alert_on_exceed()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  thr NUMERIC(5,2);
  diff NUMERIC(5,2);
  lvl VARCHAR(20);
BEGIN
  SELECT COALESCE(threshold_db, 65.00) INTO thr FROM monitoring_points WHERE id = NEW.point_id;
  IF NEW.db_value > thr THEN
    diff := NEW.db_value - thr;
    IF diff >= 20 THEN
      lvl := 'severe';
    ELSIF diff >= 10 THEN
      lvl := 'moderate';
    ELSE
      lvl := 'minor';
    END IF;
    INSERT INTO alerts(point_id, triggered_at, db_value, threshold_db, level, status)
    VALUES (NEW.point_id, NEW.measured_at, NEW.db_value, thr, lvl, 'open');
  END IF;
  RETURN NULL;
END;
$$;

CREATE TRIGGER trg_noise_alert_after_insert
AFTER INSERT ON noise_readings
FOR EACH ROW
WHEN (NEW.is_exceed)
EXECUTE FUNCTION fn_alert_on_exceed();

-- Additional index to speed up open alert queries
CREATE INDEX IF NOT EXISTS idx_alerts_open ON alerts(point_id, triggered_at) WHERE status = 'open';
