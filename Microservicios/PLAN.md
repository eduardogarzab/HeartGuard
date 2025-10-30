# Heartguard Microservicios Backend

## Arquitectura lógica
```
                       +----------------+
                       |  Frontends     |
                       | (Web & Móvil)  |
                       +----------------+
                               |
                               v
                       +----------------+
                       |   Gateway      |
                       |  (Flask 5000)  |
                       +----------------+
        _________ _________ _________ _________ _________ _________
       /         |         |         |         |         |         \
      v          v         v         v         v         v          v
+---------+ +---------+ +---------+ +---------+ +---------+ +---------+
|  Auth   | | Org     | | User    | | Media   | |Timeseries| | Audit   |
| 5001    | | 5002    | | 5003    | | 5004    | | 5005     | | 5006    |
+---------+ +---------+ +---------+ +---------+ +---------+ +---------+
      |          |         |          |            |            |
      |          |         |          |            |            |
      |          |         |          |            v            |
      |          |         |          |     +-------------+     |
      |          |         |          |     |  InfluxDB   |     |
      |          |         |          |     |  (8086)     |     |
      |          |         |          |     +-------------+     |
      |          |         |          |                          |
      v          v         v          v                          v
+---------+                                        +-------------------+
| Redis   |                                        |   Persistencia    |
| 6379    |                                        | (Archivos Audit)  |
+---------+                                        +-------------------+
```

## Puertos de servicio

| Servicio     | Puerto |
|--------------|--------|
| Gateway      | 5000   |
| Auth         | 5001   |
| Organization | 5002   |
| User         | 5003   |
| Media        | 5004   |
| Timeseries   | 5005   |
| Audit        | 5006   |
| Redis        | 6379   |
| InfluxDB     | 8086   |

## Flujo de autenticación
1. El cliente envía `POST /auth/login` al gateway con credenciales.
2. Gateway enruta al microservicio `auth` que valida usuario/contraseña usando bcrypt.
3. Auth emite un **access token** JWT (HS256) con TTL corto (`JWT_EXPIRES_IN`) y un **refresh token** (UUID) guardado en Redis con TTL (`REFRESH_TOKEN_TTL`).
4. Gateway responde al cliente respetando negociación JSON/XML.
5. El cliente usa el access token en `Authorization: Bearer ...` para acceder al resto de microservicios.
6. Cuando el access token expira, cliente llama `POST /auth/refresh` con refresh token; auth valida presencia en Redis y entrega nuevo access token.
7. Para cerrar sesión, cliente ejecuta `POST /auth/logout`, auth elimina el refresh token de Redis y el token deja de ser válido.

## Flujo de subida de media a GCS
1. Cliente autenticado invoca `POST /media/upload` vía gateway con archivo (multipart u octet-stream).
2. Gateway aplica CORS, JWT, RBAC y reenruta al servicio `media`.
3. `media` valida MIME y tamaño (`MAX_MEDIA_BYTES`), sube directo al bucket `heartguard-system` usando la cuenta de servicio configurada (`google-cloud-storage`).
4. Se genera `media_id`, metadata y URL firmada temporal.
5. Gateway devuelve metadata + `signed_url` en formato negociado.

## Flujo de ingestión/consulta de métricas (timeseries)
1. Dispositivos o servicios autorizados llaman `POST /timeseries/write` con mediciones.
2. `timeseries` valida payload contra los esquemas JSON/XSD y escribe en InfluxDB usando el cliente oficial.
3. Consultas `GET /timeseries/query` aplican RBAC (usuarios solo ven sus datos) y ejecutan consultas agregadas en InfluxDB.
4. Resultados paginados son devueltos respetando JSON/XML.

## Negociación de contenido JSON/XML
- Cada servicio analiza el header `Accept` y prioriza `application/xml` sobre JSON. Si no se especifica, responde JSON.
- Para peticiones de escritura (`POST/PUT/PATCH`) se valida `Content-Type` (JSON o XML) y se parsea al diccionario interno usando `utils_format.parse_body`.
- Las respuestas se producen con `utils_format.make_response`, lo que garantiza consistencia en formato.

## Manejo de errores y logging
- `error_handler.py` captura excepciones y devuelve estructura estándar:
  ```json
  {
    "error": {
      "code": 401,
      "message": "Unauthorized",
      "request_id": "...",
      "timestamp": "2025-10-29T18:00:00Z",
      "details": {}
    }
  }
  ```
- `middleware.py` genera `request_id`, calcula latencia, aplica límites de tamaño y escribe logs estructurados en stdout con datos de método, ruta, usuario y rol.
- `REQUEST_STATS` centraliza métricas para `/metrics`.

## Observabilidad
- `/health` comprueba que el proceso está vivo.
- `/ready` verifica dependencias (Redis, InfluxDB, credenciales GCS).
- `/metrics` entrega `requests_total`, `avg_latency_ms`, `uptime_seconds` y el nombre del servicio en JSON/XML.

## Levantar el stack localmente en Windows
1. `cd Microservicios`
2. Copiar `.env.example` a `.env` y ajustar secretos:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Ejecutar servicios:
   ```powershell
   .\start_services.bat
   ```
4. Validar endpoints:
   ```powershell
   .\validate_endpoints.bat localhost
   ```
5. Consumir el gateway en `http://localhost:5000`.

## Despliegue en VM Linux pública (ej. 34.70.7.33)
1. Copiar repositorio a la VM (`scp` o Git clone).
2. Configurar `.env` con secretos reales.
3. Ejecutar:
   ```bash
   ./start_services.sh
   ```
4. Validar salud remota:
   ```bash
   ./validate_endpoints.sh 34.70.7.33
   ```
5. Exponer puertos 5000-5006, 6379 y 8086 según políticas de firewall.

