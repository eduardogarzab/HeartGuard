# Changelog

All notable changes to this project are documented here.

## [Unreleased]

-   Work in progress for upcoming features.

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
    -   API key management
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
