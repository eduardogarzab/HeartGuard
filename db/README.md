# HeartGuard Database (PostgreSQL + PostGIS)

## Descripción

Módulo de base de datos para HeartGuard que define el esquema principal, catálogos, roles, usuarios, seeds y extensiones necesarias para el sistema de monitoreo y alertas.

---

## Tecnologías

- **PostgreSQL 14+**
- **PostGIS**
- **pgcrypto** (UUIDs y bcrypt para hashes)
- **Docker** (opcional para desarrollo)

---

## Estructura

```
db/
├── init.sql        # Creación de esquema, extensiones, roles y tablas
├── seed.sql        # Datos iniciales (catálogos, roles, permisos, superadmin demo)
└── migrations/     # Directorio opcional para futuras migraciones
```

---

## Requisitos

- Docker + Docker Compose
- Make
- psql (opcional fuera de Docker)

---

## Variables de entorno

Ver archivo `.env`:

- `PGSUPER`, `PGSUPER_PASS`, `PGHOST`, `PGPORT`
- `DBNAME`, `DBUSER`, `DBPASS`
- `DATABASE_URL` (cadena completa)

---

## Comandos principales (`Makefile`)

| Comando         | Descripción                                                        |
|-----------------|--------------------------------------------------------------------|
| `make db-init`  | Inicializar la base de datos                                       |
| `make db-seed`  | Cargar datos iniciales (catálogos, roles, superadmin demo)         |
| `make db-health`| Verificar estado (healthcheck básico y conteos)                    |
| `make db-reset` | Resetear base de datos                                             |
| `make db-psql`  | Abrir cliente interactivo                                          |

---

## Usuario Superadmin de Demo

Se incluye automáticamente al ejecutar el seed:

- **Email:** `admin@heartguard.com`
- **Password:** `Admin#2025`
- **Rol:** `superadmin`
- **Estado:** `activo`

La contraseña se genera en cada seed con pgcrypto/bcrypt para garantizar acceso estable en entornos de demo.

---

## Notas

- No usar este usuario en producción (solo para demo).
- Para cambiar credenciales en producción, ajustar `seed.sql`.
- PostGIS es requerido aunque algunas tablas iniciales no lo usen (compatibilidad futura).
- Los catálogos y roles utilizan `ON CONFLICT` para seeds idempotentes.

