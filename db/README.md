# HeartGuard DB

## Prerrequisitos

- **Docker y Docker Compose**
- **Make** (instalado por defecto en la mayoría de distros Linux)
- **Opcional:** cliente `psql` en el host, para pruebas rápidas

## Estructura del repositorio

```text
HeartGuard/
├─ db/
│  ├─ init.sql         # crea roles, DB, esquema y tablas
│  └─ seed.sql         # carga datos base (roles, permisos, tipos, usuario demo)
├─ scripts/
│  ├─ db-reset.sh      # helper para limpiar y recrear
│  └─ db-health.sh     # verifica estado de la DB
├─ docker-compose.yml  # servicio Postgres+PostGIS
├─ .env.example        # variables de entorno de ejemplo
├─ .env                # copia editada con credenciales reales
├─ Makefile            # comandos de conveniencia
└─ README.txt
```

## Setup desde cero

1. **Copia el archivo de entorno y edítalo:**
   ```sh
   cp .env.example .env
   nano .env
   ```

2. **Levanta la base en Docker:**
   ```sh
   docker compose up -d
   ```

3. **Inicializa la base de datos:**
   ```sh
   make db-init
   ```

4. **Carga datos de ejemplo (semillas):**
   ```sh
   make db-seed
   ```

5. **Verifica el estado:**
   ```sh
   make db-health
   ```

## Reset total

Para limpiar y recrear todo (drop + init + seed):

```sh
make db-reset
```

## Conexión desde aplicaciones

Utiliza la variable estándar `DATABASE_URL`:

```
postgres://heartguard_app:dev_change_me@127.0.0.1:5432/heartguard?sslmode=disable
```

## Tips

- El contenedor expone **5432** (cambia en `docker-compose.yml` si ya tienes un Postgres local).
- Los scripts usan el superusuario definido en `.env` (`PGSUPER` / `PGSUPER_PASS`).
- El usuario demo creado es **admin@heartguard.com** (password hash de ejemplo en `seed.sql`, cámbialo para producción).
- Para probar rápido:
  ```sh
  make db-psql
  ```

## Demo data (smoke test)

Para insertar un paciente y alerta demo:

```sql
psql "$DATABASE_URL" <<'SQL'
INSERT INTO organizations(code, name) VALUES ('FAM-001', 'Familia Demo') ON CONFLICT DO NOTHING;
WITH o AS (SELECT id FROM organizations WHERE code='FAM-001')
INSERT INTO patients(org_id, person_name, birthdate)
SELECT o.id, 'Paciente Demo', '1980-01-01' FROM o ON CONFLICT DO NOTHING;
WITH p AS (SELECT id FROM patients WHERE person_name='Paciente Demo'),
     t AS (SELECT id FROM alert_types WHERE code='ARRHYTHMIA'),
     s AS (SELECT id FROM alert_status WHERE code='created'),
     l AS (SELECT id FROM alert_levels WHERE code='high')
INSERT INTO alerts(patient_id, type_id, status_id, alert_level_id, description, created_at)
SELECT p.id, t.id, s.id, l.id, 'Prueba de alerta', NOW()
FROM p, t, s, l ON CONFLICT DO NOTHING;
SELECT * FROM v_patient_active_alerts;
SQL
```

## Notas de Docker y solución de problemas comunes

### Puerto 5432 ocupado

- Si el puerto **5432** ya está en uso por otro PostgreSQL en tu host, tienes dos opciones:
   1. **Cambiar el mapeo de puerto** en `docker-compose.yml` (por ejemplo `5433:5432`) y ajustar `PGPORT` en `.env`.
   2. **Detener el servicio de PostgreSQL** del host:
       ```sh
       sudo systemctl stop postgresql
       sudo systemctl disable postgresql
       ```

### Cambios en configuración

- Si modificas `docker-compose.yml` (puertos, variables de entorno, etc.), reinicia todo:
   ```sh
   docker compose down
   docker compose up -d --build
   ```

### Logs y acceso al contenedor

- Para ver los **logs** del contenedor de Postgres:
   ```sh
   docker compose logs -f postgres
   ```
- Para **entrar al contenedor** y abrir `psql` como superusuario:
   ```sh
   docker exec -it heartguard-postgres psql -U postgres
   ```

### Borrar datos y volúmenes

- Para borrar todos los datos de Postgres (incluyendo el volumen persistente):
   ```sh
   docker compose down -v
   ```
   > ⚠️ Esto elimina el volumen `postgres_data`. Úsalo solo si quieres empezar desde cero.

### Permisos de archivos

- Si tienes errores de permisos con los scripts `.sql`, asegúrate de que no tengan permisos restrictivos:
   ```sh
   chmod 644 db/*.sql
   chmod 755 scripts/*.sh
   ```

### Cambios de contraseñas

- Si cambias el password de `PGSUPER` o `DBUSER` en `.env`, recuerda también actualizar `docker-compose.yml` (`POSTGRES_PASSWORD`) y recrear la base con:
   ```sh
   make db-reset
   ```

### Comprobar salud del contenedor

- Para comprobar la salud del contenedor:
   ```sh
   docker compose ps
   ```
   El estado debe marcar **"healthy"**.
