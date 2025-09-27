# HeartGuard — Monorepo (DB + Superadmin API)

## Descripción

Proyecto de demo: plataforma de monitoreo y alertas de riesgo cardiovascular.  
Este monorepo contiene la base de datos (**PostgreSQL + PostGIS**) y el backend Superadmin en **Go**.

---

## Estructura

- `db/` — SQL de inicialización y semillas
- `backend/` — Superadmin API en Go
- `docker-compose.yml` — Postgres para desarrollo
- `Makefile` — Comandos para DB y backend (unificado)
- `.env.example` — Variables de entorno de ejemplo
- `.env` — Copia editable (**no subir a git**)

---

## Requisitos

- Docker + Docker Compose
- Make
- Go 1.22+
- (Opcional) psql y jq

---

## Variables de entorno

- `PGSUPER`, `PGSUPER_PASS`, `PGHOST`, `PGPORT`
- `DBNAME`, `DBUSER`, `DBPASS`
- `DATABASE_URL` (cadena literal completa)
- `ENV`, `HTTP_ADDR`, `SUPERADMIN_TEST_TOKEN`, `ACCESS_TOKEN_SECRET`

---

## Pasos desde cero

1. **Copiar variables y editarlas:**
   ```sh
   cp .env.example .env
   nano .env
   ```
2. **Levantar Postgres:**
   ```sh
   docker compose up -d
   ```
3. **Inicializar y sembrar la DB:**
   ```sh
   make db-init
   make db-seed
   make db-health
   ```
4. **Ejecutar el backend:**
   ```sh
   make dev
   ```
5. **Probar health del backend:**
   ```sh
   curl -i http://localhost:8080/healthz
   ```

---

## Notas útiles

- Si el puerto `5432` está ocupado, cambia el mapeo en `docker-compose.yml` y en `.env`
- `make db-reset` elimina y recrea todo
- Instalar jq en Ubuntu:  
  ```sh
  sudo apt install jq
  ```

---

## Troubleshooting

- **“DATABASE_URL is required”**  
  ```sh
  export $(grep -v '^#' .env | xargs)
  ```
- **“missing go.sum entry”**  
  ```sh
  go mod tidy
  ```
