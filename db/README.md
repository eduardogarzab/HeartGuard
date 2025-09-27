# HeartGuard DB — PostgreSQL + PostGIS

## Propósito
- Esquema clínico y de operaciones.
- Catálogos y seguridad básica.
- Vistas de conveniencia para alertas activas.

## Requisitos
- **Docker + Compose**
- **Make**
- **Extensiones:** `postgis`, `pgcrypto`

## Variables (desde `.env` raíz)
- `PGSUPER`, `PGSUPER_PASS`
- `PGHOST`, `PGPORT`
- `DBNAME`, `DBUSER`, `DBPASS`
- `DATABASE_URL`

## Comandos principales
```sh
docker compose up -d
make db-init
make db-seed
make db-health
make db-reset
make db-psql
```

## DSN de conexión
```
postgres://heartguard_app:dev_change_me@127.0.0.1:5432/heartguard?sslmode=disable
```

## Smoke test
```sh
export $(grep -v '^#' .env | xargs)
psql "$DATABASE_URL" <<'SQL'
INSERT INTO organizations(code, name)
VALUES ('FAM-001', 'Familia Demo')
ON CONFLICT DO NOTHING;

WITH o AS (SELECT id FROM organizations WHERE code='FAM-001')
INSERT INTO patients(org_id, person_name, birthdate)
SELECT o.id, 'Paciente Demo', '1980-01-01' FROM o
ON CONFLICT DO NOTHING;

WITH p AS (SELECT id FROM patients WHERE person_name='Paciente Demo'),
   t AS (SELECT id FROM alert_types WHERE code='ARRHYTHMIA'),
   s AS (SELECT id FROM alert_status WHERE code='created'),
   l AS (SELECT id FROM alert_levels WHERE code='high')
INSERT INTO alerts(patient_id, type_id, status_id, alert_level_id, description, created_at)
SELECT p.id, t.id, s.id, l.id, 'Prueba de alerta', NOW()
FROM p, t, s, l
ON CONFLICT DO NOTHING;

SELECT * FROM v_patient_active_alerts;
SQL
```

## Solución de problemas
- **Puerto ocupado:** cambia mapeo en `docker-compose.yml`
- **Borrar datos:** `docker compose down -v`
- **Logs:** `docker compose logs -f postgres`
- **Entrar al contenedor:** `docker exec -it heartguard-postgres psql -U postgres`
