# Changelog

All notable changes to this project are documented here.

## [2.0.0] - 2025-11-01

### 🚀 Production Complete

#### HTTPS and SSL/TLS
-   **Let's Encrypt SSL**: Valid certificate until 2026-01-30 for admin.heartguard.live
-   **Automatic renewal**: Systemd timer configured (every 12 hours)
-   **PostgreSQL SSL**: Self-signed certificates with SANs, sslmode=require enforced
-   **Redis TLS**: Port 6380 with TLS authentication and password protection
-   **Backend SSL/TLS verification**: Certificate validation enabled for all connections
-   **End-to-end encryption**: HTTPS frontend + SSL database + TLS Redis

#### Infrastructure
-   **Reserved IP**: 134.199.133.125 (Digital Ocean atl1) configured and persistent
-   **Domain**: admin.heartguard.live pointing to reserved IP
-   **Nginx reverse proxy**: HTTPS with HTTP/2, security headers, and rate limiting
-   **UFW firewall**: Ports 22, 80, 443 properly configured
-   **iptables fix**: DOCKER-USER chain rules corrected for Let's Encrypt validation
-   **Systemd services**: iptables-docker.service and certbot-renew.service for persistence

#### Documentation Reorganization
-   **Centralized docs**: All documentation moved to `docs/` with proper structure
-   **docs/deployment/**: Production guides (PRODUCTION_STATUS.md, production_deployment.md)
-   **docs/security/**: Security docs (CREDENTIALS.md, SECURITY_SSL_TLS.md, ssl_tls_setup.md)
-   **docs/scripts/**: Utility scripts (generate_certs.sh, verify_production.sh, etc.)
-   **docs/README.md**: Complete documentation index
-   **Updated readme.md**: New structure, quick start guides, and production status

#### Scripts and Utilities
-   **verify_production.sh**: Complete system verification script
-   **generate_certs.sh**: Enhanced certificate generation with SANs
-   **reset_and_deploy_prod.sh**: Complete production reset and deploy
-   **redis-entrypoint.sh**: Custom Redis entrypoint with TLS support

#### Security Credentials
-   **All generated with openssl**: 32+ bytes entropy for all passwords
-   **PostgreSQL credentials**: Updated and synchronized with .env.production
-   **Redis password**: Strong password for TLS connections
-   **JWT secret**: Cryptographically secure secret
-   **CREDENTIALS.md**: Complete credentials documentation (not in git)

### 🐛 Critical Fixes
-   Fixed Backend TLS config: Added `ServerName: "postgres"` for TLS connection
-   Fixed Certificates: Regenerated with Subject Alternative Names (SANs) for Go 1.22+
-   Fixed heartguard_app password: Updated in PostgreSQL to match .env.production
-   Fixed iptables blocking: Removed DROP rules blocking Let's Encrypt validation
-   Fixed Nginx SSL errors: Temporary HTTP config during certificate acquisition
-   Fixed Docker Compose: Removed obsolete `version: "3.9"`, fixed POSTGRES_INITDB_ARGS
-   Fixed Redis TLS: Added `--tls-auth-clients optional` for healthchecks

### ✅ Verified Working
-   ✅ PostgreSQL SSL enabled (`SHOW ssl;` = on)
-   ✅ Redis TLS active (redis-cli --tls PING = PONG)
-   ✅ Backend SSL/TLS verification logs working
-   ✅ HTTPS working (curl -I https://admin.heartguard.live)
-   ✅ Login functional (admin@heartguard.com / Admin#2025)
-   ✅ Certificate valid until 2026-01-30
-   ✅ Firewall configured (UFW + iptables)
-   ✅ DNS resolution (admin.heartguard.live → 134.199.133.125)

---

## [Unreleased]

### Added

-   Gestión de equipos de cuidado, miembros y cuidadores desde el panel superadmin (API y vistas).

### Changed

-   Backend HTTP server ahora acepta únicamente conexiones desde localhost, bloqueando cualquier acceso remoto.
-   Documentación y `.env.example` actualizados para reflejar el backend de administración cerrado.
-   Superadmin panel migrado de SPA a renderizado del lado del servidor usando plantillas Go y `ui.ViewData`.
-   Activos estáticos reorganizados en `backend/ui/assets` junto con nuevas utilidades JS/CSS para componentes SSR.
-   Se eliminaron los archivos legacy bajo `backend/web` y se actualizaron las guías para reflejar la nueva arquitectura.

## [0.2.0] - 2025-09-28

### Added

-   **Redis integration** for refresh token storage and rate limiting.
-   **Real authentication**:
    -   JWT access + refresh flow with rotation.
    -   Refresh/logout endpoints backed by Redis.
    -   Removal of demo/test tokens (`X-Demo-Superadmin`).
-   **Audit logging**:
    -   Now includes client IP (proxied or local).
-   **Superadmin web panel**:
    -   Login/logout using real JWT.
    -   Automatic refresh handling.
    -   UI cleanup aligned with new backend flows.
-   **Makefile**:
    -   New `reset-all` target to fully clean DB, Redis, and Docker volumes.
-   **Database seed**:
    -   Deterministic demo superadmin user with fixed password for testing.

### Changed

-   Updated backend README with real auth flow, `curl` smoke tests, and Redis details.
-   Updated root README to reflect new commands, reset workflow, and removal of demo token auth.

### Notes

-   Default demo superadmin: `admin@heartguard.com` / `Admin#2025`.
-   Panel served from backend binary, now secured with JWT auth.

## [0.1.0] - 2025-09-27

### Added

-   **PostgreSQL setup**: Initialization/seed scripts, schema definitions, demo data, and role management.
-   **Docker Compose**: Configuration for Postgres + PostGIS with persistent volume.
-   **Makefile targets**: Database lifecycle (`db-init`, `db-seed`, `db-reset`, `db-health`, `db-psql`).
-   **Helper scripts**: For database reset and health checks.
-   **Go-based Superadmin API backend**:
    -   CRUD for organizations
    -   User and membership management
    -   Invitation flows
    -   Audit logs with structured writes
-   **Unified project structure**:
    -   Separated `db/` and `backend/` directories
    -   Shared `.env.example` with consistent variables
    -   Unified Makefile for DB and backend
-   **Detailed README.md files**:
    -   Root repo overview
    -   Database setup and troubleshooting
    -   Backend usage with example `curl` smoke tests

### Notes

-   Backend authentication is demo-only (`X-Demo-Superadmin: 1` or `Authorization: Bearer let-me-in`).
-   Initial seed includes a demo superadmin user (`admin@heartguard.com` with example hash).
-   First stable snapshot combining database and backend in a single repo.
