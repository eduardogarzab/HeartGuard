# HeartGuard Microservices Validation Plan

This document describes the comprehensive validation strategy implemented for the HeartGuard microservices suite and explains how to execute the automated test harness delivered in `validate_microservices.bat`.

## Objectives
- Guarantee that every Python microservice runs in an isolated virtual environment.
- Verify outbound connectivity from the local workstation to the shared PostgreSQL and Redis services hosted at `35.184.124.76`.
- Launch all microservices in a deterministic order and capture their runtime logs.
- Exercise critical business flows end-to-end via HTTP using `curl`, including success and error scenarios.
- Demonstrate resilience by simulating a controlled outage and observing the gateway's behaviour.
- Produce auditable evidence (report and logs) suitable for academic evaluation.

## Pre-requisites
1. Windows 10/11 shell (PowerShell or Command Prompt).
2. Python launcher (`py`) or `python` available on `PATH`.
3. Internet access to reach the remote VM at `35.184.124.76` (ports 5432 and 6379).
4. Seed data present in PostgreSQL for the super-admin account:
   - Email: `ana.ruiz@heartguard.com`
   - Password: `Demo#2025`
5. Repository cloned locally with write permissions to create virtual environments and logs.
6. Optional: update `microservicios/.env` if credentials change.

## Automation Workflow
The batch script performs the following high-level stages:

1. **Environment preparation**
   - Resolves repository paths and sets up a dedicated `validation_logs` folder under `microservicios`.
   - Detects an available Python interpreter (`py`, `python`, or `python3`).
   - Creates (or reuses) per-service virtual environments and installs dependencies from `requirements.txt`.

2. **Connectivity verification**
   - Uses `Test-NetConnection` to probe PostgreSQL (`35.184.124.76:5432`) and Redis (`35.184.124.76:6379`).
   - Executes lightweight Python probes (`SELECT 1` and `Redis.ping()`) inside the `auth_service` virtual environment to ensure credentials and networking are correct.

3. **Service orchestration**
   - Starts `auth_service`, `org_service`, `audit_service`, and `gateway` in that order via PowerShell `Start-Process`, capturing stdout/stderr into individual log files.
   - Confirms that each process remains alive after a short warm-up period.

4. **Functional verification (HTTP/cURL)**
   - Health checks for every microservice and the gateway.
   - Direct authentication flow against `auth_service` (login, refresh, and `users/me`).
   - Gateway-mediated login and organization queries (`/v1/orgs/me`, `/v1/orgs/{id}`).
   - Audit log creation routed through the gateway to `audit_service`.
   - Negative cases (missing credentials, forbidden organization access).

5. **Degradation drill**
   - Forcefully stops `org_service` and immediately exercises the gateway to confirm it surfaces a `503` error while downstream dependency is unavailable.
   - Executes an additional gateway request without a token to verify authentication guards while the system is degraded.

6. **Reporting and teardown**
   - Terminates any remaining service processes.
   - Writes a summary to `validation_report.txt` indicating pass/fail counts and timestamps.
   - Retains all request/response payloads and cURL stderr output for later inspection.

## Test Matrix Overview
| Category            | Endpoint / Action                                  | Expected Outcome |
|--------------------|----------------------------------------------------|------------------|
| Connectivity       | PostgreSQL `SELECT 1` / Redis `PING`               | Success (network OK) |
| Health             | `/health` on each service                          | HTTP 200 |
| Auth success       | `POST /v1/auth/login` (direct and via gateway)     | HTTP 200 + tokens |
| Auth refresh       | `POST /v1/auth/refresh`                            | HTTP 200 |
| Auth identity      | `GET /v1/users/me`                                 | HTTP 200 |
| Org listing        | `GET /v1/orgs/me` via gateway                      | HTTP 200 + memberships |
| Org detail         | `GET /v1/orgs/{id}` via gateway                    | HTTP 200 |
| Audit log create   | `POST /v1/audit` via gateway                       | HTTP 201 |
| Invalid login      | Missing password                                   | HTTP 401 |
| Forbidden access   | Non-member org detail                              | HTTP 403 |
| Missing token      | Gateway request without `Authorization` header     | HTTP 401 |
| Degradation        | Gateway request while `org_service` is offline     | HTTP 503 |

## Artefacts Generated
- `microservicios/validation_logs/validation_report.txt` – master report with timestamps and verdicts.
- `microservicios/validation_logs/test_*.json` – individual HTTP responses captured during testing.
- `microservicios/validation_logs/payload_*.json` – request payloads used in POST operations.
- `microservicios/validation_logs/*_stdout.log` / `*_stderr.log` – service runtime logs.
- `microservicios/validation_logs/curl_errors.log` – stderr stream for all curl executions.

## How to Execute
```batch
cd C:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard
validate_microservices.bat
```

Upon completion the script exits with code `0` when every check passes, or `1` if any validation fails. Consult the report and log files to analyse failures.

## Suggested Follow-up
- Feed the generated logs into your observability stack or include them in the project portfolio.
- Extend the script with additional CRUD journeys (e.g., invitation acceptance) once corresponding APIs are stabilized.
- Integrate the batch script into CI (e.g., GitHub Actions self-hosted runner) to automate regression checks on each merge.
