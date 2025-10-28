
# 🏢 HeartGuard – Org Service

Microservicio encargado de la **gestión de organizaciones, miembros e invitaciones** dentro del ecosistema **HeartGuard**.  
Desarrollado en **Flask puro**, con soporte **dual JSON/XML** y autenticación **JWT** compartida con `auth_service`.

---

## 📦 Estructura del proyecto

```

org_service/
├─ app.py               # Punto de entrada del servicio
├─ config.py            # Configuración global (lee el .env de la raíz)
├─ db.py                # Pool de conexiones PostgreSQL
├─ responses.py         # Respuestas JSON/XML unificadas
├─ repository.py        # Consultas SQL a organizations / invitations / membership
├─ routes/
│  ├─ orgs.py           # Endpoints para listar organizaciones y detalle
│  └─ invitations.py    # Endpoints para enviar/listar/aceptar invitaciones
├─ requirements.txt     # Dependencias Python
└─ README.md

````

---

## ⚙️ Configuración

Este servicio reutiliza el archivo **`.env` ubicado en la raíz del proyecto**, por lo tanto **no necesita un `.env` local propio**. Si necesitas valores distintos para pruebas, ajusta el `.env` global o exporta las variables antes de ejecutar el servicio.

Ejemplo de `.env` global:

```bash
FLASK_ENV=development
SERVICE_PORT=5002

PGHOST=localhost
PGPORT=5432
PGDATABASE=heartguard
PGUSER=heartguard_app
PGPASSWORD=dev_change_me
PGSCHEMA=heartguard

JWT_SECRET=supersecret123
ACCESS_TTL_MIN=30
REFRESH_TTL_DAYS=7
````

> Asegúrate de que `JWT_SECRET` sea **idéntico** al de `auth_service`, para que ambos validen los mismos tokens.

---

## 🧱 Inicialización

1️⃣ Crea o activa tu entorno virtual desde la raíz del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
```

2️⃣ Instala las dependencias:

```bash
pip install -r microservicios/org_service/requirements.txt
```

3️⃣ Ejecuta el servicio:

```bash
python microservicios/org_service/app.py
```

Por defecto se levanta en:

```
http://localhost:5002
```

---

## 🔐 Autenticación JWT

Todas las rutas requieren un token JWT válido emitido por el `auth_service`.
Debe enviarse en el header:

```
Authorization: Bearer <ACCESS_TOKEN>
```

Los tokens se validan con `flask-jwt-extended` y deben incluir campos como:

```json
{
  "user_id": "uuid",
  "email": "jorge@example.com",
  "org_id": "org-uuid",
  "global_role": "user"
}
```

---

## 🧠 Endpoints principales

### 🔹 Health Check

Verifica que el servicio esté activo.

```bash
GET /health
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "service": "org_service",
    "status": "healthy"
  }
}
```

---

### 🔹 Listar organizaciones del usuario

Devuelve las organizaciones a las que pertenece el usuario autenticado y su rol dentro de cada una.

```bash
GET /v1/orgs/me
Authorization: Bearer <ACCESS_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "organizations": [
      {
        "id": "uuid",
        "code": "FAM-001",
        "name": "Familia García",
        "role_code": "org_admin",
        "created_at": "2025-07-18T17:43:22+00:00"
      }
    ]
  }
}
```

> `GET /v1/orgs` es un alias de este endpoint.

---

### 🔹 Detalle de una organización

Solo si el usuario pertenece a la organización solicitada.

```bash
GET /v1/orgs/<ORG_ID>
Authorization: Bearer <ACCESS_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "organization": {
      "id": "uuid",
      "code": "FAM-001",
      "name": "Familia García",
      "created_at": "2025-07-18T17:43:22+00:00"
    },
    "membership": {
      "org_id": "uuid",
      "org_code": "FAM-001",
      "org_name": "Familia García",
      "role_code": "org_admin",
      "joined_at": "2025-07-19T12:11:03+00:00"
    }
  }
}
```

---

### 🔹 Enviar invitación

Envía una invitación para que un usuario se una a una organización.
Genera un token único (UUID) que podrá usarse luego para aceptar la invitación.

```bash
POST /v1/invitations
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "email": "nuevo.usuario@example.com",
  "org_id": "<ORG_ID>",
  "role_code": "org_user"
}
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "id": "uuid",
    "email": "nuevo.usuario@example.com",
    "org_id": "<ORG_ID>",
    "token": "f0a7b13e-2ab9-4f31-9a78-1c0dbb1e9e4a",
    "role_code": "org_user"
  }
}
```

---

### 🔹 Listar invitaciones de una organización

Devuelve todas las invitaciones enviadas para una organización específica.

```bash
GET /v1/invitations/org/<ORG_ID>
Authorization: Bearer <ACCESS_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "invitations": [
      {
        "id": "uuid",
        "email": "nuevo.usuario@example.com",
        "status": "pending",
        "created_at": "2025-10-27T18:05:00",
        "expires_at": "2025-10-30T18:05:00+00:00",
        "role_code": "org_user"
      }
    ]
  }
}
```

---

### 🔹 Aceptar invitación

El usuario autenticado (debe coincidir con el correo de la invitación) consume el token para unirse a la organización.

```bash
POST /v1/invitations/<TOKEN>/accept
Authorization: Bearer <ACCESS_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "organization": {
      "id": "uuid",
      "name": "Familia García",
      "role_code": "org_user"
    },
    "user_id": "uuid"
  }
}
```

---

## 🧩 Respuestas en XML

Si el cliente envía el header:

```
Accept: application/xml
```

El servicio devuelve la misma estructura en formato XML.

Ejemplo:

```xml
<response>
  <status>ok</status>
  <data>
    <id>uuid</id>
    <name>Hospital Alfa</name>
  </data>
</response>
```

---

## 🧰 Dependencias principales

| Paquete                | Uso                         |
| ---------------------- | --------------------------- |
| **Flask**              | Framework base              |
| **flask-jwt-extended** | Autenticación JWT           |
| **psycopg2-binary**    | Conexión PostgreSQL         |
| **python-dotenv**      | Carga de variables globales |
| **dicttoxml**          | Conversión JSON → XML       |

---

## 🧾 Notas técnicas

* Usa la base `heartguard` compartida por todos los microservicios.
* Cada conexión ejecuta `SET search_path TO <schema>, public` automáticamente.
* Los endpoints están protegidos con `@jwt_required()` y devuelven respuestas JSON/XML homogéneas incluso ante errores de autenticación.
* Las invitaciones expiran según `INVITATION_TTL_HOURS` (72h por defecto) y pueden asignar roles existentes (`org_user`, `org_admin`, `viewer`, ...).

---

## 🔗 Integración con otros servicios

| Servicio            | Interacción                                                        |
| ------------------- | ------------------------------------------------------------------ |
| **auth_service**    | Emite los JWT usados por `org_service`                             |
| **patient_service** | Asociará pacientes a una organización                              |
| **media_service**   | Permitirá a cada organización subir y leer imágenes en su contexto |

---

## 🧠 Próximos pasos recomendados

1. Implementar `POST /v1/invitations/:token/accept` (para que usuarios invitados puedan unirse).
2. Añadir control de roles (`@requires_role("org_admin")`).
3. Registrar eventos de creación en `audit_service`.

---

## 👤 Autor

Desarrollado por **Jorge Serangelli**
Proyecto académico–profesional **HeartGuard**
Universidad de Monterrey – Accenture Data & Analytics

```

---

¿Quieres que te genere además un **archivo `.http` listo para Thunder Client / VS Code** con todos los requests (`login`, `create org`, `list orgs`, `invite user`)? Así podrías probar el flujo completo con un clic desde tu laptop o directamente en tu VM GCP.
```
