# Gateway Service

Punto de entrada para los clientes web y mobile de HeartGuard. Expone rutas bajo `/v1/*` y reenvia la peticion al microservicio correspondiente, respetando el modelo multi tenant mediante el encabezado `x-org-id`.

---

## Requisitos

- Python 3.10 o superior
- Microservicios de auth y org corriendo (pueden estar en tu maquina local)
- Conectividad con la VM `4.246.170.83` donde viven PostgreSQL, Redis y el backend legacy
- Archivo `.env` en la raiz del monorepo con la configuracion compartida

---

## Variables de entorno

El gateway lee unicamente el `.env` ubicado en la raiz (`HeartGuard/.env`). Ejemplo minimo:

```
# Modo de ejecucion
FLASK_ENV=development
GATEWAY_SERVICE_PORT=5000

# Servicios destino
AUTH_SERVICE_URL=http://127.0.0.1:5001
ORG_SERVICE_URL=http://127.0.0.1:5002
GATEWAY_SERVICE_MAP=auth=http://127.0.0.1:5001,orgs=http://127.0.0.1:5002,patients=http://127.0.0.1:5002

# JWT compartido con auth_service
AUTH_JWT_SECRET=super_secreto

# Accesos a PostgreSQL y Redis alojados en la VM remota
PGHOST=4.246.170.83
PGPORT=5432
PGUSER=heartguard_app
PGPASSWORD=coloca_tu_password
PGDATABASE=heartguard
AUTH_REDIS_URL=redis://4.246.170.83:6379/0
```

`GATEWAY_SERVICE_MAP` es opcional, pero permite ajustar el routing sin tocar codigo. Si lo omites se usa la configuracion por defecto (auth y orgs).

---

## Instalacion rapida (PowerShell)

```powershell
cd microservicios\auth_service
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

cd ..\org_service
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

cd ..\gateway
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

Si ya tienes un virtualenv compartido puedes reutilizarlo; solo instala los `requirements.txt` de cada servicio.

---

## Ejecucion local

1. Asegura que el `.env` raiz esta cargado (`Invoke-Expression (Get-Content .env | ? {$_ -notmatch '^#'} | % {"set " + $_})` si necesitas exportarlo manualmente).
2. Arranca los microservicios de soporte (auth y org) usando PowerShell:
   ```powershell
   python microservicios/auth_service/app.py
   python microservicios/org_service/app.py
   python microservicios/gateway/app.py
   ```
   Tambien puedes usar `./start_microservices.sh` desde WSL o Git Bash para levantarlos en segundo plano.
3. El gateway queda disponible en `http://127.0.0.1:5000`.

Durante el arranque veras en consola algo como:

```
[Gateway] Rutas activas: auth -> http://127.0.0.1:5001, orgs -> http://127.0.0.1:5002, patients -> http://127.0.0.1:5002
```

---

## Pruebas rapidas

### Health check
```powershell
Invoke-RestMethod -Method Get http://127.0.0.1:5000/health
```

### Login JSON
```powershell
curl.exe -X POST "http://127.0.0.1:5000/v1/auth/login" ^
  -H "Content-Type: application/json" ^
  -H "X-Org-ID: <uuid_org>" ^
  -d "{\"email\":\"usuario@example.com\",\"password\":\"tu_password\"}"
```

### Endpoint protegido `/v1/orgs/me`
```powershell
$token = "<ACCESS_TOKEN_DEVUELTO_POR_LOGIN>"
curl.exe -X GET "http://127.0.0.1:5000/v1/orgs/me" ^
  -H "Authorization: Bearer $token"
```

El gateway propagara los headers al microservicio y anadira automaticamente `x-org-id` si el token incluye `org_id`.

---

## Mapeo de rutas

| Prefijo | Servicio destino | Como ajustar |
| ------- | ---------------- | ------------ |
| `/v1/auth/*` | `AUTH_SERVICE_URL` | Edita `AUTH_SERVICE_URL` o `GATEWAY_SERVICE_MAP` |
| `/v1/orgs/*` | `ORG_SERVICE_URL` | Usa `ORG_SERVICE_URL` o `GATEWAY_SERVICE_MAP` |
| `/v1/patients/*` | `ORG_SERVICE_URL` (temporal) | Cambia cuando exista `patient_service` |

Para nuevos microservicios anade la entrada en `GATEWAY_SERVICE_MAP`, por ejemplo:

```
GATEWAY_SERVICE_MAP=auth=http://127.0.0.1:5001,orgs=http://127.0.0.1:5002,media=http://127.0.0.1:5004
```

---

## Seguridad y auditoria

- Requiere JWT emitido por `auth_service` para todo excepto login, registro y refresh.
- Inserta `x-org-id` a partir del claim `org_id` para garantizar el aislamiento tenant.
- Propaga `X-Forwarded-For` y `X-Forwarded-Proto` hacia los microservicios.
- Si el servicio destino no responde, devuelve `503` o `504` con mensaje legible.

---

## Proximos pasos sugeridos

- Anadir circuit breakers y reintentos para microservicios criticos.
- Registrar cada request en `audit_service` cuando este disponible.
- Configurar metricas (Prometheus) y logs estructurados hacia `analytics_service`.
- Empaquetar en contenedor Docker para despliegue homogeno.
