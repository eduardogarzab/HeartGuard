-- =========================================================
-- HeartGuard + DDL v2.5 (ajustada para evitar 42804)
-- =========================================================
-- Ejecuta con:
--   psql -U postgres -v dbname=heartguard -v dbuser=heartguard_app -v dbpass='dev_change_me' -f init.sql

\set dbname 'heartguard'
\set dbuser 'heartguard_app'
\set dbpass 'dev_change_me'

-- 0) Crear/ajustar ROLE de aplicación (idempotente, sin DO)
SELECT
  'CREATE ROLE ' || quote_ident(:'dbuser') ||
  ' LOGIN PASSWORD ' || quote_literal(:'dbpass') ||
  ' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT CONNECTION LIMIT -1'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'dbuser')
\gexec

SELECT format('ALTER ROLE %I LOGIN PASSWORD %L', :'dbuser', :'dbpass')
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'dbuser')
\gexec

-- 1) Crear DATABASE si no existe
SELECT format(
  'CREATE DATABASE %I OWNER %I ENCODING ''UTF8'' LC_COLLATE %L LC_CTYPE %L TEMPLATE template0',
  :'dbname', :'dbuser', current_setting('lc_collate'), current_setting('lc_ctype')
)
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = :'dbname')
\gexec

-- 2) Conectarse a la DB
\connect :dbname

-- 3) Schema + seguridad básica
CREATE SCHEMA IF NOT EXISTS heartguard AUTHORIZATION :dbuser;

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE :dbname FROM PUBLIC;

ALTER DATABASE :dbname SET search_path = heartguard, public;
SET search_path = heartguard, public;

-- 4) Extensiones en schema heartguard (requiere superusuario)
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA heartguard;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA heartguard;

-- 5) Grants y defaults
GRANT CONNECT ON DATABASE :dbname TO :dbuser;
GRANT USAGE ON SCHEMA heartguard TO :dbuser;
GRANT USAGE ON SCHEMA public TO :dbuser;

ALTER DEFAULT PRIVILEGES IN SCHEMA heartguard
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO :dbuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA heartguard
  GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO :dbuser;

-- Timeouts por defecto (opcional)
ALTER DATABASE :dbname SET statement_timeout = '30s';
ALTER DATABASE :dbname SET idle_in_transaction_session_timeout = '15s';

-- =========================================================
-- A) Catálogos (reemplazo de ENUMs)
-- =========================================================
CREATE TABLE IF NOT EXISTS user_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS signal_types (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_channels (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS alert_levels (
  id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code   VARCHAR(40) NOT NULL UNIQUE,
  weight INT NOT NULL,
  label  VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS sexes (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(8)  NOT NULL UNIQUE,
  label VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS platforms (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS service_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS delivery_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

CREATE TABLE IF NOT EXISTS batch_export_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

ALTER TABLE IF EXISTS user_statuses ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS signal_types ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS alert_channels ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS alert_levels ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS platforms ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS service_statuses ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS delivery_statuses ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS batch_export_statuses ALTER COLUMN label SET NOT NULL;

-- =========================================================
-- B) Seguridad global (RBAC) + Multi-tenant
-- =========================================================
CREATE TABLE IF NOT EXISTS roles (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          VARCHAR(50)  NOT NULL UNIQUE,
  description   TEXT,
  created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS permissions (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code          VARCHAR(64)  NOT NULL UNIQUE,
  description   TEXT
);

CREATE TABLE IF NOT EXISTS role_permission (
  role_id       UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
  granted_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY(role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS users (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name               VARCHAR(100) NOT NULL,
  email              VARCHAR(150) NOT NULL UNIQUE,
  password_hash      TEXT NOT NULL,
  user_status_id     UUID NOT NULL REFERENCES user_statuses(id) ON DELETE RESTRICT,
  two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_role (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
  assigned_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY(user_id, role_id)
);

CREATE TABLE IF NOT EXISTS system_settings (
  id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  brand_name TEXT NOT NULL DEFAULT 'HeartGuard',
  support_email TEXT NOT NULL DEFAULT 'support@example.com',
  primary_color VARCHAR(16) NOT NULL DEFAULT '#0ea5e9',
  secondary_color VARCHAR(16),
  logo_url TEXT,
  contact_phone TEXT,
  default_locale VARCHAR(16) NOT NULL DEFAULT 'es-MX',
  default_timezone VARCHAR(64) NOT NULL DEFAULT 'America/Mexico_City',
  maintenance_mode BOOLEAN NOT NULL DEFAULT FALSE,
  maintenance_message TEXT,
  updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(60) NOT NULL UNIQUE,
  name        VARCHAR(160) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS org_roles (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

ALTER TABLE IF EXISTS org_roles ALTER COLUMN label SET NOT NULL;

CREATE TABLE IF NOT EXISTS user_org_membership (
  org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
  org_role_id UUID NOT NULL REFERENCES org_roles(id)     ON DELETE RESTRICT,
  joined_at   TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (org_id, user_id)
);

-- =========================================================
-- C) Dominio clínico
-- =========================================================
CREATE TABLE IF NOT EXISTS patients (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id        UUID REFERENCES organizations(id) ON DELETE RESTRICT,
  person_name   VARCHAR(120) NOT NULL,
  birthdate     DATE,
  sex_id        UUID REFERENCES sexes(id) ON DELETE RESTRICT,
  risk_level    VARCHAR(20),
  created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patients_org ON patients(org_id);

CREATE TABLE IF NOT EXISTS care_teams (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id      UUID REFERENCES organizations(id) ON DELETE RESTRICT,
  name        VARCHAR(120) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_care_teams_org ON care_teams(org_id);

CREATE TABLE IF NOT EXISTS care_team_member (
  care_team_id  UUID NOT NULL REFERENCES care_teams(id) ON DELETE CASCADE,
  user_id       UUID NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
  role_in_team  VARCHAR(50) NOT NULL,
  joined_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (care_team_id, user_id)
);

CREATE TABLE IF NOT EXISTS patient_care_team (
  patient_id    UUID NOT NULL REFERENCES patients(id)   ON DELETE CASCADE,
  care_team_id  UUID NOT NULL REFERENCES care_teams(id) ON DELETE CASCADE,
  PRIMARY KEY (patient_id, care_team_id)
);

CREATE TABLE IF NOT EXISTS caregiver_relationship_types (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80) NOT NULL
);

ALTER TABLE IF EXISTS caregiver_relationship_types ALTER COLUMN label SET NOT NULL;

CREATE TABLE IF NOT EXISTS caregiver_patient (
  patient_id  UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
  rel_type_id UUID REFERENCES caregiver_relationship_types(id) ON DELETE SET NULL,
  is_primary  BOOLEAN NOT NULL DEFAULT FALSE,
  started_at  TIMESTAMP NOT NULL DEFAULT NOW(),
  ended_at    TIMESTAMP,
  note        TEXT,
  PRIMARY KEY (patient_id, user_id)
);

CREATE TABLE IF NOT EXISTS org_invitations (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email        VARCHAR(150),
  org_role_id  UUID NOT NULL REFERENCES org_roles(id) ON DELETE RESTRICT,
  token        VARCHAR(120) NOT NULL UNIQUE,
  expires_at   TIMESTAMP NOT NULL,
  used_at      TIMESTAMP,
  revoked_at   TIMESTAMP,
  created_by   UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_org_inv_org ON org_invitations(org_id);

-- =========================================================
-- Stored procedures: CATÁLOGOS
-- (Forzamos tipos/orden para evitar 42804)
-- =========================================================
CREATE OR REPLACE FUNCTION heartguard.sp_catalog_resolve(
  p_catalog text,
  OUT table_name text,
  OUT has_weight boolean)
LANGUAGE plpgsql
AS $$
BEGIN
  has_weight := FALSE;
  table_name := NULL;
  CASE lower(p_catalog)
    WHEN 'user_statuses'        THEN table_name := 'user_statuses';
    WHEN 'signal_types'         THEN table_name := 'signal_types';
    WHEN 'alert_channels'       THEN table_name := 'alert_channels';
    WHEN 'alert_levels'         THEN table_name := 'alert_levels';        -- con weight
    WHEN 'sexes'                THEN table_name := 'sexes';
    WHEN 'platforms'            THEN table_name := 'platforms';
    WHEN 'service_statuses'     THEN table_name := 'service_statuses';
    WHEN 'delivery_statuses'    THEN table_name := 'delivery_statuses';
    WHEN 'batch_export_statuses'THEN table_name := 'batch_export_statuses';
    WHEN 'org_roles'            THEN table_name := 'org_roles';
      WHEN 'content_categories'   THEN table_name := 'content_categories';
      WHEN 'content_statuses'     THEN table_name := 'content_statuses';
  END CASE;
  IF table_name IS NULL THEN
    RAISE EXCEPTION 'Catalogo % no soportado', p_catalog;
  END IF;
  IF lower(p_catalog) = 'alert_levels' THEN
    has_weight := TRUE;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_catalog_list(
  p_catalog text,
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE(id text, code text, label text, weight integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  tname text;
  with_weight boolean;
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 200);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  SELECT table_name, has_weight INTO tname, with_weight
  FROM heartguard.sp_catalog_resolve(p_catalog);

  RETURN QUERY EXECUTE format(
    'SELECT (id)::text, (code)::text, (label)::text, %s
       FROM heartguard.%I
      ORDER BY code
      LIMIT %s OFFSET %s',
    CASE WHEN with_weight THEN 'weight::int' ELSE 'NULL::int' END,
    tname, safe_limit, safe_offset
  );
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_catalog_create(
  p_catalog text,
  p_code text,
  p_label text DEFAULT NULL,
  p_weight integer DEFAULT NULL)
RETURNS TABLE(id text, code text, label text, weight integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  tname text;
  with_weight boolean;
  label_clean text;
BEGIN
  SELECT table_name, has_weight INTO tname, with_weight
  FROM heartguard.sp_catalog_resolve(p_catalog);

  IF p_label IS NULL OR btrim(p_label) = '' THEN
    RAISE EXCEPTION 'Label requerido' USING ERRCODE = '23514';
  END IF;
  label_clean := btrim(p_label);

  IF with_weight THEN
    RETURN QUERY EXECUTE format(
      'INSERT INTO heartguard.%I (code, label, weight)
       VALUES ($1,$2,$3)
       RETURNING (id)::text,(code)::text,(label)::text,(weight)::int',
      tname
    ) USING p_code, label_clean, p_weight;
  ELSE
    RETURN QUERY EXECUTE format(
      'INSERT INTO heartguard.%I (code, label)
       VALUES ($1,$2)
       RETURNING (id)::text,(code)::text,(label)::text,NULL::int',
      tname
    ) USING p_code, label_clean;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_catalog_update(
  p_catalog text,
  p_id uuid,
  p_code text DEFAULT NULL,
  p_label text DEFAULT NULL,
  p_weight integer DEFAULT NULL)
RETURNS TABLE(id text, code text, label text, weight integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  tname text;
  with_weight boolean;
  label_clean text;
BEGIN
  SELECT table_name, has_weight INTO tname, with_weight
  FROM heartguard.sp_catalog_resolve(p_catalog);

  IF p_label IS NOT NULL THEN
    label_clean := btrim(p_label);
    IF label_clean = '' THEN
      RAISE EXCEPTION 'Label requerido' USING ERRCODE = '23514';
    END IF;
  END IF;

  IF with_weight THEN
    RETURN QUERY EXECUTE format(
      'UPDATE heartguard.%I
          SET code   = COALESCE($2, code),
              label  = COALESCE($3, label),
              weight = COALESCE($4, weight)
        WHERE id = $1
      RETURNING (id)::text,(code)::text,(label)::text,(weight)::int',
      tname
    ) USING p_id, p_code, label_clean, p_weight;
  ELSE
    RETURN QUERY EXECUTE format(
      'UPDATE heartguard.%I
          SET code   = COALESCE($2, code),
              label  = COALESCE($3, label)
        WHERE id = $1
      RETURNING (id)::text,(code)::text,(label)::text,NULL::int',
      tname
    ) USING p_id, p_code, label_clean;
  END IF;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_catalog_delete(
  p_catalog text,
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  tname text;
  dummy boolean;
  rows_deleted integer;
BEGIN
  SELECT table_name, has_weight INTO tname, dummy
  FROM heartguard.sp_catalog_resolve(p_catalog);

  EXECUTE format('DELETE FROM heartguard.%I WHERE id = $1', tname) USING p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

-- =========================================================
-- Stored procedures: INVITACIONES (12 columnas, casts explícitos)
-- =========================================================
CREATE OR REPLACE FUNCTION heartguard.sp_org_invitation_create(
  p_org_id uuid,
  p_org_role_id uuid,
  p_email text,
  p_ttl_hours integer,
  p_created_by uuid)
RETURNS TABLE (
  id text,
  org_id text,
  email text,
  org_role_id text,
  org_role_code text,
  token text,
  expires_at timestamp,
  used_at timestamp,
  revoked_at timestamp,
  created_by text,
  created_at timestamp,
  status text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  new_id uuid;
  ttl integer := COALESCE(p_ttl_hours, 24);
BEGIN
  INSERT INTO heartguard.org_invitations AS inv
    (org_id, email, org_role_id, token, expires_at, created_by, created_at)
  VALUES
    (p_org_id, p_email, p_org_role_id, gen_random_uuid()::text,
     (NOW() + make_interval(hours => ttl))::timestamp,
     p_created_by, NOW()::timestamp)
  RETURNING inv.id INTO new_id;

  RETURN QUERY
  SELECT
    i.id::text,
    i.org_id::text,
    i.email::text,
    i.org_role_id::text,
    COALESCE(oroles.code,'')::text,
    i.token::text,
    i.expires_at::timestamp,
    i.used_at::timestamp,
    i.revoked_at::timestamp,
    i.created_by::text,
    i.created_at::timestamp,
    CASE
      WHEN i.revoked_at IS NOT NULL THEN 'revoked'
      WHEN i.used_at    IS NOT NULL THEN 'used'
      WHEN i.expires_at <= NOW()     THEN 'expired'
      ELSE 'pending'
    END::text
  FROM heartguard.org_invitations i
  LEFT JOIN heartguard.org_roles oroles ON oroles.id = i.org_role_id
  WHERE i.id = new_id;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_org_invitations_list(
  p_org_id uuid DEFAULT NULL,
  p_limit integer DEFAULT 50,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  org_id text,
  email text,
  org_role_id text,
  org_role_code text,
  token text,
  expires_at timestamp,
  used_at timestamp,
  revoked_at timestamp,
  created_by text,
  created_at timestamp,
  status text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 200);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    i.id::text,
    i.org_id::text,
    i.email::text,
    i.org_role_id::text,
    COALESCE(oroles.code,'')::text,
    i.token::text,
    i.expires_at::timestamp,
    i.used_at::timestamp,
    i.revoked_at::timestamp,
    i.created_by::text,
    i.created_at::timestamp,
    CASE
      WHEN i.revoked_at IS NOT NULL THEN 'revoked'
      WHEN i.used_at    IS NOT NULL THEN 'used'
      WHEN i.expires_at <= NOW()     THEN 'expired'
      ELSE 'pending'
    END::text
  FROM heartguard.org_invitations i
  LEFT JOIN heartguard.org_roles oroles ON oroles.id = i.org_role_id
  WHERE p_org_id IS NULL OR i.org_id = p_org_id
  ORDER BY i.created_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_org_invitation_cancel(p_invitation_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  affected integer;
BEGIN
  UPDATE heartguard.org_invitations
  SET revoked_at = NOW()::timestamp
  WHERE id = p_invitation_id AND revoked_at IS NULL AND used_at IS NULL;
  GET DIAGNOSTICS affected = ROW_COUNT;
  RETURN affected > 0;
END;
$$;

-- =========================================================
-- D) Dispositivos y streams
-- =========================================================
CREATE TABLE IF NOT EXISTS device_types (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(40) UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE IF NOT EXISTS devices (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id           UUID REFERENCES organizations(id) ON DELETE RESTRICT,
  serial           VARCHAR(80) NOT NULL UNIQUE,
  brand            VARCHAR(80),
  model            VARCHAR(80),
  device_type_id   UUID NOT NULL REFERENCES device_types(id) ON DELETE RESTRICT,
  owner_patient_id UUID REFERENCES patients(id) ON DELETE SET NULL,
  registered_at    TIMESTAMP NOT NULL DEFAULT NOW(),
  active           BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS idx_devices_org ON devices(org_id);

CREATE TABLE IF NOT EXISTS signal_streams (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id     UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  device_id      UUID NOT NULL REFERENCES devices(id)  ON DELETE RESTRICT,
  signal_type_id UUID NOT NULL REFERENCES signal_types(id) ON DELETE RESTRICT,
  sample_rate_hz NUMERIC(10,3) CHECK (sample_rate_hz > 0),
  started_at     TIMESTAMP NOT NULL,
  ended_at       TIMESTAMP,
  CONSTRAINT stream_time_ok CHECK (ended_at IS NULL OR ended_at > started_at)
);

CREATE TABLE IF NOT EXISTS timeseries_binding (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  stream_id      UUID NOT NULL REFERENCES signal_streams(id) ON DELETE CASCADE,
  influx_org     VARCHAR(120),
  influx_bucket  VARCHAR(120) NOT NULL,
  measurement    VARCHAR(120) NOT NULL,
  retention_hint VARCHAR(60),
  created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE (stream_id, influx_bucket, measurement)
);

CREATE TABLE IF NOT EXISTS timeseries_binding_tag (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  binding_id UUID NOT NULL REFERENCES timeseries_binding(id) ON DELETE CASCADE,
  tag_key    VARCHAR(120) NOT NULL,
  tag_value  VARCHAR(240) NOT NULL,
  UNIQUE (binding_id, tag_key)
);

-- =========================================================
-- E) ML e inferencias
-- =========================================================
CREATE TABLE IF NOT EXISTS models (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name              VARCHAR(120) NOT NULL,
  version           VARCHAR(40)  NOT NULL,
  task              VARCHAR(40)  NOT NULL,
  training_data_ref TEXT,
  hyperparams       JSONB,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW(),
  UNIQUE(name, version)
);

CREATE TABLE IF NOT EXISTS event_types (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                VARCHAR(40) NOT NULL UNIQUE,
  description         TEXT,
  severity_default_id UUID NOT NULL REFERENCES alert_levels(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS inferences (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  model_id           UUID REFERENCES models(id) ON DELETE SET NULL,
  stream_id          UUID NOT NULL REFERENCES signal_streams(id) ON DELETE CASCADE,
  window_start       TIMESTAMP NOT NULL,
  window_end         TIMESTAMP NOT NULL,
  predicted_event_id UUID NOT NULL REFERENCES event_types(id) ON DELETE RESTRICT,
  score              NUMERIC(5,4) CHECK (score >= 0 AND score <= 1),
  threshold          NUMERIC(5,4),
  metadata           JSONB,
  created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  series_ref         TEXT,
  feature_snapshot   JSONB,
  UNIQUE(stream_id, window_start, window_end, predicted_event_id)
);
CREATE INDEX IF NOT EXISTS idx_inferences_stream_time
  ON inferences(stream_id, window_start, window_end);

-- =========================================================
-- F) Ground truth
-- =========================================================
CREATE TABLE IF NOT EXISTS ground_truth_labels (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id           UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  event_type_id        UUID NOT NULL REFERENCES event_types(id) ON DELETE RESTRICT,
  onset                TIMESTAMP NOT NULL,
  offset_at            TIMESTAMP,
  annotated_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  source               VARCHAR(40),
  note                 TEXT
);

-- =========================================================
-- G) Alertas y ciclo de vida
-- =========================================================
CREATE TABLE IF NOT EXISTS alert_types (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code            VARCHAR(40) NOT NULL UNIQUE,
  description     TEXT,
  severity_min_id UUID NOT NULL REFERENCES alert_levels(id) ON DELETE RESTRICT,
  severity_max_id UUID NOT NULL REFERENCES alert_levels(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS alert_status (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(30) NOT NULL UNIQUE,
  description TEXT,
  step_order  INT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id                UUID,
  patient_id            UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  type_id               UUID NOT NULL REFERENCES alert_types(id) ON DELETE RESTRICT,
  created_by_model_id   UUID REFERENCES models(id) ON DELETE SET NULL,
  source_inference_id   UUID REFERENCES inferences(id) ON DELETE SET NULL,
  alert_level_id        UUID NOT NULL REFERENCES alert_levels(id) ON DELETE RESTRICT,
  status_id             UUID NOT NULL REFERENCES alert_status(id) ON DELETE RESTRICT,
  created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
  description           TEXT,
  location              geometry(Point,4326),
  duplicate_of_alert_id UUID REFERENCES alerts(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_alerts_org ON alerts(org_id);
CREATE INDEX IF NOT EXISTS idx_alerts_patient_status ON alerts(patient_id, status_id);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(alert_level_id);
CREATE INDEX IF NOT EXISTS idx_alerts_loc_gix ON alerts USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);

CREATE TABLE IF NOT EXISTS alert_assignment (
  alert_id            UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  assignee_user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  assigned_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY(alert_id, assignee_user_id, assigned_at)
);

CREATE TABLE IF NOT EXISTS alert_ack (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id        UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  ack_by_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
  ack_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  note            TEXT
);

CREATE TABLE IF NOT EXISTS alert_resolution (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id            UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  resolved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  resolved_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  outcome             VARCHAR(80),
  note                TEXT
);

CREATE TABLE IF NOT EXISTS alert_delivery (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id           UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  channel_id         UUID NOT NULL REFERENCES alert_channels(id) ON DELETE RESTRICT,
  target             VARCHAR(160) NOT NULL,
  sent_at            TIMESTAMP NOT NULL DEFAULT NOW(),
  delivery_status_id UUID NOT NULL REFERENCES delivery_statuses(id) ON DELETE RESTRICT,
  response_payload   JSONB
);
CREATE INDEX IF NOT EXISTS idx_delivery_alert_channel ON alert_delivery(alert_id, channel_id);

-- Trigger: poblar alerts.org_id desde patients.org_id
CREATE OR REPLACE FUNCTION set_alert_org_from_patient()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.patient_id IS NOT NULL THEN
    SELECT org_id INTO NEW.org_id FROM patients WHERE id = NEW.patient_id;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_alerts_set_org ON alerts;
CREATE TRIGGER trg_alerts_set_org
BEFORE INSERT OR UPDATE OF patient_id ON alerts
FOR EACH ROW
EXECUTE FUNCTION set_alert_org_from_patient();

-- =========================================================
-- H) Ubicaciones
-- =========================================================
CREATE TABLE IF NOT EXISTS patient_locations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  ts         TIMESTAMP NOT NULL DEFAULT NOW(),
  geom       geometry(Point,4326) NOT NULL,
  source     VARCHAR(40),
  accuracy_m NUMERIC(7,2),
  UNIQUE(patient_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_patient_locations_geom_gix ON patient_locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_patient_locations_ts ON patient_locations(patient_id, ts DESC);

CREATE TABLE IF NOT EXISTS user_locations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  ts         TIMESTAMP NOT NULL DEFAULT NOW(),
  geom       geometry(Point,4326) NOT NULL,
  source     VARCHAR(40),
  accuracy_m NUMERIC(7,2),
  UNIQUE (user_id, ts)
);
CREATE INDEX IF NOT EXISTS idx_user_locations_geom_gix ON user_locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_user_locations_ts ON user_locations(user_id, ts DESC);

-- =========================================================
-- I) Operación
-- =========================================================
CREATE TABLE IF NOT EXISTS services (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        VARCHAR(120) NOT NULL UNIQUE,
  url         VARCHAR(255) NOT NULL,
  description TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS service_health (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  service_id         UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
  checked_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  service_status_id  UUID NOT NULL REFERENCES service_statuses(id) ON DELETE RESTRICT,
  latency_ms         INT CHECK (latency_ms >= 0),
  version            VARCHAR(40)
);
CREATE INDEX IF NOT EXISTS idx_service_health_service_time ON service_health(service_id, checked_at DESC);

-- =========================================================
-- Contenido editorial para panel (knowledge base)
-- =========================================================
CREATE TABLE IF NOT EXISTS content_categories (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(60) NOT NULL UNIQUE,
  label VARCHAR(120) NOT NULL,
  color VARCHAR(16)
);

CREATE TABLE IF NOT EXISTS content_statuses (
  id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code   VARCHAR(40) NOT NULL UNIQUE,
  label  VARCHAR(80) NOT NULL,
  weight INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS content_items (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title           TEXT NOT NULL,
  category_id     UUID NOT NULL REFERENCES content_categories(id) ON DELETE RESTRICT,
  status_id       UUID NOT NULL REFERENCES content_statuses(id) ON DELETE RESTRICT,
  author_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
  summary         TEXT,
  created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMP NOT NULL DEFAULT NOW(),
  published_at    TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_content_items_category ON content_items(category_id);
CREATE INDEX IF NOT EXISTS idx_content_items_status ON content_items(status_id);
CREATE INDEX IF NOT EXISTS idx_content_items_author ON content_items(author_user_id);
CREATE INDEX IF NOT EXISTS idx_content_items_created_at ON content_items(created_at DESC);

CREATE TABLE IF NOT EXISTS content_updates (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  content_id     UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
  editor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  change_type    VARCHAR(40) NOT NULL,
  note           TEXT,
  created_at     TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_content_updates_content ON content_updates(content_id);
CREATE INDEX IF NOT EXISTS idx_content_updates_created_at ON content_updates(created_at DESC);

CREATE OR REPLACE FUNCTION touch_content_item()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE content_items
     SET updated_at = NEW.created_at
   WHERE id = NEW.content_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_content_updates_touch ON content_updates;
CREATE TRIGGER trg_content_updates_touch
AFTER INSERT ON content_updates
FOR EACH ROW
EXECUTE FUNCTION touch_content_item();

-- Stored procedure para métricas del panel
CREATE OR REPLACE FUNCTION heartguard.sp_metrics_overview()
RETURNS TABLE (
  avg_response_ms numeric,
  active_users integer,
  active_orgs integer,
  active_memberships integer,
  pending_invitations integer,
  operations jsonb)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_avg numeric;
  v_users integer;
  v_orgs integer;
  v_memberships integer;
  v_pending integer;
  v_ops jsonb;
BEGIN
  SELECT AVG(latency_ms) INTO v_avg
  FROM heartguard.service_health
  WHERE checked_at > NOW() - INTERVAL '7 days';

  SELECT COUNT(*) INTO v_users FROM heartguard.users;
  SELECT COUNT(DISTINCT org_id) INTO v_orgs FROM heartguard.user_org_membership;
  SELECT COUNT(*) INTO v_memberships FROM heartguard.user_org_membership;
  SELECT COUNT(*) INTO v_pending FROM heartguard.org_invitations
    WHERE used_at IS NULL AND revoked_at IS NULL AND expires_at > NOW();

  SELECT COALESCE(jsonb_agg(jsonb_build_object('type', action, 'count', cnt)), '[]'::jsonb) INTO v_ops
  FROM (
    SELECT action, COUNT(*) AS cnt
    FROM heartguard.audit_logs
    WHERE ts > NOW() - INTERVAL '30 days'
    GROUP BY action
    ORDER BY cnt DESC
    LIMIT 10
  ) AS recent_ops;

  avg_response_ms := COALESCE(v_avg, 0);
  active_users := COALESCE(v_users, 0);
  active_orgs := COALESCE(v_orgs, 0);
  active_memberships := COALESCE(v_memberships, 0);
  pending_invitations := COALESCE(v_pending, 0);
  operations := COALESCE(v_ops, '[]'::jsonb);
  RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_recent_activity(p_limit integer DEFAULT 8)
RETURNS TABLE (
  ts timestamp,
  action text,
  entity text,
  actor_email text,
  details jsonb)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 50);
BEGIN
  RETURN QUERY
  SELECT
    a.ts,
    a.action::text,
    a.entity::text,
    u.email::text,
    a.details
  FROM heartguard.audit_logs a
  LEFT JOIN heartguard.users u ON u.id = a.user_id
  ORDER BY a.ts DESC
  LIMIT safe_limit;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_user_status_breakdown()
RETURNS TABLE (
  status_code text,
  status_label text,
  total integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    us.code::text,
    us.label::text,
    COUNT(u.*)::integer AS total
  FROM heartguard.user_statuses us
  LEFT JOIN heartguard.users u ON u.user_status_id = us.id
  GROUP BY us.code, us.label
  ORDER BY total DESC, us.label;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_invitation_breakdown()
RETURNS TABLE (
  status text,
  label text,
  total integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  WITH status_map AS (
    SELECT
      CASE
        WHEN inv.revoked_at IS NOT NULL THEN 'revoked'
        WHEN inv.used_at IS NOT NULL THEN 'used'
        WHEN inv.expires_at < NOW() THEN 'expired'
        ELSE 'pending'
      END AS status
    FROM heartguard.org_invitations inv
  ), aggregated AS (
    SELECT sm.status AS status_value, COUNT(*)::integer AS total
    FROM status_map sm
    GROUP BY sm.status
  )
  SELECT
    s.status_value AS status,
    CASE s.status_value
      WHEN 'pending' THEN 'Pendientes'
      WHEN 'used' THEN 'Utilizadas'
      WHEN 'expired' THEN 'Expiradas'
      WHEN 'revoked' THEN 'Revocadas'
      ELSE INITCAP(s.status_value)
    END AS label,
    s.total
  FROM aggregated s
  ORDER BY s.total DESC;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_content_snapshot()
RETURNS TABLE (
  totals jsonb,
  monthly jsonb,
  categories jsonb,
  status_trends jsonb,
  role_activity jsonb,
  cumulative jsonb,
  top_authors jsonb,
  update_heatmap jsonb)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_totals jsonb := '{}'::jsonb;
  v_monthly jsonb := '[]'::jsonb;
  v_categories jsonb := '[]'::jsonb;
  v_status_trends jsonb := '[]'::jsonb;
  v_role_activity jsonb := '[]'::jsonb;
  v_cumulative jsonb := '[]'::jsonb;
  v_top_authors jsonb := '[]'::jsonb;
  v_heatmap jsonb := '[]'::jsonb;
BEGIN
  WITH base AS (
    SELECT
      COUNT(*) AS total,
      COUNT(*) FILTER (WHERE cs.code = 'published') AS published,
      COUNT(*) FILTER (WHERE cs.code = 'draft') AS drafts,
      COUNT(*) FILTER (WHERE cs.code = 'in_review') AS in_review,
      COUNT(*) FILTER (WHERE cs.code = 'scheduled') AS scheduled,
      COUNT(*) FILTER (WHERE cs.code = 'archived') AS archived,
      COUNT(*) FILTER (WHERE ci.updated_at < NOW() - INTERVAL '45 days') AS stale
    FROM heartguard.content_items ci
    LEFT JOIN heartguard.content_statuses cs ON cs.id = ci.status_id
  ),
  recent_updates AS (
    SELECT COUNT(*) AS updates_last_30_days
    FROM heartguard.content_updates cu
    WHERE cu.created_at >= NOW() - INTERVAL '30 days'
  ),
  update_intervals AS (
    SELECT
      EXTRACT(EPOCH FROM (created_at - LAG(created_at) OVER (PARTITION BY content_id ORDER BY created_at))) / 86400.0 AS diff_days
    FROM heartguard.content_updates
    WHERE created_at >= NOW() - INTERVAL '180 days'
  ),
  active_authors AS (
    SELECT COUNT(DISTINCT user_id) AS total_authors
    FROM (
      SELECT ci.author_user_id AS user_id
      FROM heartguard.content_items ci
      WHERE ci.author_user_id IS NOT NULL
        AND ci.updated_at >= NOW() - INTERVAL '90 days'
      UNION ALL
      SELECT cu.editor_user_id AS user_id
      FROM heartguard.content_updates cu
      WHERE cu.editor_user_id IS NOT NULL
        AND cu.created_at >= NOW() - INTERVAL '90 days'
    ) all_authors
  )
  SELECT jsonb_build_object(
           'total', COALESCE(b.total, 0),
           'published', COALESCE(b.published, 0),
           'drafts', COALESCE(b.drafts, 0),
           'in_review', COALESCE(b.in_review, 0),
           'scheduled', COALESCE(b.scheduled, 0),
           'archived', COALESCE(b.archived, 0),
           'stale', COALESCE(b.stale, 0),
           'active_authors', COALESCE(aa.total_authors, 0),
           'updates_last_30_days', COALESCE(ru.updates_last_30_days, 0),
           'avg_update_interval_days', COALESCE((SELECT AVG(diff_days) FROM update_intervals WHERE diff_days IS NOT NULL AND diff_days >= 0), 0)
         )
  INTO v_totals
  FROM base b
  CROSS JOIN recent_updates ru
  CROSS JOIN active_authors aa;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'period', to_char(month_bucket, 'YYYY-MM'),
             'total', total_count,
             'published', published_count,
             'drafts', draft_count
           )
           ORDER BY month_bucket
         ), '[]'::jsonb)
    INTO v_monthly
  FROM (
    SELECT
      date_trunc('month', ci.created_at) AS month_bucket,
      COUNT(*) AS total_count,
      COUNT(*) FILTER (WHERE cs.code = 'published') AS published_count,
      COUNT(*) FILTER (WHERE cs.code IN ('draft', 'in_review')) AS draft_count
    FROM heartguard.content_items ci
    LEFT JOIN heartguard.content_statuses cs ON cs.id = ci.status_id
    WHERE ci.created_at >= NOW() - INTERVAL '12 months'
    GROUP BY month_bucket
    ORDER BY month_bucket
  ) monthly_stats;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'category', category_stats.code,
             'label', category_stats.label,
             'count', category_stats.category_count
           )
           ORDER BY category_stats.category_count DESC, category_stats.label
         ), '[]'::jsonb)
    INTO v_categories
  FROM (
    SELECT
      cc.code,
      cc.label,
      COUNT(*) AS category_count
    FROM heartguard.content_items ci
    JOIN heartguard.content_categories cc ON cc.id = ci.category_id
    GROUP BY cc.code, cc.label
  ) category_stats;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'period', to_char(period_bucket, 'YYYY-MM'),
             'status', status_code,
             'count', status_count
           )
           ORDER BY period_bucket, status_code
         ), '[]'::jsonb)
    INTO v_status_trends
  FROM (
    SELECT
      date_trunc('month', COALESCE(ci.published_at, ci.updated_at)) AS period_bucket,
      cs.code AS status_code,
      COUNT(*) AS status_count
    FROM heartguard.content_items ci
    JOIN heartguard.content_statuses cs ON cs.id = ci.status_id
    WHERE COALESCE(ci.published_at, ci.updated_at) >= NOW() - INTERVAL '12 months'
    GROUP BY period_bucket, cs.code
  ) status_stats;

  WITH recent_editor_activity AS (
    SELECT cu.editor_user_id, cu.created_at
    FROM heartguard.content_updates cu
    WHERE cu.editor_user_id IS NOT NULL
      AND cu.created_at >= NOW() - INTERVAL '90 days'
  ), role_map AS (
    SELECT ur.user_id, MIN(r.name) AS role_name
    FROM heartguard.user_role ur
    JOIN heartguard.roles r ON r.id = ur.role_id
    GROUP BY ur.user_id
  )
  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'role', role_name,
             'count', role_count
           )
           ORDER BY role_count DESC, role_name
         ), '[]'::jsonb)
    INTO v_role_activity
  FROM (
    SELECT
      COALESCE(rm.role_name, 'Sin rol asignado') AS role_name,
      COUNT(*) AS role_count
    FROM recent_editor_activity rea
    LEFT JOIN role_map rm ON rm.user_id = rea.editor_user_id
    GROUP BY COALESCE(rm.role_name, 'Sin rol asignado')
  ) role_stats;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'period', to_char(period_bucket, 'YYYY-MM'),
             'count', cumulative_count
           )
           ORDER BY period_bucket
         ), '[]'::jsonb)
    INTO v_cumulative
  FROM (
    SELECT
      period_bucket,
      SUM(monthly_count) OVER (ORDER BY period_bucket) AS cumulative_count
    FROM (
      SELECT
        date_trunc('month', COALESCE(ci.published_at, ci.created_at)) AS period_bucket,
        COUNT(*) AS monthly_count
      FROM heartguard.content_items ci
      JOIN heartguard.content_statuses cs ON cs.id = ci.status_id AND cs.code = 'published'
      WHERE COALESCE(ci.published_at, ci.created_at) >= NOW() - INTERVAL '18 months'
      GROUP BY period_bucket
      ORDER BY period_bucket
    ) published_monthly
  ) cumulative_stats;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'user_id', author_user_id,
             'name', COALESCE(author_name, 'Sin autor'),
             'email', author_email,
             'published', published_count,
             'last_published', CASE WHEN last_published_at IS NULL THEN NULL ELSE to_char(last_published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') END
           )
           ORDER BY published_count DESC, last_published_at DESC
         ), '[]'::jsonb)
    INTO v_top_authors
  FROM (
    SELECT
      ag.author_user_id::text AS author_user_id,
      u.name AS author_name,
      u.email AS author_email,
      ag.published_count,
      ag.last_published_at
    FROM (
      SELECT
        ci.author_user_id,
        COUNT(*) AS published_count,
        MAX(COALESCE(ci.published_at, ci.updated_at)) AS last_published_at
      FROM heartguard.content_items ci
      JOIN heartguard.content_statuses cs ON cs.id = ci.status_id AND cs.code = 'published'
      WHERE ci.author_user_id IS NOT NULL
        AND COALESCE(ci.published_at, ci.updated_at) >= NOW() - INTERVAL '180 days'
      GROUP BY ci.author_user_id
      ORDER BY COUNT(*) DESC, MAX(COALESCE(ci.published_at, ci.updated_at)) DESC
      LIMIT 6
    ) ag
    LEFT JOIN heartguard.users u ON u.id = ag.author_user_id
  ) author_stats;

  SELECT COALESCE(jsonb_agg(
           jsonb_build_object(
             'date', to_char(day_bucket, 'YYYY-MM-DD'),
             'count', update_count
           )
           ORDER BY day_bucket
         ), '[]'::jsonb)
    INTO v_heatmap
  FROM (
    SELECT
      date_trunc('day', cu.created_at) AS day_bucket,
      COUNT(*) AS update_count
    FROM heartguard.content_updates cu
    WHERE cu.created_at >= NOW() - INTERVAL '30 days'
    GROUP BY day_bucket
    ORDER BY day_bucket
  ) heatmap_stats;

  totals := COALESCE(v_totals, '{}'::jsonb);
  monthly := COALESCE(v_monthly, '[]'::jsonb);
  categories := COALESCE(v_categories, '[]'::jsonb);
  status_trends := COALESCE(v_status_trends, '[]'::jsonb);
  role_activity := COALESCE(v_role_activity, '[]'::jsonb);
  cumulative := COALESCE(v_cumulative, '[]'::jsonb);
  top_authors := COALESCE(v_top_authors, '[]'::jsonb);
  update_heatmap := COALESCE(v_heatmap, '[]'::jsonb);
  RETURN NEXT;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_content_report(
  p_from DATE DEFAULT NULL,
  p_to DATE DEFAULT NULL,
  p_status TEXT DEFAULT NULL,
  p_category TEXT DEFAULT NULL,
  p_search TEXT DEFAULT NULL,
  p_limit INTEGER DEFAULT 100,
  p_offset INTEGER DEFAULT 0)
RETURNS TABLE (
  content_id UUID,
  title TEXT,
  status_code TEXT,
  status_label TEXT,
  category_code TEXT,
  category_label TEXT,
  author_name TEXT,
  author_email TEXT,
  published_at TIMESTAMP,
  updated_at TIMESTAMP,
  last_update_at TIMESTAMP,
  last_editor_name TEXT,
  updates_30d INTEGER,
  total_count INTEGER)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
  from_ts TIMESTAMP;
  to_ts TIMESTAMP;
BEGIN
  IF p_from IS NOT NULL THEN
    from_ts := date_trunc('day', p_from);
  END IF;
  IF p_to IS NOT NULL THEN
    to_ts := date_trunc('day', p_to) + INTERVAL '1 day';
  END IF;

  RETURN QUERY
  WITH filtered AS (
    SELECT
      ci.id,
      ci.title,
      cs.code AS status_code,
      cs.label AS status_label,
      cc.code AS category_code,
      cc.label AS category_label,
      au.name AS author_name,
      au.email AS author_email,
      ci.published_at,
      ci.updated_at,
      ci.summary
    FROM heartguard.content_items ci
    JOIN heartguard.content_statuses cs ON cs.id = ci.status_id
    JOIN heartguard.content_categories cc ON cc.id = ci.category_id
    LEFT JOIN heartguard.users au ON au.id = ci.author_user_id
    WHERE (from_ts IS NULL OR COALESCE(ci.published_at, ci.created_at) >= from_ts)
      AND (to_ts IS NULL OR COALESCE(ci.published_at, ci.created_at) < to_ts)
      AND (p_status IS NULL OR cs.code = p_status)
      AND (p_category IS NULL OR cc.code = p_category)
      AND (
        p_search IS NULL OR p_search = ''
        OR ci.title ILIKE '%' || p_search || '%'
        OR COALESCE(ci.summary, '') ILIKE '%' || p_search || '%'
      )
  )
  SELECT
    f.id::uuid,
    f.title::text,
    f.status_code::text,
    f.status_label::text,
    f.category_code::text,
    f.category_label::text,
    f.author_name::text,
    f.author_email::text,
    f.published_at,
    f.updated_at,
    lu.last_update_at,
    lu.last_editor_name::text,
    COALESCE(uc.updates_30d, 0)::integer AS updates_30d,
    COUNT(*) OVER()::integer AS total_count
  FROM filtered f
  LEFT JOIN LATERAL (
    SELECT
      cu.created_at AS last_update_at,
      u.name AS last_editor_name
    FROM heartguard.content_updates cu
    LEFT JOIN heartguard.users u ON u.id = cu.editor_user_id
    WHERE cu.content_id = f.id
    ORDER BY cu.created_at DESC
    LIMIT 1
  ) lu ON true
  LEFT JOIN LATERAL (
    SELECT COUNT(*)::integer AS updates_30d
    FROM heartguard.content_updates cu
    WHERE cu.content_id = f.id
      AND cu.created_at >= NOW() - INTERVAL '30 days'
  ) uc ON true
  ORDER BY
    COALESCE(f.published_at, f.updated_at) DESC,
    lower(f.title)
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_operations_report(
  p_from DATE DEFAULT NULL,
  p_to DATE DEFAULT NULL,
  p_action TEXT DEFAULT NULL,
  p_limit INTEGER DEFAULT 100,
  p_offset INTEGER DEFAULT 0)
RETURNS TABLE (
  action TEXT,
  total_events INTEGER,
  unique_users INTEGER,
  unique_entities INTEGER,
  first_event TIMESTAMP,
  last_event TIMESTAMP,
  total_count INTEGER)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
  from_ts TIMESTAMP;
  to_ts TIMESTAMP;
  action_filter TEXT := NULLIF(p_action, '');
BEGIN
  IF p_from IS NOT NULL THEN
    from_ts := date_trunc('day', p_from);
  END IF;
  IF p_to IS NOT NULL THEN
    to_ts := date_trunc('day', p_to) + INTERVAL '1 day';
  END IF;

  RETURN QUERY
  WITH filtered AS (
    SELECT
      a.action,
      a.ts,
      a.user_id,
      a.entity_id
    FROM heartguard.audit_logs a
    WHERE (from_ts IS NULL OR a.ts >= from_ts)
      AND (to_ts IS NULL OR a.ts < to_ts)
      AND (action_filter IS NULL OR a.action = action_filter)
  )
  SELECT
    f.action::text,
    COUNT(*)::integer AS total_events,
    COUNT(DISTINCT f.user_id)::integer AS unique_users,
    COUNT(DISTINCT f.entity_id)::integer AS unique_entities,
    MIN(f.ts) AS first_event,
    MAX(f.ts) AS last_event,
    COUNT(*) OVER()::integer AS total_count
  FROM filtered f
  GROUP BY f.action
  ORDER BY total_events DESC, f.action
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_metrics_users_report(
  p_from DATE DEFAULT NULL,
  p_to DATE DEFAULT NULL,
  p_status TEXT DEFAULT NULL,
  p_search TEXT DEFAULT NULL,
  p_limit INTEGER DEFAULT 100,
  p_offset INTEGER DEFAULT 0)
RETURNS TABLE (
  user_id UUID,
  name TEXT,
  email TEXT,
  status_code TEXT,
  status_label TEXT,
  created_at TIMESTAMP,
  first_action TIMESTAMP,
  last_action TIMESTAMP,
  actions_count INTEGER,
  distinct_actions INTEGER,
  org_memberships INTEGER,
  total_count INTEGER)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
  from_ts TIMESTAMP;
  to_ts TIMESTAMP;
  status_filter TEXT := NULLIF(p_status, '');
  search_filter TEXT := NULLIF(p_search, '');
BEGIN
  IF p_from IS NOT NULL THEN
    from_ts := date_trunc('day', p_from);
  END IF;
  IF p_to IS NOT NULL THEN
    to_ts := date_trunc('day', p_to) + INTERVAL '1 day';
  END IF;

  RETURN QUERY
  WITH logs AS (
    SELECT
      a.user_id,
      a.action,
      a.ts
    FROM heartguard.audit_logs a
    WHERE a.user_id IS NOT NULL
      AND (from_ts IS NULL OR a.ts >= from_ts)
      AND (to_ts IS NULL OR a.ts < to_ts)
  ),
  aggregated AS (
    SELECT
      l.user_id,
      COUNT(*)::integer AS actions_count,
      COUNT(DISTINCT l.action)::integer AS distinct_actions,
      MIN(l.ts) AS first_action,
      MAX(l.ts) AS last_action
    FROM logs l
    GROUP BY l.user_id
  ),
  candidates AS (
    SELECT u.id
    FROM heartguard.users u
    WHERE (from_ts IS NULL OR u.created_at >= from_ts)
      AND (to_ts IS NULL OR u.created_at < to_ts)
    UNION
    SELECT agg.user_id
    FROM aggregated agg
  ),
  memberships AS (
    SELECT uom.user_id, COUNT(DISTINCT uom.org_id)::integer AS org_count
    FROM heartguard.user_org_membership uom
    GROUP BY uom.user_id
  )
  SELECT
    u.id,
    u.name::text,
    u.email::text,
    us.code::text,
    us.label::text,
    u.created_at,
    agg.first_action,
    agg.last_action,
    COALESCE(agg.actions_count, 0)::integer,
    COALESCE(agg.distinct_actions, 0)::integer,
    COALESCE(m.org_count, 0)::integer,
    COUNT(*) OVER()::integer AS total_count
  FROM candidates c
  JOIN heartguard.users u ON u.id = c.id
  LEFT JOIN aggregated agg ON agg.user_id = u.id
  LEFT JOIN heartguard.user_statuses us ON us.id = u.user_status_id
  LEFT JOIN memberships m ON m.user_id = u.id
  WHERE (status_filter IS NULL OR us.code = status_filter)
    AND (
      search_filter IS NULL OR search_filter = ''
      OR u.name ILIKE '%' || search_filter || '%'
      OR u.email ILIKE '%' || search_filter || '%'
    )
  ORDER BY COALESCE(agg.actions_count, 0) DESC, u.created_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

-- =========================================================
-- J) Auditoría
-- =========================================================
CREATE TABLE IF NOT EXISTS audit_logs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID REFERENCES users(id) ON DELETE SET NULL,
  action     VARCHAR(80) NOT NULL,
  entity     VARCHAR(80),
  entity_id  UUID,
  ts         TIMESTAMP NOT NULL DEFAULT NOW(),
  ip         INET,
  details    JSONB
);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);

-- =========================================================
-- K) Tokens y API Keys
-- =========================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash         TEXT NOT NULL,
  issued_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at         TIMESTAMP NOT NULL,
  revoked_at         TIMESTAMP,
  client_id          VARCHAR(120),
  device_fingerprint VARCHAR(200),
  ip_issued          INET,
  UNIQUE (user_id, token_hash)
);
CREATE INDEX IF NOT EXISTS idx_refresh_not_revoked
  ON refresh_tokens(user_id) WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS api_keys (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
  key_hash       TEXT NOT NULL,
  label          VARCHAR(120),
  created_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at     TIMESTAMP,
  revoked_at     TIMESTAMP,
  scopes         TEXT[] NOT NULL DEFAULT '{}'::text[],
  UNIQUE (key_hash)
);

CREATE TABLE IF NOT EXISTS api_key_permission (
  api_key_id     UUID NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE,
  permission_id  UUID NOT NULL REFERENCES permissions(id) ON DELETE RESTRICT,
  granted_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (api_key_id, permission_id)
);

CREATE TABLE IF NOT EXISTS push_devices (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  platform_id    UUID NOT NULL REFERENCES platforms(id) ON DELETE RESTRICT,
  push_token     TEXT NOT NULL,
  last_seen_at   TIMESTAMP NOT NULL DEFAULT NOW(),
  active         BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE (user_id, platform_id, push_token)
);

-- =========================================================
-- L) Exports batch
-- =========================================================
CREATE TABLE IF NOT EXISTS batch_exports (
  id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  purpose                  VARCHAR(80) NOT NULL,
  target_ref               TEXT NOT NULL,
  requested_by             UUID REFERENCES users(id) ON DELETE SET NULL,
  requested_at             TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at             TIMESTAMP,
  batch_export_status_id   UUID NOT NULL REFERENCES batch_export_statuses(id) ON DELETE RESTRICT,
  details                  JSONB
);

-- =========================================================
-- M) Trigger updated_at
-- =========================================================
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := NOW();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =========================================================
-- N) Vista de conveniencia
-- =========================================================
CREATE OR REPLACE VIEW v_patient_active_alerts AS
SELECT a.id, a.patient_id, p.person_name,
       at.code AS alert_code,
       al.code AS level,
       s.code  AS status,
       a.created_at, a.description
FROM alerts a
JOIN patients p      ON p.id = a.patient_id
JOIN alert_types at  ON at.id = a.type_id
JOIN alert_levels al ON al.id = a.alert_level_id
JOIN alert_status s  ON s.id = a.status_id
WHERE s.code IN ('created','notified','ack');

-- FIN init.sql
