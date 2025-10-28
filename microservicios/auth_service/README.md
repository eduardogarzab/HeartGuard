
# 🧑‍💻 HeartGuard – Auth Service

Microservicio de autenticación y control de acceso para **HeartGuard**, desarrollado con **Flask puro**, **PostgreSQL**, y soporte **dual JSON/XML**.  
Gestiona usuarios, login, refresh tokens, y roles, sirviendo tanto al **panel web (XML)** como a la **app móvil (JSON)**.

---

## 📦 Estructura del proyecto

```

auth_service/
├─ app.py               # Punto de entrada Flask
├─ config.py            # Configuración (DB, JWT, entorno)
├─ db.py                # Pool de conexión PostgreSQL
├─ security.py          # Hash de contraseñas, JWT
├─ responses.py         # Respuestas unificadas JSON/XML
├─ repository.py        # Acceso a base de datos
├─ routes/
│  ├─ auth.py           # Login, refresh, logout
│  └─ users.py          # Registro y perfil /me
├─ requirements.txt     # Dependencias
└─ README.md

````

---

## ⚙️ Requisitos previos

- Python **3.10+**
- PostgreSQL con esquema `heartguard` inicializado (`init.sql`)
- Instancia de **Redis** accesible para la lista de revocación
- Virtualenv o entorno equivalente

---

## 🧩 Instalación

```bash
cd microservicios/auth_service
python -m venv .venv
source .venv/bin/activate   # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
````

---

## ⚙️ Configuración

El microservicio reutiliza exclusivamente el archivo `.env` centralizado en `microservicios/.env`, de modo que comparte credenciales con el resto de componentes Python. Parte de la plantilla `microservicios/.env.example` y ajusta los valores ahí (o vía variables de entorno) cuando necesites cambios.

### Variables clave

| Variable                                       | Descripción                                      |
| ---------------------------------------------- | ------------------------------------------------ |
| `DATABASE_URL` / `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` | Cadena o parámetros de PostgreSQL                |
| `PGSCHEMA`                                     | Debe apuntar al esquema `heartguard`             |
| `AUTH_JWT_SECRET` / `JWT_SECRET`               | Llave para firmar JWT                            |
| `AUTH_ACCESS_TTL_MIN`                          | Duración del access token (minutos)              |
| `AUTH_REFRESH_TTL_DAYS`                        | Duración del refresh token (días)                |
| `AUTH_SERVICE_PORT`                            | Puerto donde correrá Flask                       |
| `DEFAULT_ORG_ID`                               | Organización por defecto para testing (opcional) |
| `AUTH_REDIS_URL`                               | URL de Redis para la lista de revocación JWT     |
| `AUTH_REDIS_PREFIX`                            | Prefijo de claves en Redis (opcional)            |

---

## 🧱 Inicialización de datos

Antes de usar el servicio, asegúrate de tener al menos un estado de usuario activo:

```sql
INSERT INTO heartguard.user_statuses (code, label)
VALUES ('active', 'Activo')
ON CONFLICT (code) DO NOTHING;

SELECT id FROM heartguard.user_statuses WHERE code='active';
```

Guarda ese `id` para usarlo en el registro de usuarios.

---

## 🚀 Ejecución

```bash
python app.py
```

Por defecto, se levanta en:

```
http://localhost:5001
```

---

## 🧠 Endpoints principales

### 🔹 `POST /v1/users`

Registrar nuevo usuario.

**Body JSON:**

```json
{
  "name": "Jorge",
  "email": "jorge@example.com",
  "password": "secret",
  "user_status_id": "uuid-del-status-active"
}
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "id": "uuid",
    "email": "jorge@example.com",
    "name": "Jorge"
  }
}
```

---

### 🔹 `POST /v1/auth/login`

Iniciar sesión.

**Headers:**

```
Content-Type: application/json
X-Org-ID: org-uuid
```

**Body:**

```json
{
  "email": "jorge@example.com",
  "password": "secret"
}
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "user": {
      "id": "uuid",
      "email": "jorge@example.com",
      "org_id": "org-uuid"
    }
  }
}
```

> Si el cliente envía `Accept: application/xml`, la respuesta se entrega en XML.

---

### 🔹 `GET /v1/users/me`

Devuelve la información del usuario autenticado.

**Headers:**

```
Authorization: Bearer <ACCESS_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "identity": {
      "user_id": "uuid",
      "email": "jorge@example.com",
      "org_id": "org-uuid",
      "global_role": "user"
    }
  }
}
```

---

### 🔹 `POST /v1/auth/refresh`

Renueva el access token usando el refresh token.

**Headers:**

```
Authorization: Bearer <REFRESH_TOKEN>
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "access_token": "nuevo-token"
  }
}
```

---

### 🔹 `POST /v1/auth/logout`

Revoca el refresh token actual.

**Headers:**

```
Authorization: Bearer <REFRESH_TOKEN>
```

**Body:**

```json
{
  "refresh_token": "eyJ..."
}
```

---

## 🔁 Flujo de uso

1. `POST /v1/users` → crear usuario
2. `POST /v1/auth/login` → obtener access/refresh token
3. `GET /v1/users/me` → consultar identidad
4. `POST /v1/auth/refresh` → renovar sesión
5. `POST /v1/auth/logout` → cerrar sesión

---

## 📡 Health Check

```bash
GET /health
```

**Respuesta:**

```json
{
  "status": "ok",
  "data": {
    "service": "auth_service",
    "status": "healthy"
  }
}
```

---

## 🧩 Integración con otros microservicios

Este servicio expone JWT con el siguiente *payload base*:

```json
{
  "user_id": "uuid",
  "email": "jorge@example.com",
  "org_id": "org-uuid",
  "global_role": "user",
  "typ": "access"
}
```

Otros microservicios (como `org_service`, `patient_service`) validan este token en cada solicitud y verifican que `org_id` coincida con su ámbito de datos.

---

## 🧾 Logs y auditoría

Cada inicio y cierre de sesión genera eventos que pueden enviarse al `audit_service` (pendiente de integrar).
Actualmente, los logs se imprimen en consola durante desarrollo.

---

## 🧰 Dependencias

| Paquete              | Uso                        |
| -------------------- | -------------------------- |
| `flask`              | Framework principal        |
| `flask-jwt-extended` | Manejo de tokens JWT       |
| `psycopg2-binary`    | Conexión PostgreSQL        |
| `passlib[bcrypt]`    | Hash seguro de contraseñas |
| `dicttoxml`          | Respuesta XML              |
| `python-dotenv`      | Variables de entorno       |
| `redis`              | Lista de revocación de tokens |

---

## 🧩 Próximos pasos sugeridos

* Añadir `@requires_role("org_admin")` para proteger endpoints según rol.
* Registrar eventos en `audit_service` para auditoría centralizada.
* Añadir pruebas automatizadas para el flujo completo login → refresh → logout.

---

## 🧠 Autor

Desarrollado por **Jorge Serangelli** como parte del proyecto **HeartGuard**,
Sistema distribuido para monitoreo cardiovascular predictivo.

```

---

¿Quieres que te lo formatee con emojis y estilo visual similar al de tus otros proyectos (por ejemplo, con secciones azul/blanco y encabezados decorativos tipo *TechDocs* para incluirlo directamente en tu repo de GitHub)? Puedo ajustarlo para que se vea más profesional en el `README.md` del repo.
```
