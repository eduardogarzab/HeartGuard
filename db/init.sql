-- =========================================================
-- HeartGuard + DDL v2.5 (ajustada para evitar 42804)
-- =========================================================
-- Ejecuta con:
--   psql -U postgres -v dbname=heartguard -v dbuser=heartguard_app -v dbpass='dev_change_me' -f init.sql

-- Todas las entidades exceptuando las que contienen jsonb estan normalizadas hasta la 3FN, sin embargo al ser un sistema de monitoreo se requieren de detalles adicinales los cuales se documentan en cada tabla y no es practico normalizar.
-- Por lo tanto consideramos que no se deben considerar al evaluar la normalizacion, ya que no afectan la integridad de los datos. Omite la revisión de normalización en las tablas que contienen columnas JSONB.

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

CREATE TABLE IF NOT EXISTS risk_levels (
  id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code    VARCHAR(20) UNIQUE NOT NULL, -- ej: 'low', 'medium', 'high'
  label   VARCHAR(50) NOT NULL, -- ej: 'Bajo', 'Medio', 'Alto'
  weight  INT -- Ordenamiento opcional
);
CREATE INDEX IF NOT EXISTS idx_risk_levels_code ON risk_levels(code);

CREATE TABLE IF NOT EXISTS team_member_roles (
  id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code    VARCHAR(30) UNIQUE NOT NULL, -- ej: 'doctor', 'nurse',...
  label   VARCHAR(60) NOT NULL -- ej: 'Doctor/a', 'Enfermero/a',
);
CREATE INDEX IF NOT EXISTS idx_team_member_roles_code ON team_member_roles(code);

ALTER TABLE IF EXISTS user_statuses ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS signal_types ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS alert_channels ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS alert_levels ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS platforms ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS service_statuses ALTER COLUMN label SET NOT NULL;
ALTER TABLE IF EXISTS delivery_statuses ALTER COLUMN label SET NOT NULL;

-- =========================================================
-- B) Seguridad global (RBAC) + Multi-tenant
-- =========================================================
CREATE TABLE IF NOT EXISTS roles (
  code        VARCHAR(40) PRIMARY KEY,
  label       VARCHAR(80) NOT NULL,
  description TEXT,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name               VARCHAR(100) NOT NULL,
  email              VARCHAR(150) NOT NULL UNIQUE,
  password_hash      TEXT NOT NULL,
  user_status_id     UUID NOT NULL REFERENCES user_statuses(id) ON DELETE RESTRICT,
  role_code          VARCHAR(40) NOT NULL DEFAULT 'user' REFERENCES roles(code) ON DELETE RESTRICT,
  two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  profile_photo_url  TEXT,
  created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(user_status_id);

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
CREATE INDEX IF NOT EXISTS idx_system_settings_updated_by ON system_settings(updated_by);

CREATE TABLE IF NOT EXISTS organizations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(60) NOT NULL UNIQUE,
  name        VARCHAR(160) NOT NULL,
  created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_org_membership (
  org_id      UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id)         ON DELETE CASCADE,
  role_code   VARCHAR(40) NOT NULL REFERENCES roles(code) ON DELETE RESTRICT,
  joined_at   TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (org_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_user_org_membership_role ON user_org_membership(role_code);

-- =========================================================
-- C) Dominio clínico
-- =========================================================
CREATE TABLE IF NOT EXISTS patients (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id            UUID REFERENCES organizations(id) ON DELETE RESTRICT,
  person_name       VARCHAR(120) NOT NULL,
  email             VARCHAR(150) NOT NULL UNIQUE,
  password_hash     TEXT NOT NULL,
  birthdate         DATE,
  sex_id            UUID REFERENCES sexes(id) ON DELETE RESTRICT,
  risk_level_id     UUID REFERENCES risk_levels(id) ON DELETE SET NULL,
  profile_photo_url TEXT,
  created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_patients_org ON patients(org_id);
CREATE INDEX IF NOT EXISTS idx_patients_sex ON patients(sex_id);
CREATE INDEX IF NOT EXISTS idx_patients_risk_level ON patients(risk_level_id);

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
  role_id       UUID NOT NULL REFERENCES team_member_roles(id) ON DELETE RESTRICT,
  joined_at     TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (care_team_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_care_team_member_role ON care_team_member(role_id);

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
CREATE INDEX IF NOT EXISTS idx_caregiver_patient_rel_type ON caregiver_patient(rel_type_id);

CREATE OR REPLACE FUNCTION heartguard.sp_patients_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  person_name text,
  email text,
  birthdate date,
  sex_code text,
  sex_label text,
  risk_level_id text,
  risk_level_code text,
  risk_level_label text,
  profile_photo_url text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    p.id::text,
    p.org_id::text,
    o.name::text,
    p.person_name::text,
    p.email::text,
    p.birthdate,
    sx.code::text,
    sx.label::text,
    p.risk_level_id::text,
    rl.code::text,
    rl.label::text,
    p.profile_photo_url::text,
    p.created_at
  FROM heartguard.patients p
  LEFT JOIN heartguard.organizations o ON o.id = p.org_id
  LEFT JOIN heartguard.sexes sx ON sx.id = p.sex_id
  LEFT JOIN heartguard.risk_levels rl ON rl.id = p.risk_level_id
  ORDER BY p.created_at DESC, p.person_name
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

-- Breakdown of inferences by predicted event type (code, label, count)
CREATE OR REPLACE FUNCTION heartguard.sp_metrics_inference_breakdown()
RETURNS TABLE (
  code text,
  label text,
  count integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT
    et.code::text,
    COALESCE(et.description, et.code)::text,
    COUNT(inf.*)::integer
  FROM heartguard.inferences inf
  JOIN heartguard.event_types et ON et.id = inf.predicted_event_id
  GROUP BY et.code, et.description
  ORDER BY COUNT(inf.*) DESC;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_patient_create(
  p_org_id uuid,
  p_person_name text,
  p_email text,
  p_password text,
  p_birthdate date DEFAULT NULL,
  p_sex_code text DEFAULT NULL,
  p_risk_level_id uuid DEFAULT NULL,
  p_profile_photo_url text DEFAULT NULL)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  person_name text,
  email text,
  birthdate date,
  sex_code text,
  sex_label text,
  risk_level_id text,
  risk_level_code text,
  risk_level_label text,
  profile_photo_url text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_name text;
  v_sex_id uuid := NULL;
  v_photo_url text;
  v_email text;
  v_password_hash text;
BEGIN
  v_name := NULLIF(btrim(p_person_name), '');
  IF v_name IS NULL THEN
    RAISE EXCEPTION 'Nombre requerido' USING ERRCODE = '23514';
  END IF;

  v_email := lower(NULLIF(btrim(p_email), ''));
  IF v_email IS NULL THEN
    RAISE EXCEPTION 'Correo requerido' USING ERRCODE = '23514';
  END IF;

  IF p_password IS NULL OR btrim(p_password) = '' THEN
    RAISE EXCEPTION 'Contraseña requerida' USING ERRCODE = '23514';
  END IF;
  v_password_hash := crypt(p_password, gen_salt('bf', 10));

  IF p_sex_code IS NOT NULL THEN
    IF btrim(p_sex_code) = '' THEN
      v_sex_id := NULL;
    ELSE
      SELECT sx.id INTO v_sex_id
      FROM heartguard.sexes sx
      WHERE lower(sx.code) = lower(btrim(p_sex_code))
      LIMIT 1;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'Sexo % no existe', p_sex_code USING ERRCODE = '23514';
      END IF;
    END IF;
  END IF;

  v_photo_url := NULLIF(btrim(p_profile_photo_url), '');

  RETURN QUERY
  INSERT INTO heartguard.patients AS p (org_id, person_name, email, password_hash, birthdate, sex_id, risk_level_id, profile_photo_url)
  VALUES (p_org_id, v_name, v_email, v_password_hash, p_birthdate, v_sex_id, p_risk_level_id, v_photo_url)
  RETURNING
    p.id::text,
    p.org_id::text,
    (SELECT o.name::text FROM heartguard.organizations o WHERE o.id = p.org_id),
    p.person_name::text,
    p.email::text,
    p.birthdate,
    (SELECT sx.code::text FROM heartguard.sexes sx WHERE sx.id = p.sex_id),
    (SELECT sx.label::text FROM heartguard.sexes sx WHERE sx.id = p.sex_id),
    p.risk_level_id::text,
    (SELECT rl.code::text FROM heartguard.risk_levels rl WHERE rl.id = p.risk_level_id),
    (SELECT rl.label::text FROM heartguard.risk_levels rl WHERE rl.id = p.risk_level_id),
    p.profile_photo_url::text,
    p.created_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_patient_update(
  p_id uuid,
  p_org_id uuid,
  p_person_name text,
  p_email text,
  p_password text,
  p_birthdate date,
  p_sex_code text,
  p_risk_level_id uuid,
  p_profile_photo_url text)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  person_name text,
  email text,
  birthdate date,
  sex_code text,
  sex_label text,
  risk_level_id text,
  risk_level_code text,
  risk_level_label text,
  profile_photo_url text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_name text;
  v_sex_id uuid := NULL;
  v_photo_url text;
  v_email text := NULL;
  v_password_hash text := NULL;
BEGIN
  v_name := NULLIF(btrim(p_person_name), '');
  IF v_name IS NULL THEN
    RAISE EXCEPTION 'Nombre requerido' USING ERRCODE = '23514';
  END IF;

  IF p_email IS NOT NULL THEN
    v_email := lower(NULLIF(btrim(p_email), ''));
    IF v_email IS NULL THEN
      RAISE EXCEPTION 'Correo requerido' USING ERRCODE = '23514';
    END IF;
  END IF;

  IF p_password IS NOT NULL THEN
    IF btrim(p_password) = '' THEN
      RAISE EXCEPTION 'Contraseña inválida' USING ERRCODE = '23514';
    END IF;
    v_password_hash := crypt(p_password, gen_salt('bf', 10));
  END IF;

  IF p_sex_code IS NOT NULL THEN
    IF btrim(p_sex_code) = '' THEN
      v_sex_id := NULL;
    ELSE
      SELECT sx.id INTO v_sex_id
      FROM heartguard.sexes sx
      WHERE lower(sx.code) = lower(btrim(p_sex_code))
      LIMIT 1;
      IF NOT FOUND THEN
        RAISE EXCEPTION 'Sexo % no existe', p_sex_code USING ERRCODE = '23514';
      END IF;
    END IF;
  END IF;

  v_photo_url := NULLIF(btrim(p_profile_photo_url), '');

  RETURN QUERY
  UPDATE heartguard.patients AS p
     SET org_id = COALESCE(p_org_id, p.org_id),
         person_name = v_name,
         email = COALESCE(v_email, p.email),
         password_hash = COALESCE(v_password_hash, p.password_hash),
         birthdate = CASE WHEN p_birthdate IS NULL THEN p.birthdate ELSE p_birthdate END,
         sex_id = CASE WHEN p_sex_code IS NULL THEN p.sex_id ELSE v_sex_id END,
         risk_level_id = CASE WHEN p_risk_level_id IS NULL THEN p.risk_level_id ELSE p_risk_level_id END,
         profile_photo_url = CASE WHEN p_profile_photo_url IS NULL THEN p.profile_photo_url ELSE v_photo_url END
   WHERE p.id = p_id
  RETURNING
    p.id::text,
    p.org_id::text,
    (SELECT o.name::text FROM heartguard.organizations o WHERE o.id = p.org_id),
    p.person_name::text,
    p.email::text,
    p.birthdate,
    (SELECT sx.code::text FROM heartguard.sexes sx WHERE sx.id = p.sex_id),
    (SELECT sx.label::text FROM heartguard.sexes sx WHERE sx.id = p.sex_id),
    p.risk_level_id::text,
    (SELECT rl.code::text FROM heartguard.risk_levels rl WHERE rl.id = p.risk_level_id),
    (SELECT rl.label::text FROM heartguard.risk_levels rl WHERE rl.id = p.risk_level_id),
    p.profile_photo_url::text,
    p.created_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_patient_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.patients WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

CREATE TABLE IF NOT EXISTS org_invitations (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email        VARCHAR(150),
  role_code    VARCHAR(40) NOT NULL REFERENCES roles(code) ON DELETE RESTRICT,
  token        VARCHAR(120) NOT NULL UNIQUE,
  expires_at   TIMESTAMP NOT NULL,
  used_at      TIMESTAMP,
  revoked_at   TIMESTAMP,
  created_by   UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_org_inv_org ON org_invitations(org_id);
CREATE INDEX IF NOT EXISTS idx_org_inv_role_code ON org_invitations(role_code);
CREATE INDEX IF NOT EXISTS idx_org_inv_created_by ON org_invitations(created_by);

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
    WHEN 'user_statuses'     THEN table_name := 'user_statuses';
    WHEN 'signal_types'      THEN table_name := 'signal_types';
    WHEN 'alert_channels'    THEN table_name := 'alert_channels';
    WHEN 'alert_levels'      THEN table_name := 'alert_levels';        -- con weight
    WHEN 'sexes'             THEN table_name := 'sexes';
    WHEN 'platforms'         THEN table_name := 'platforms';
    WHEN 'service_statuses'  THEN table_name := 'service_statuses';
    WHEN 'delivery_statuses' THEN table_name := 'delivery_statuses';
    WHEN 'device_types'      THEN table_name := 'device_types';
    WHEN 'risk_levels'       THEN table_name := 'risk_levels';       -- con weight
    WHEN 'team_member_roles' THEN table_name := 'team_member_roles';
  END CASE;
  IF table_name IS NULL THEN
    RAISE EXCEPTION 'Catalogo % no soportado', p_catalog;
  END IF;
  IF lower(p_catalog) IN ('alert_levels', 'risk_levels') THEN
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
  p_role_code text,
  p_email text,
  p_ttl_hours integer,
  p_created_by uuid)
RETURNS TABLE (
  id text,
  org_id text,
  email text,
  role_code text,
  role_label text,
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
    (org_id, email, role_code, token, expires_at, created_by, created_at)
  VALUES
    (p_org_id, p_email, p_role_code, gen_random_uuid()::text,
     (NOW() + make_interval(hours => ttl))::timestamp,
     p_created_by, NOW()::timestamp)
  RETURNING inv.id INTO new_id;

  RETURN QUERY
  SELECT
    i.id::text,
    i.org_id::text,
    i.email::text,
    i.role_code::text,
    COALESCE(r.label,'')::text,
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
  LEFT JOIN heartguard.roles r ON r.code = i.role_code
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
  role_code text,
  role_label text,
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
    i.role_code::text,
    COALESCE(r.label,'')::text,
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
  LEFT JOIN heartguard.roles r ON r.code = i.role_code
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
  label       VARCHAR(120) NOT NULL
);

ALTER TABLE IF EXISTS device_types ALTER COLUMN label SET NOT NULL;

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
CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(device_type_id);
CREATE INDEX IF NOT EXISTS idx_devices_owner ON devices(owner_patient_id);

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
CREATE INDEX IF NOT EXISTS idx_signal_streams_patient ON signal_streams(patient_id);
CREATE INDEX IF NOT EXISTS idx_signal_streams_device ON signal_streams(device_id);
CREATE INDEX IF NOT EXISTS idx_signal_streams_type ON signal_streams(signal_type_id);

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
CREATE INDEX IF NOT EXISTS idx_timeseries_binding_stream ON timeseries_binding(stream_id);

CREATE TABLE IF NOT EXISTS timeseries_binding_tag (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  binding_id UUID NOT NULL REFERENCES timeseries_binding(id) ON DELETE CASCADE,
  tag_key    VARCHAR(120) NOT NULL,
  tag_value  VARCHAR(240) NOT NULL,
  UNIQUE (binding_id, tag_key)
);
CREATE INDEX IF NOT EXISTS idx_timeseries_binding_tag_binding ON timeseries_binding_tag(binding_id);

CREATE OR REPLACE FUNCTION heartguard.sp_signal_streams_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  patient_id text,
  patient_name text,
  device_id text,
  device_serial text,
  signal_type_code text,
  signal_type_label text,
  sample_rate_hz numeric,
  started_at timestamp,
  ended_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    ss.id::text,
    ss.patient_id::text,
    pat.person_name::text,
    ss.device_id::text,
    dev.serial::text,
    st.code::text,
    st.label::text,
    ss.sample_rate_hz,
    ss.started_at,
    ss.ended_at
  FROM heartguard.signal_streams ss
  JOIN heartguard.patients pat ON pat.id = ss.patient_id
  JOIN heartguard.devices dev ON dev.id = ss.device_id
  JOIN heartguard.signal_types st ON st.id = ss.signal_type_id
  ORDER BY ss.started_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_signal_stream_create(
  p_patient_id uuid,
  p_device_id uuid,
  p_signal_type_code text,
  p_sample_rate numeric,
  p_started_at timestamp,
  p_ended_at timestamp)
RETURNS TABLE (
  id text,
  patient_id text,
  patient_name text,
  device_id text,
  device_serial text,
  signal_type_code text,
  signal_type_label text,
  sample_rate_hz numeric,
  started_at timestamp,
  ended_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_signal_type_id uuid;
BEGIN
  SELECT st.id INTO v_signal_type_id
  FROM heartguard.signal_types st
  WHERE lower(st.code) = lower(btrim(p_signal_type_code))
  LIMIT 1;
  IF v_signal_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de señal % no existe', p_signal_type_code USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  INSERT INTO heartguard.signal_streams AS ss (patient_id, device_id, signal_type_id, sample_rate_hz, started_at, ended_at)
  VALUES (p_patient_id, p_device_id, v_signal_type_id, p_sample_rate, p_started_at, p_ended_at)
  RETURNING
    ss.id::text,
    ss.patient_id::text,
    (SELECT pat.person_name::text FROM heartguard.patients pat WHERE pat.id = ss.patient_id),
    ss.device_id::text,
    (SELECT dev.serial::text FROM heartguard.devices dev WHERE dev.id = ss.device_id),
    (SELECT st.code::text FROM heartguard.signal_types st WHERE st.id = ss.signal_type_id),
    (SELECT st.label::text FROM heartguard.signal_types st WHERE st.id = ss.signal_type_id),
    ss.sample_rate_hz,
    ss.started_at,
    ss.ended_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_signal_stream_update(
  p_id uuid,
  p_patient_id uuid,
  p_device_id uuid,
  p_signal_type_code text,
  p_sample_rate numeric,
  p_started_at timestamp,
  p_ended_at timestamp)
RETURNS TABLE (
  id text,
  patient_id text,
  patient_name text,
  device_id text,
  device_serial text,
  signal_type_code text,
  signal_type_label text,
  sample_rate_hz numeric,
  started_at timestamp,
  ended_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_signal_type_id uuid;
BEGIN
  SELECT st.id INTO v_signal_type_id
  FROM heartguard.signal_types st
  WHERE lower(st.code) = lower(btrim(p_signal_type_code))
  LIMIT 1;
  IF v_signal_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de señal % no existe', p_signal_type_code USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  UPDATE heartguard.signal_streams AS ss
     SET patient_id = p_patient_id,
         device_id = p_device_id,
         signal_type_id = v_signal_type_id,
         sample_rate_hz = p_sample_rate,
         started_at = p_started_at,
         ended_at = p_ended_at
   WHERE ss.id = p_id
  RETURNING
    ss.id::text,
    ss.patient_id::text,
    (SELECT pat.person_name::text FROM heartguard.patients pat WHERE pat.id = ss.patient_id),
    ss.device_id::text,
    (SELECT dev.serial::text FROM heartguard.devices dev WHERE dev.id = ss.device_id),
    (SELECT st.code::text FROM heartguard.signal_types st WHERE st.id = ss.signal_type_id),
    (SELECT st.label::text FROM heartguard.signal_types st WHERE st.id = ss.signal_type_id),
    ss.sample_rate_hz,
    ss.started_at,
    ss.ended_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_signal_stream_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.signal_streams WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_devices_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  serial text,
  brand text,
  model text,
  device_type_code text,
  device_type_label text,
  owner_patient_id text,
  owner_patient_name text,
  registered_at timestamp,
  active boolean)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    d.id::text,
    d.org_id::text,
    o.name::text,
    d.serial::text,
    d.brand::text,
    d.model::text,
    dt.code::text,
    dt.label::text,
    d.owner_patient_id::text,
    p.person_name::text,
    d.registered_at,
    d.active
  FROM heartguard.devices d
  LEFT JOIN heartguard.organizations o ON o.id = d.org_id
  JOIN heartguard.device_types dt ON dt.id = d.device_type_id
  LEFT JOIN heartguard.patients p ON p.id = d.owner_patient_id
  ORDER BY d.registered_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_device_create(
  p_org_id uuid,
  p_serial text,
  p_brand text DEFAULT NULL,
  p_model text DEFAULT NULL,
  p_device_type_code text DEFAULT NULL,
  p_owner_patient_id uuid DEFAULT NULL,
  p_active boolean DEFAULT TRUE)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  serial text,
  brand text,
  model text,
  device_type_code text,
  device_type_label text,
  owner_patient_id text,
  owner_patient_name text,
  registered_at timestamp,
  active boolean)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_serial text;
  v_brand text;
  v_model text;
  v_type_id uuid;
BEGIN
  v_serial := NULLIF(btrim(p_serial), '');
  IF v_serial IS NULL THEN
    RAISE EXCEPTION 'Serie requerida' USING ERRCODE = '23514';
  END IF;

  SELECT dt.id INTO v_type_id
  FROM heartguard.device_types dt
  WHERE lower(dt.code) = lower(btrim(p_device_type_code))
  LIMIT 1;
  IF v_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de dispositivo % no existe', p_device_type_code USING ERRCODE = '23514';
  END IF;

  v_brand := NULLIF(btrim(p_brand), '');
  v_model := NULLIF(btrim(p_model), '');

  RETURN QUERY
  INSERT INTO heartguard.devices AS d (org_id, serial, brand, model, device_type_id, owner_patient_id, active)
  VALUES (p_org_id, v_serial, v_brand, v_model, v_type_id, p_owner_patient_id, COALESCE(p_active, TRUE))
  RETURNING
    d.id::text,
    d.org_id::text,
    (SELECT o.name::text FROM heartguard.organizations o WHERE o.id = d.org_id),
    d.serial::text,
    d.brand::text,
    d.model::text,
    (SELECT dt.code::text FROM heartguard.device_types dt WHERE dt.id = d.device_type_id),
    (SELECT dt.label::text FROM heartguard.device_types dt WHERE dt.id = d.device_type_id),
    d.owner_patient_id::text,
    (SELECT p.person_name::text FROM heartguard.patients p WHERE p.id = d.owner_patient_id),
    d.registered_at,
    d.active;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_device_update(
  p_id uuid,
  p_org_id uuid,
  p_serial text,
  p_brand text,
  p_model text,
  p_device_type_code text,
  p_owner_patient_id uuid,
  p_active boolean)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  serial text,
  brand text,
  model text,
  device_type_code text,
  device_type_label text,
  owner_patient_id text,
  owner_patient_name text,
  registered_at timestamp,
  active boolean)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_serial text;
  v_brand text;
  v_model text;
  v_type_id uuid;
BEGIN
  v_serial := NULLIF(btrim(p_serial), '');
  IF v_serial IS NULL THEN
    RAISE EXCEPTION 'Serie requerida' USING ERRCODE = '23514';
  END IF;

  SELECT dt.id INTO v_type_id
  FROM heartguard.device_types dt
  WHERE lower(dt.code) = lower(btrim(p_device_type_code))
  LIMIT 1;
  IF v_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de dispositivo % no existe', p_device_type_code USING ERRCODE = '23514';
  END IF;

  v_brand := NULLIF(btrim(p_brand), '');
  v_model := NULLIF(btrim(p_model), '');

  RETURN QUERY
  UPDATE heartguard.devices AS d
     SET org_id = COALESCE(p_org_id, d.org_id),
         serial = v_serial,
         brand = v_brand,
         model = v_model,
         device_type_id = v_type_id,
         owner_patient_id = p_owner_patient_id,
         active = COALESCE(p_active, d.active)
   WHERE d.id = p_id
  RETURNING
    d.id::text,
    d.org_id::text,
    (SELECT o.name::text FROM heartguard.organizations o WHERE o.id = d.org_id),
    d.serial::text,
    d.brand::text,
    d.model::text,
    (SELECT dt.code::text FROM heartguard.device_types dt WHERE dt.id = d.device_type_id),
    (SELECT dt.label::text FROM heartguard.device_types dt WHERE dt.id = d.device_type_id),
    d.owner_patient_id::text,
    (SELECT p.person_name::text FROM heartguard.patients p WHERE p.id = d.owner_patient_id),
    d.registered_at,
    d.active;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_device_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  -- Primero eliminar los signal_streams asociados (y sus cascadas: timeseries_binding, etc.)
  DELETE FROM heartguard.signal_streams WHERE device_id = p_id;
  
  -- Ahora eliminar el dispositivo
  DELETE FROM heartguard.devices WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

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

CREATE OR REPLACE FUNCTION heartguard.sp_models_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  name text,
  version text,
  task text,
  training_data_ref text,
  hyperparams text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    m.id::text,
    m.name::text,
    m.version::text,
    m.task::text,
    m.training_data_ref,
    CASE WHEN m.hyperparams IS NULL THEN NULL ELSE m.hyperparams::text END,
    m.created_at
  FROM heartguard.models m
  ORDER BY m.created_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_model_create(
  p_name text,
  p_version text,
  p_task text,
  p_training_data_ref text DEFAULT NULL,
  p_hyperparams jsonb DEFAULT NULL)
RETURNS TABLE (
  id text,
  name text,
  version text,
  task text,
  training_data_ref text,
  hyperparams text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_name text;
  v_version text;
  v_task text;
BEGIN
  v_name := NULLIF(btrim(p_name), '');
  v_version := NULLIF(btrim(p_version), '');
  v_task := NULLIF(btrim(p_task), '');
  IF v_name IS NULL OR v_version IS NULL OR v_task IS NULL THEN
    RAISE EXCEPTION 'Nombre, versión y tarea son obligatorios' USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  INSERT INTO heartguard.models AS m (name, version, task, training_data_ref, hyperparams)
  VALUES (v_name, v_version, v_task, NULLIF(btrim(p_training_data_ref), ''), p_hyperparams)
  RETURNING
    m.id::text,
    m.name::text,
    m.version::text,
    m.task::text,
    m.training_data_ref,
    CASE WHEN m.hyperparams IS NULL THEN NULL ELSE m.hyperparams::text END,
    m.created_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_model_update(
  p_id uuid,
  p_name text,
  p_version text,
  p_task text,
  p_training_data_ref text,
  p_hyperparams jsonb)
RETURNS TABLE (
  id text,
  name text,
  version text,
  task text,
  training_data_ref text,
  hyperparams text,
  created_at timestamp)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_name text;
  v_version text;
  v_task text;
BEGIN
  v_name := NULLIF(btrim(p_name), '');
  v_version := NULLIF(btrim(p_version), '');
  v_task := NULLIF(btrim(p_task), '');
  IF v_name IS NULL OR v_version IS NULL OR v_task IS NULL THEN
    RAISE EXCEPTION 'Nombre, versión y tarea son obligatorios' USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  UPDATE heartguard.models AS m
     SET name = v_name,
         version = v_version,
         task = v_task,
         training_data_ref = NULLIF(btrim(p_training_data_ref), ''),
         hyperparams = p_hyperparams
   WHERE m.id = p_id
  RETURNING
    m.id::text,
    m.name::text,
    m.version::text,
    m.task::text,
    m.training_data_ref,
    CASE WHEN m.hyperparams IS NULL THEN NULL ELSE m.hyperparams::text END,
    m.created_at;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_model_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.models WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

CREATE TABLE IF NOT EXISTS event_types (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code                VARCHAR(40) NOT NULL UNIQUE,
  description         TEXT,
  severity_default_id UUID NOT NULL REFERENCES alert_levels(id) ON DELETE RESTRICT
);
CREATE INDEX IF NOT EXISTS idx_event_types_severity ON event_types(severity_default_id);

CREATE OR REPLACE FUNCTION heartguard.sp_event_types_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  code text,
  description text,
  severity_code text,
  severity_label text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 200);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    et.id::text,
    et.code::text,
    et.description,
    al.code::text,
    al.label::text
  FROM heartguard.event_types et
  JOIN heartguard.alert_levels al ON al.id = et.severity_default_id
  ORDER BY et.code
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_event_type_create(
  p_code text,
  p_description text DEFAULT NULL,
  p_severity_code text DEFAULT NULL)
RETURNS TABLE (
  id text,
  code text,
  description text,
  severity_code text,
  severity_label text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_code text;
  v_desc text;
  v_severity_id uuid;
BEGIN
  v_code := lower(NULLIF(btrim(p_code), ''));
  IF v_code IS NULL THEN
    RAISE EXCEPTION 'Código requerido' USING ERRCODE = '23514';
  END IF;

  SELECT al.id INTO v_severity_id
  FROM heartguard.alert_levels al
  WHERE lower(al.code) = lower(btrim(p_severity_code))
  LIMIT 1;
  IF v_severity_id IS NULL THEN
    RAISE EXCEPTION 'Nivel de alerta % no existe', p_severity_code USING ERRCODE = '23514';
  END IF;

  v_desc := NULLIF(btrim(p_description), '');

  RETURN QUERY
  INSERT INTO heartguard.event_types AS et (code, description, severity_default_id)
  VALUES (v_code, v_desc, v_severity_id)
  RETURNING
    et.id::text,
    et.code::text,
    et.description,
    (SELECT al.code::text FROM heartguard.alert_levels al WHERE al.id = et.severity_default_id),
    (SELECT al.label::text FROM heartguard.alert_levels al WHERE al.id = et.severity_default_id);
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_event_type_update(
  p_id uuid,
  p_code text,
  p_description text,
  p_severity_code text)
RETURNS TABLE (
  id text,
  code text,
  description text,
  severity_code text,
  severity_label text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_code text;
  v_desc text;
  v_severity_id uuid;
BEGIN
  v_code := lower(NULLIF(btrim(p_code), ''));
  IF v_code IS NULL THEN
    RAISE EXCEPTION 'Código requerido' USING ERRCODE = '23514';
  END IF;

  SELECT al.id INTO v_severity_id
  FROM heartguard.alert_levels al
  WHERE lower(al.code) = lower(btrim(p_severity_code))
  LIMIT 1;
  IF v_severity_id IS NULL THEN
    RAISE EXCEPTION 'Nivel de alerta % no existe', p_severity_code USING ERRCODE = '23514';
  END IF;

  v_desc := NULLIF(btrim(p_description), '');

  RETURN QUERY
  UPDATE heartguard.event_types AS et
     SET code = v_code,
         description = v_desc,
         severity_default_id = v_severity_id
   WHERE et.id = p_id
  RETURNING
    et.id::text,
    et.code::text,
    et.description,
    (SELECT al.code::text FROM heartguard.alert_levels al WHERE al.id = et.severity_default_id),
    (SELECT al.label::text FROM heartguard.alert_levels al WHERE al.id = et.severity_default_id);
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_event_type_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.event_types WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

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
CREATE INDEX IF NOT EXISTS idx_inferences_model ON inferences(model_id);
CREATE INDEX IF NOT EXISTS idx_inferences_event ON inferences(predicted_event_id);

CREATE OR REPLACE FUNCTION heartguard.sp_inferences_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0)
RETURNS TABLE (
  id text,
  model_id text,
  model_name text,
  stream_id text,
  patient_name text,
  device_serial text,
  event_code text,
  event_label text,
  window_start timestamp,
  window_end timestamp,
  score numeric,
  threshold numeric,
  created_at timestamp,
  series_ref text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    inf.id::text,
    inf.model_id::text,
    m.name::text,
    inf.stream_id::text,
    pat.person_name::text,
    dev.serial::text,
    et.code::text,
    et.description,
    inf.window_start,
    inf.window_end,
    inf.score,
    inf.threshold,
    inf.created_at,
    inf.series_ref
  FROM heartguard.inferences inf
  JOIN heartguard.signal_streams ss ON ss.id = inf.stream_id
  JOIN heartguard.patients pat ON pat.id = ss.patient_id
  JOIN heartguard.devices dev ON dev.id = ss.device_id
  JOIN heartguard.event_types et ON et.id = inf.predicted_event_id
  LEFT JOIN heartguard.models m ON m.id = inf.model_id
  ORDER BY inf.created_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_inference_create(
  p_model_id uuid,
  p_stream_id uuid,
  p_window_start timestamp,
  p_window_end timestamp,
  p_event_code text,
  p_score numeric,
  p_threshold numeric,
  p_metadata jsonb DEFAULT NULL,
  p_series_ref text DEFAULT NULL,
  p_feature_snapshot jsonb DEFAULT NULL)
RETURNS TABLE (
  id text,
  model_id text,
  model_name text,
  stream_id text,
  patient_name text,
  device_serial text,
  event_code text,
  event_label text,
  window_start timestamp,
  window_end timestamp,
  score numeric,
  threshold numeric,
  created_at timestamp,
  series_ref text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_event_id uuid;
BEGIN
  IF p_window_end <= p_window_start THEN
    RAISE EXCEPTION 'La ventana debe ser válida' USING ERRCODE = '23514';
  END IF;

  SELECT et.id INTO v_event_id
  FROM heartguard.event_types et
  WHERE lower(et.code) = lower(btrim(p_event_code))
  LIMIT 1;
  IF v_event_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de evento % no existe', p_event_code USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  INSERT INTO heartguard.inferences AS inf (model_id, stream_id, window_start, window_end, predicted_event_id, score, threshold, metadata, series_ref, feature_snapshot)
  VALUES (p_model_id, p_stream_id, p_window_start, p_window_end, v_event_id, p_score, p_threshold, p_metadata, NULLIF(btrim(p_series_ref), ''), p_feature_snapshot)
  RETURNING
    inf.id::text,
    inf.model_id::text,
    (SELECT m.name::text FROM heartguard.models m WHERE m.id = inf.model_id),
    inf.stream_id::text,
    (SELECT pat.person_name::text FROM heartguard.patients pat JOIN heartguard.signal_streams ss ON ss.patient_id = pat.id WHERE ss.id = inf.stream_id),
    (SELECT dev.serial::text FROM heartguard.devices dev JOIN heartguard.signal_streams ss ON ss.device_id = dev.id WHERE ss.id = inf.stream_id),
    (SELECT et.code::text FROM heartguard.event_types et WHERE et.id = inf.predicted_event_id),
    (SELECT et.description FROM heartguard.event_types et WHERE et.id = inf.predicted_event_id),
    inf.window_start,
    inf.window_end,
    inf.score,
    inf.threshold,
    inf.created_at,
    inf.series_ref;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_inference_update(
  p_id uuid,
  p_model_id uuid,
  p_stream_id uuid,
  p_window_start timestamp,
  p_window_end timestamp,
  p_event_code text,
  p_score numeric,
  p_threshold numeric,
  p_metadata jsonb,
  p_series_ref text,
  p_feature_snapshot jsonb)
RETURNS TABLE (
  id text,
  model_id text,
  model_name text,
  stream_id text,
  patient_name text,
  device_serial text,
  event_code text,
  event_label text,
  window_start timestamp,
  window_end timestamp,
  score numeric,
  threshold numeric,
  created_at timestamp,
  series_ref text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_event_id uuid;
BEGIN
  IF p_window_end <= p_window_start THEN
    RAISE EXCEPTION 'La ventana debe ser válida' USING ERRCODE = '23514';
  END IF;

  SELECT et.id INTO v_event_id
  FROM heartguard.event_types et
  WHERE lower(et.code) = lower(btrim(p_event_code))
  LIMIT 1;
  IF v_event_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de evento % no existe', p_event_code USING ERRCODE = '23514';
  END IF;

  RETURN QUERY
  UPDATE heartguard.inferences AS inf
     SET model_id = p_model_id,
         stream_id = p_stream_id,
         window_start = p_window_start,
         window_end = p_window_end,
         predicted_event_id = v_event_id,
         score = p_score,
         threshold = p_threshold,
         metadata = p_metadata,
         series_ref = NULLIF(btrim(p_series_ref), ''),
         feature_snapshot = p_feature_snapshot
   WHERE inf.id = p_id
  RETURNING
    inf.id::text,
    inf.model_id::text,
    (SELECT m.name::text FROM heartguard.models m WHERE m.id = inf.model_id),
    inf.stream_id::text,
    (SELECT pat.person_name::text FROM heartguard.patients pat JOIN heartguard.signal_streams ss ON ss.patient_id = pat.id WHERE ss.id = inf.stream_id),
    (SELECT dev.serial::text FROM heartguard.devices dev JOIN heartguard.signal_streams ss ON ss.device_id = dev.id WHERE ss.id = inf.stream_id),
    (SELECT et.code::text FROM heartguard.event_types et WHERE et.id = inf.predicted_event_id),
    (SELECT et.description FROM heartguard.event_types et WHERE et.id = inf.predicted_event_id),
    inf.window_start,
    inf.window_end,
    inf.score,
    inf.threshold,
    inf.created_at,
    inf.series_ref;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_inference_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.inferences WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

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
CREATE INDEX IF NOT EXISTS idx_ground_truth_patient ON ground_truth_labels(patient_id);
CREATE INDEX IF NOT EXISTS idx_ground_truth_event_type ON ground_truth_labels(event_type_id);
CREATE INDEX IF NOT EXISTS idx_ground_truth_user ON ground_truth_labels(annotated_by_user_id);

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
CREATE INDEX IF NOT EXISTS idx_alert_types_sev_min ON alert_types(severity_min_id);
CREATE INDEX IF NOT EXISTS idx_alert_types_sev_max ON alert_types(severity_max_id);

CREATE TABLE IF NOT EXISTS alert_status (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code        VARCHAR(30) NOT NULL UNIQUE,
  description TEXT,
  step_order  INT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
CREATE INDEX IF NOT EXISTS idx_alerts_patient_status ON alerts(patient_id, status_id);
CREATE INDEX IF NOT EXISTS idx_alerts_level ON alerts(alert_level_id);
CREATE INDEX IF NOT EXISTS idx_alerts_loc_gix ON alerts USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type_id);
CREATE INDEX IF NOT EXISTS idx_alerts_model ON alerts(created_by_model_id);
CREATE INDEX IF NOT EXISTS idx_alerts_inference ON alerts(source_inference_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status_id);
CREATE INDEX IF NOT EXISTS idx_alerts_duplicate ON alerts(duplicate_of_alert_id);

CREATE OR REPLACE FUNCTION heartguard.sp_alerts_list(
  p_limit integer DEFAULT 100,
  p_offset integer DEFAULT 0,
  p_from timestamp DEFAULT NULL,
  p_to timestamp DEFAULT NULL)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  patient_id text,
  patient_name text,
  alert_type_code text,
  alert_type_label text,
  level_code text,
  level_label text,
  status_code text,
  status_label text,
  created_at timestamp,
  description text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  safe_limit integer := LEAST(GREATEST(p_limit, 1), 500);
  safe_offset integer := GREATEST(p_offset, 0);
BEGIN
  RETURN QUERY
  SELECT
    a.id::text,
    p.org_id::text,
    o.name::text,
    a.patient_id::text,
    p.person_name::text,
    at.code::text,
    at.description,
    al.code::text,
    al.label::text,
    ast.code::text,
    ast.description,
    a.created_at,
    a.description
  FROM heartguard.alerts a
  JOIN heartguard.patients p ON p.id = a.patient_id
  LEFT JOIN heartguard.organizations o ON o.id = p.org_id
  JOIN heartguard.alert_types at ON at.id = a.type_id
  JOIN heartguard.alert_levels al ON al.id = a.alert_level_id
  JOIN heartguard.alert_status ast ON ast.id = a.status_id
  WHERE (p_from IS NULL OR a.created_at >= p_from)
    AND (p_to IS NULL OR a.created_at <= p_to)
  ORDER BY a.created_at DESC
  LIMIT safe_limit OFFSET safe_offset;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_alert_create(
  p_patient_id uuid,
  p_alert_type_code text,
  p_alert_level_code text,
  p_status_code text,
  p_model_id uuid,
  p_inference_id uuid,
  p_description text,
  p_location_wkt text)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  patient_id text,
  patient_name text,
  alert_type_code text,
  alert_type_label text,
  level_code text,
  level_label text,
  status_code text,
  status_label text,
  created_at timestamp,
  description text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_type_id uuid;
  v_level_id uuid;
  v_status_id uuid;
  v_location geometry(Point,4326);
BEGIN
  SELECT at.id INTO v_type_id
  FROM heartguard.alert_types at
  WHERE lower(at.code) = lower(btrim(p_alert_type_code))
  LIMIT 1;
  IF v_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de alerta % no existe', p_alert_type_code USING ERRCODE = '23514';
  END IF;

  SELECT al.id INTO v_level_id
  FROM heartguard.alert_levels al
  WHERE lower(al.code) = lower(btrim(p_alert_level_code))
  LIMIT 1;
  IF v_level_id IS NULL THEN
    RAISE EXCEPTION 'Nivel de alerta % no existe', p_alert_level_code USING ERRCODE = '23514';
  END IF;

  SELECT ast.id INTO v_status_id
  FROM heartguard.alert_status ast
  WHERE lower(ast.code) = lower(btrim(p_status_code))
  LIMIT 1;
  IF v_status_id IS NULL THEN
    RAISE EXCEPTION 'Estatus de alerta % no existe', p_status_code USING ERRCODE = '23514';
  END IF;

  IF p_location_wkt IS NOT NULL AND btrim(p_location_wkt) <> '' THEN
    v_location := ST_GeomFromText(p_location_wkt, 4326);
  END IF;

  RETURN QUERY
  WITH inserted_alert AS (
    INSERT INTO heartguard.alerts AS a (patient_id, type_id, created_by_model_id, source_inference_id, alert_level_id, status_id, description, location)
    VALUES (p_patient_id, v_type_id, p_model_id, p_inference_id, v_level_id, v_status_id, NULLIF(btrim(p_description), ''), v_location)
    RETURNING a.id, a.patient_id, a.type_id, a.alert_level_id, a.status_id, a.created_at, a.description
  )
  SELECT
    ia.id::text,
    p.org_id::text,
    o.name::text,
    ia.patient_id::text,
    p.person_name::text,
    at.code::text,
    at.description,
    al.code::text,
    al.label::text,
    ast.code::text,
    ast.description,
    ia.created_at,
    ia.description
  FROM inserted_alert ia
  JOIN heartguard.patients p ON p.id = ia.patient_id
  LEFT JOIN heartguard.organizations o ON o.id = p.org_id
  JOIN heartguard.alert_types at ON at.id = ia.type_id
  JOIN heartguard.alert_levels al ON al.id = ia.alert_level_id
  JOIN heartguard.alert_status ast ON ast.id = ia.status_id;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_alert_update(
  p_id uuid,
  p_alert_type_code text,
  p_alert_level_code text,
  p_status_code text,
  p_model_id uuid,
  p_inference_id uuid,
  p_description text,
  p_location_wkt text)
RETURNS TABLE (
  id text,
  org_id text,
  org_name text,
  patient_id text,
  patient_name text,
  alert_type_code text,
  alert_type_label text,
  level_code text,
  level_label text,
  status_code text,
  status_label text,
  created_at timestamp,
  description text)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_type_id uuid;
  v_level_id uuid;
  v_status_id uuid;
  v_location geometry(Point,4326);
BEGIN
  SELECT at.id INTO v_type_id
  FROM heartguard.alert_types at
  WHERE lower(at.code) = lower(btrim(p_alert_type_code))
  LIMIT 1;
  IF v_type_id IS NULL THEN
    RAISE EXCEPTION 'Tipo de alerta % no existe', p_alert_type_code USING ERRCODE = '23514';
  END IF;

  SELECT al.id INTO v_level_id
  FROM heartguard.alert_levels al
  WHERE lower(al.code) = lower(btrim(p_alert_level_code))
  LIMIT 1;
  IF v_level_id IS NULL THEN
    RAISE EXCEPTION 'Nivel de alerta % no existe', p_alert_level_code USING ERRCODE = '23514';
  END IF;

  SELECT ast.id INTO v_status_id
  FROM heartguard.alert_status ast
  WHERE lower(ast.code) = lower(btrim(p_status_code))
  LIMIT 1;
  IF v_status_id IS NULL THEN
    RAISE EXCEPTION 'Estatus de alerta % no existe', p_status_code USING ERRCODE = '23514';
  END IF;

  IF p_location_wkt IS NOT NULL AND btrim(p_location_wkt) <> '' THEN
    v_location := ST_GeomFromText(p_location_wkt, 4326);
  ELSE
    v_location := NULL;
  END IF;

  RETURN QUERY
  WITH updated_alert AS (
    UPDATE heartguard.alerts AS a
       SET type_id = v_type_id,
           alert_level_id = v_level_id,
           status_id = v_status_id,
           created_by_model_id = p_model_id,
           source_inference_id = p_inference_id,
           description = NULLIF(btrim(p_description), ''),
           location = v_location
     WHERE a.id = p_id
    RETURNING a.id, a.patient_id, a.type_id, a.alert_level_id, a.status_id, a.created_at, a.description
  )
  SELECT
    ua.id::text,
    p.org_id::text,
    o.name::text,
    ua.patient_id::text,
    p.person_name::text,
    at.code::text,
    at.description,
    al.code::text,
    al.label::text,
    ast.code::text,
    ast.description,
    ua.created_at,
    ua.description
  FROM updated_alert ua
  JOIN heartguard.patients p ON p.id = ua.patient_id
  LEFT JOIN heartguard.organizations o ON o.id = p.org_id
  JOIN heartguard.alert_types at ON at.id = ua.type_id
  JOIN heartguard.alert_levels al ON al.id = ua.alert_level_id
  JOIN heartguard.alert_status ast ON ast.id = ua.status_id;
END;
$$;

CREATE OR REPLACE FUNCTION heartguard.sp_alert_delete(
  p_id uuid)
RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  rows_deleted integer;
BEGIN
  DELETE FROM heartguard.alerts WHERE id = p_id;
  GET DIAGNOSTICS rows_deleted = ROW_COUNT;
  RETURN rows_deleted > 0;
END;
$$;

CREATE TABLE IF NOT EXISTS alert_assignment (
  alert_id            UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  assignee_user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  assigned_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  assigned_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY(alert_id, assignee_user_id, assigned_at)
);
CREATE INDEX IF NOT EXISTS idx_alert_assignment_by ON alert_assignment(assigned_by_user_id);

CREATE TABLE IF NOT EXISTS alert_ack (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id        UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  ack_by_user_id  UUID REFERENCES users(id) ON DELETE SET NULL,
  ack_at          TIMESTAMP NOT NULL DEFAULT NOW(),
  note            TEXT
);
CREATE INDEX IF NOT EXISTS idx_alert_ack_alert ON alert_ack(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_ack_user ON alert_ack(ack_by_user_id);

CREATE TABLE IF NOT EXISTS alert_resolution (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  alert_id            UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
  resolved_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  resolved_at         TIMESTAMP NOT NULL DEFAULT NOW(),
  outcome             VARCHAR(80),
  note                TEXT
);
CREATE INDEX IF NOT EXISTS idx_alert_resolution_alert ON alert_resolution(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_resolution_user ON alert_resolution(resolved_by_user_id);

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
CREATE INDEX IF NOT EXISTS idx_delivery_status ON alert_delivery(delivery_status_id);

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
CREATE INDEX IF NOT EXISTS idx_service_health_status ON service_health(service_status_id);

-- Stored procedure para métricas del panel
-- Stored procedure para métricas del panel
CREATE OR REPLACE FUNCTION heartguard.sp_metrics_overview()
RETURNS TABLE (
  avg_response_ms numeric,
  avg_ack_duration interval,
  avg_resolve_duration interval, -- Ajustado para usar pgtype.Interval
  total_users integer,
  total_orgs integer,
  total_memberships integer,
  pending_invitations integer,
  operations jsonb,
  unassigned_alerts_count integer,
  active_patients_count integer,
  disconnected_devices_count integer)
LANGUAGE plpgsql SECURITY DEFINER
AS $$
DECLARE
  v_avg numeric;
  v_mtta interval;
  v_mttr interval;
  v_users integer;
  v_orgs integer;
  v_memberships integer;
  v_pending integer;
  v_ops jsonb;
  v_unassigned integer;
  v_active_patients integer;
  v_disconnected integer;
BEGIN
  SELECT AVG(latency_ms) INTO v_avg
  FROM heartguard.service_health
  WHERE checked_at > NOW() - INTERVAL '7 days';

  -- MTTA: promedio de tiempo de acuse de alertas
  SELECT AVG(ack.ack_at - a.created_at) INTO v_mtta
  FROM heartguard.alerts a
  JOIN heartguard.alert_ack ack ON ack.alert_id = a.id
    AND ack.ack_at IS NOT NULL
    AND a.created_at IS NOT NULL;

  -- MTTR: promedio de tiempo de resolución basado en alert_resolution
  -- Calcula el tiempo promedio desde que se crea una alerta hasta que se resuelve
  -- Solo considera alertas que tienen una entrada en alert_resolution con resolved_at posterior a created_at
  SELECT AVG(ar.resolved_at - a.created_at) INTO v_mttr
  FROM heartguard.alerts a
  INNER JOIN heartguard.alert_resolution ar ON ar.alert_id = a.id
  WHERE ar.resolved_at IS NOT NULL
    AND a.created_at IS NOT NULL
    AND ar.resolved_at > a.created_at;

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

  -- Alerts without any assignment and still in 'created' status
  SELECT COUNT(*) INTO v_unassigned
  FROM heartguard.alerts a
  WHERE NOT EXISTS (SELECT 1 FROM heartguard.alert_assignment aa WHERE aa.alert_id = a.id)
    AND a.status_id = (SELECT id FROM heartguard.alert_status WHERE code = 'created');

  -- Active patients: patients with signal streams started in the last 7 days
  SELECT COUNT(DISTINCT ss.patient_id)::integer INTO v_active_patients
  FROM heartguard.signal_streams ss
  WHERE ss.started_at > NOW() - INTERVAL '7 days';

  -- Disconnected devices: active devices with no recent streams in last 24 hours
  SELECT COUNT(*)::integer INTO v_disconnected
  FROM heartguard.devices d
  WHERE d.active = TRUE
    AND NOT EXISTS (
      SELECT 1 FROM heartguard.signal_streams ss
      WHERE ss.device_id = d.id AND ss.started_at > NOW() - INTERVAL '24 hours'
    );

  avg_response_ms := COALESCE(v_avg, 0);
  avg_ack_duration := COALESCE(v_mtta, interval '0');
  avg_resolve_duration := COALESCE(v_mttr, interval '0'); -- Asignar v_mttr a la columna de salida
  total_users := COALESCE(v_users, 0);
  total_orgs := COALESCE(v_orgs, 0);
  total_memberships := COALESCE(v_memberships, 0);
  pending_invitations := COALESCE(v_pending, 0);
  operations := COALESCE(v_ops, '[]'::jsonb);
  unassigned_alerts_count := COALESCE(v_unassigned, 0);
  active_patients_count := COALESCE(v_active_patients, 0);
  disconnected_devices_count := COALESCE(v_disconnected, 0);
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
        WHEN i.revoked_at IS NOT NULL THEN 'revoked'
        WHEN i.used_at IS NOT NULL THEN 'used'
        WHEN i.expires_at <= NOW() THEN 'expired'
        ELSE 'pending'
      END::text AS status_value
    FROM heartguard.org_invitations i
  ),
  aggregated AS (
    SELECT
      s.status_value,
      COUNT(*)::integer AS total
    FROM status_map s
    GROUP BY s.status_value
  )
  SELECT
    s.status_value::text,
    CASE s.status_value
      WHEN 'pending' THEN 'Pendientes'
      WHEN 'used' THEN 'Utilizadas'
      WHEN 'expired' THEN 'Expiradas'
      WHEN 'revoked' THEN 'Revocadas'
      ELSE INITCAP(s.status_value)
    END::text AS label,
    s.total
  FROM aggregated s
  ORDER BY s.total DESC;
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
  user_id uuid,
  name text,
  email text,
  status_code text,
  status_label text,
  created_at timestamp,
  first_action timestamp,
  last_action timestamp,
  actions_count integer,
  distinct_actions integer,
  org_memberships integer,
  total_count integer)
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
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_id);

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
