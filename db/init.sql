-- =========================================================
-- HeartGuard + DDL v2.5
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
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS signal_types (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS alert_channels (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS alert_levels (
  id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code   VARCHAR(40) NOT NULL UNIQUE,
  weight INT NOT NULL,
  label  VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS sexes (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(8)  NOT NULL UNIQUE,
  label VARCHAR(40) NOT NULL
);

CREATE TABLE IF NOT EXISTS platforms (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS service_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS delivery_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

CREATE TABLE IF NOT EXISTS batch_export_statuses (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

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

CREATE TABLE IF NOT EXISTS organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(60) NOT NULL UNIQUE,
  name        VARCHAR(160) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS org_roles (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code  VARCHAR(40) NOT NULL UNIQUE,
  label VARCHAR(80)
);

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
  label VARCHAR(80)
);

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
  offset_at            TIMESTAMP,  -- <== renombrado (antes: offset)
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
  UNIQUE(user_id, ts)
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
-- Sin NOW() en el predicate (VOLATILE): solo indexa los no revocados
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
