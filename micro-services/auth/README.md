# Auth Service - HeartGuard

Microservicio de autenticación y autorización para el sistema HeartGuard. Maneja el registro, login y emisión de tokens JWT para dos tipos de cuentas: **Usuarios** (staff/familiares/doctores) y **Pacientes**.

## 🎯 Arquitectura

- **Puerto:** 5001
- **Base de datos:** PostgreSQL (compartida con superadmin-api)
- **JWT:** PyJWT con HS256
- **Hash:** bcrypt para passwords
- **Framework:** Flask

## 🔑 Dos Tipos de Cuentas

### 👤 Usuarios (Staff/Familiares/Doctores)
- Tabla: `users`
- Pueden pertenecer a **múltiples organizaciones**
- Tienen roles de sistema (`superadmin` o `user`)
- Tienen roles por organización (`org_admin` u `org_viewer`)
- Se agregan a organizaciones mediante invitaciones
- Gestionan pacientes y tienen acceso al panel de administración

### 🏥 Pacientes
- Tabla: `patients`
- Pertenecen a **UNA sola organización** (`org_id`)
- No tienen roles de sistema ni memberships múltiples
- Acceden a su portal de paciente
- Son gestionados por el staff

---

## 📡 Endpoints

### 1. Registro de Usuario
```http
POST /auth/register/user
Content-Type: application/json

{
  "name": "Dr. Juan Pérez",
  "email": "juan@example.com",
  "password": "SecurePass123!"
}
```

**Respuesta exitosa (201):**
```json
{
  "user_id": "uuid-here",
  "email": "juan@example.com",
  "message": "Registro exitoso"
}
```

**Validaciones:**
- Email único (no debe existir en `users`)
- Password mínimo 8 caracteres
- Crea usuario con `role_code='user'` y `user_status='active'`
- Sin organizaciones inicialmente (se agregan por invitación)

---

### 2. Registro de Paciente
```http
POST /auth/register/patient
Content-Type: application/json

{
  "name": "María González",
  "email": "maria@example.com",
  "password": "SecurePass123!",
  "org_id": "uuid-org-id",
  "birthdate": "1990-01-15",
  "sex_code": "F",
  "risk_level_code": "medium"
}
```

**Respuesta exitosa (201):**
```json
{
  "patient_id": "uuid-here",
  "email": "maria@example.com",
  "org_name": "Hospital Central",
  "message": "Registro exitoso"
}
```

**Validaciones:**
- Email único (no debe existir en `patients`)
- `org_id` es **REQUERIDO** y debe existir
- Campos opcionales: `birthdate`, `sex_code`, `risk_level_code`

---

### 3. Login de Usuario
```http
POST /auth/login/user
Content-Type: application/json

{
  "email": "juan@example.com",
  "password": "SecurePass123!"
}
```

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid-here",
    "email": "juan@example.com",
    "name": "Dr. Juan Pérez",
    "system_role": "user",
    "org_count": 2
  }
}
```

**Payload del JWT (access_token):**
```json
{
  "user_id": "uuid",
  "account_type": "user",
  "email": "juan@example.com",
  "name": "Dr. Juan Pérez",
  "system_role": "user",
  "org_memberships": [
    {
      "org_id": "uuid-1",
      "org_code": "HOSP-001",
      "org_name": "Hospital Central",
      "role_code": "org_admin"
    },
    {
      "org_id": "uuid-2",
      "org_code": "CLIN-002",
      "org_name": "Clínica Norte",
      "role_code": "org_viewer"
    }
  ],
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Validaciones:**
- Usuario existe en tabla `users`
- Password correcto (bcrypt)
- `user_status='active'`
- Consulta todas las membresías (`user_org_membership`)

---

### 4. Login de Paciente
```http
POST /auth/login/patient
Content-Type: application/json

{
  "email": "maria@example.com",
  "password": "SecurePass123!"
}
```

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "patient": {
    "id": "uuid-here",
    "email": "maria@example.com",
    "name": "María González",
    "org_name": "Hospital Central",
    "risk_level": "medium"
  }
}
```

**Payload del JWT (access_token):**
```json
{
  "patient_id": "uuid",
  "account_type": "patient",
  "email": "maria@example.com",
  "name": "María González",
  "org_id": "uuid-org",
  "org_code": "HOSP-001",
  "org_name": "Hospital Central",
  "risk_level": "medium",
  "exp": 1234567890,
  "iat": 1234567890
}
```

**Validaciones:**
- Paciente existe en tabla `patients`
- Password correcto (bcrypt)
- Consulta organización del paciente

---

### 5. Aceptar Invitación (Solo Usuarios)
```http
POST /auth/accept-invitation/:token
Authorization: Bearer <user-access-token>
```

**Respuesta exitosa (200):**
```json
{
  "message": "Te uniste a Hospital Central como Administrador de Organización",
  "org_id": "uuid-org",
  "org_name": "Hospital Central",
  "role_code": "org_admin"
}
```

**Validaciones:**
- Token de invitación existe en `org_invitations`
- Token no ha expirado (`expires_at > NOW()`)
- Token no ha sido usado (`used_at IS NULL`)
- Email del token coincide con el usuario autenticado
- Crea registro en `user_org_membership`
- Marca invitación como usada (`used_at = NOW()`)

---

### 6. Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Funcionalidad:**
- Valida el refresh_token
- Detecta `account_type` del token
- Re-consulta datos actualizados:
  - **Usuario:** Consulta membresías actuales
  - **Paciente:** Consulta datos actuales
- Genera nuevo `access_token` con datos frescos

---

### 7. Verificar Token
```http
GET /auth/verify
Authorization: Bearer <access-token>
```

**Respuesta exitosa (200):**
```json
{
  "valid": true,
  "payload": {
    "user_id": "uuid",
    "account_type": "user",
    "system_role": "user",
    "org_memberships": [...]
  }
}
```

**Respuesta error (401):**
```json
{
  "error": "Token inválido o expirado"
}
```

---

### 8. Obtener Información del Usuario Autenticado
```http
GET /auth/me
Authorization: Bearer <access-token>
```

**Respuesta para usuario (200):**
```json
{
  "account_type": "user",
  "data": {
    "id": "uuid",
    "email": "juan@example.com",
    "name": "Dr. Juan Pérez",
    "system_role": "user",
    "memberships": [
      {
        "org_id": "uuid-1",
        "org_code": "HOSP-001",
        "org_name": "Hospital Central",
        "role_code": "org_admin",
        "role_label": "Administrador de Organización"
      }
    ]
  }
}
```

**Respuesta para paciente (200):**
```json
{
  "account_type": "patient",
  "data": {
    "id": "uuid",
    "email": "maria@example.com",
    "name": "María González",
    "org_id": "uuid-org",
    "org_name": "Hospital Central",
    "birthdate": "1990-01-15",
    "risk_level": "medium"
  }
}
```

---

### 9. Logout (Opcional)
```http
POST /auth/logout
Authorization: Bearer <access-token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Respuesta exitosa (200):**
```json
{
  "message": "Sesión cerrada exitosamente"
}
```

**Funcionalidad:**
- Invalida el refresh_token (si se usa blacklist en Redis)

---

## 🔒 Reglas de Negocio

### Usuarios (Staff)
- ✅ Registro abierto sin organización inicial
- ✅ `role_code='user'` por defecto
- ✅ Se agregan a organizaciones mediante invitaciones
- ✅ Pueden pertenecer a **múltiples organizaciones**
- ✅ `system_role='superadmin'` da acceso al panel `/superadmin/*`
- ✅ `org_memberships` con `role_code='org_admin'` dan acceso al admin de esa organización

### Pacientes
- ✅ Registro requiere `org_id` (deben indicar a qué organización pertenecen)
- ✅ Solo pertenecen a **UNA organización**
- ✅ No tienen roles de sistema ni memberships múltiples
- ✅ Su JWT solo incluye su `org_id`
- ✅ Acceden a vistas de paciente (`/patient-portal/*`)

### Tokens JWT
- ✅ **access_token:** 15 minutos de validez
- ✅ **refresh_token:** 7 días de validez
- ✅ Incluyen `"account_type": "user" | "patient"` para diferenciar
- ✅ Firmados con `JWT_SECRET` compartido con otros servicios

---

## 📊 Tablas de Base de Datos

### Consultadas por el servicio:
- **`users`** - Usuarios (staff/familiares/doctores)
  - `id`, `name`, `email`, `password_hash`, `user_status_id`, `role_code`
  
- **`patients`** - Pacientes
  - `id`, `org_id`, `name`, `email`, `password_hash`, `birthdate`, `sex_id`, `risk_level_code`
  
- **`user_org_membership`** - Membresías de usuarios a organizaciones
  - `org_id`, `user_id`, `role_code`, `joined_at`
  
- **`org_invitations`** - Invitaciones a organizaciones (solo para usuarios)
  - `id`, `org_id`, `email`, `role_code`, `token`, `expires_at`, `used_at`
  
- **`organizations`** - Organizaciones
  - `id`, `code`, `name`
  
- **`roles`** - Roles del sistema
  - `code`, `label`, `description`
  
- **`user_statuses`** - Estados de usuario
  - `id`, `code`, `label`

---

## 🌐 Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgres://heartguard_app:password@localhost:5432/heartguard

# JWT
JWT_SECRET=tu-secreto-compartido-con-todos-los-servicios
JWT_ACCESS_TOKEN_EXPIRES=15  # minutos
JWT_REFRESH_TOKEN_EXPIRES=10080  # 7 días en minutos

# Flask
FLASK_ENV=development
PORT=5001
```

---

## 🚀 Uso del Gateway

El API Gateway usará los tokens para autorizar acceso:

### Usuario con `system_role='superadmin'`
```
✅ Acceso a /superadmin/* (panel de superadministración)
✅ Acceso a todas las rutas
```

### Usuario con `account_type='user'` y `role_code='org_admin'` en org
```
✅ Acceso a /admin/* (panel de administración de su organización)
✅ Acceso a recursos de sus organizaciones
```

### Paciente con `account_type='patient'`
```
✅ Acceso a /patient-portal/* (portal del paciente)
✅ Acceso solo a sus propios datos
```

---

## 📝 Notas Técnicas

### Diferencias en JWT por Tipo de Cuenta

**Usuario (Staff):**
```json
{
  "user_id": "uuid",
  "account_type": "user",
  "system_role": "user",
  "org_memberships": [...]  // Array de organizaciones
}
```

**Paciente:**
```json
{
  "patient_id": "uuid",
  "account_type": "patient",
  "org_id": "uuid-single-org",  // Solo una organización
  "org_code": "HOSP-001"
}
```

### Validación de Passwords
- Mínimo 8 caracteres
- Hasheado con bcrypt (costo: 10)
- Verificación con `bcrypt.check_password_hash()`

### Manejo de Errores
- `400` - Bad Request (validación fallida)
- `401` - Unauthorized (credenciales inválidas o token expirado)
- `404` - Not Found (usuario/paciente no existe)
- `409` - Conflict (email ya registrado)
- `500` - Internal Server Error

---

## 🧪 Testing

```bash
# Registro de usuario
curl -X POST http://localhost:5001/auth/register/user \
  -H "Content-Type: application/json" \
  -d '{"name":"Dr. Juan","email":"juan@test.com","password":"Pass123!"}'

# Login de usuario
curl -X POST http://localhost:5001/auth/login/user \
  -H "Content-Type: application/json" \
  -d '{"email":"juan@test.com","password":"Pass123!"}'

# Verificar token
curl -X GET http://localhost:5001/auth/verify \
  -H "Authorization: Bearer <your-token>"
```

---

## 📦 Dependencias

```txt
Flask>=2.3.0
Flask-CORS>=4.0.0
PyJWT>=2.8.0
bcrypt>=4.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

---

## 🔐 Seguridad

- ✅ Passwords hasheados con bcrypt (nunca en texto plano)
- ✅ JWT firmados con HS256
- ✅ Tokens con expiración
- ✅ Refresh tokens para renovación segura
- ✅ Validación de `user_status='active'` antes de login
- ✅ Invitaciones con tokens únicos y fecha de expiración
- ✅ CORS configurado para dominios permitidos

---

## 📄 Licencia

Propiedad de HeartGuard - Todos los derechos reservados
