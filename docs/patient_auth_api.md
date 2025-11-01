# Patient Authentication API

API para autenticación y gestión de pacientes en HeartGuard.

## Base URL

```
https://admin.heartguard.live/api/patient-auth
```

## Endpoints

### 1. Register (Registro de Paciente)

Registra un nuevo paciente en el sistema.

**Endpoint:** `POST /register`

**Request Body:**
```json
{
  "org_id": "uuid-de-organizacion",
  "person_name": "Juan Pérez",
  "email": "juan.perez@example.com",
  "password": "SecurePassword123!",
  "birthdate": "1985-06-15",  // Opcional, formato YYYY-MM-DD
  "sex_id": "uuid-del-sexo"   // Opcional
}
```

**Validaciones:**
- `person_name`, `email`, `password` y `org_id` son requeridos
- Password debe tener al menos 8 caracteres
- Email debe ser único en el sistema
- Fecha de nacimiento debe estar en formato YYYY-MM-DD

**Response (201 Created):**
```json
{
  "success": true,
  "patient": {
    "id": "uuid-del-paciente",
    "org_id": "uuid-de-organizacion",
    "person_name": "Juan Pérez",
    "email": "juan.perez@example.com",
    "email_verified": false,
    "birthdate": "1985-06-15T00:00:00Z",
    "created_at": "2025-11-01T10:30:00Z"
  }
}
```

**Errores:**
- `400 Bad Request`: Datos inválidos o faltantes
- `409 Conflict`: Email ya registrado

---

### 2. Login (Inicio de Sesión)

Autentica un paciente y retorna un token de sesión.

**Endpoint:** `POST /login`

**Request Body:**
```json
{
  "email": "juan.perez@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "jwt-token-aqui",
  "patient": {
    "id": "uuid-del-paciente",
    "org_id": "uuid-de-organizacion",
    "person_name": "Juan Pérez",
    "email": "juan.perez@example.com",
    "email_verified": true,
    "birthdate": "1985-06-15T00:00:00Z",
    "created_at": "2025-11-01T10:30:00Z"
  }
}
```

**Errores:**
- `400 Bad Request`: Email o contraseña faltantes
- `401 Unauthorized`: Credenciales inválidas
- `403 Forbidden`: Email no verificado

**Notas:**
- El token debe incluirse en requests subsecuentes como header: `Authorization: Bearer <token>`
- El backend actualiza automáticamente el campo `last_login_at` del paciente

---

### 3. Verify Email (Verificar Email)

Marca el email del paciente como verificado.

**Endpoint:** `POST /verify-email`

**Request Body:**
```json
{
  "patient_id": "uuid-del-paciente",
  "token": "token-de-verificacion"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Email verificado exitosamente"
}
```

**Errores:**
- `400 Bad Request`: Datos faltantes
- `404 Not Found`: Paciente no encontrado

**TODO:** Implementar sistema de tokens de verificación por email.

---

### 4. Reset Password (Resetear Contraseña)

Solicita un reset de contraseña para un paciente.

**Endpoint:** `POST /reset-password`

**Request Body:**
```json
{
  "email": "juan.perez@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Si el email existe, recibirás instrucciones para resetear tu contraseña"
}
```

**Notas:**
- Por seguridad, siempre retorna success=true aunque el email no exista
- TODO: Implementar sistema de tokens de reset y envío de emails

---

## Datos de Prueba

La base de datos incluye 3 pacientes de prueba con las siguientes credenciales:

### Paciente 1
- **Email:** maria.delgado@example.com
- **Password:** Test123!
- **Nombre:** María Delgado
- **Email verificado:** ✅ Sí
- **Organización:** FAM-001

### Paciente 2
- **Email:** jose.hernandez@example.com
- **Password:** Test123!
- **Nombre:** José Hernández
- **Email verificado:** ✅ Sí
- **Organización:** CLIN-001

### Paciente 3
- **Email:** valeria.ortiz@example.com
- **Password:** Test123!
- **Nombre:** Valeria Ortiz
- **Email verificado:** ❌ No
- **Organización:** FAM-001

---

## Stored Procedures Utilizados

### `sp_patient_register`
Registra un nuevo paciente con email y password hasheado.

**Parámetros:**
- `p_org_id` (uuid): ID de la organización
- `p_person_name` (text): Nombre del paciente
- `p_email` (text): Email (se convierte a minúsculas)
- `p_password_hash` (text): Hash bcrypt de la contraseña
- `p_birthdate` (date, opcional): Fecha de nacimiento
- `p_sex_id` (uuid, opcional): ID del sexo

**Retorna:** Registro completo del paciente creado

**Validaciones:**
- Nombre requerido
- Email requerido y único
- Password hash requerido
- Organización requerida

---

### `sp_patient_find_by_email`
Busca un paciente por email para autenticación.

**Parámetros:**
- `p_email` (text): Email del paciente

**Retorna:**
- `id`, `person_name`, `email`, `password_hash`, `email_verified`, `org_id`, `last_login_at`

---

### `sp_patient_update_last_login`
Actualiza la fecha de último login del paciente.

**Parámetros:**
- `p_id` (uuid): ID del paciente

**Retorna:** `boolean` (true si se actualizó)

---

### `sp_patient_verify_email`
Marca el email del paciente como verificado.

**Parámetros:**
- `p_id` (uuid): ID del paciente

**Retorna:** `boolean` (true si se actualizó)

---

### `sp_patient_set_password`
Actualiza el password hash de un paciente.

**Parámetros:**
- `p_id` (uuid): ID del paciente
- `p_password_hash` (text): Nuevo hash bcrypt

**Retorna:** `boolean` (true si se actualizó)

---

## Esquema de Base de Datos

### Tabla: `patients`

Campos adicionales para autenticación:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `email` | VARCHAR(150) UNIQUE | Email del paciente (para login) |
| `password_hash` | TEXT | Hash bcrypt de la contraseña |
| `email_verified` | BOOLEAN DEFAULT FALSE | Indica si el email está verificado |
| `last_login_at` | TIMESTAMP | Fecha de último login |

**Índices:**
- `idx_patients_email` en `email` (WHERE email IS NOT NULL)

---

## Seguridad

### Password Hashing
- Algoritmo: **bcrypt** con cost factor 10
- Los passwords nunca se almacenan en texto plano
- El hash se genera en el backend antes de enviar a la base de datos

### Validaciones
- Email debe ser único
- Password mínimo 8 caracteres (validación en handler)
- Emails se convierten a minúsculas automáticamente
- Login requiere email verificado (configurable)

### Session Tokens
- Los tokens son JWT gestionados por el módulo `session.Manager`
- Se almacenan en Redis con TTL configurable
- Incluyen el `patient_id` en el payload

---

## Próximos Pasos (TODOs)

1. **Sistema de Verificación de Email:**
   - Generar tokens únicos de verificación
   - Enviar emails con enlace de verificación
   - Endpoint para confirmar verificación

2. **Sistema de Reset de Contraseña:**
   - Generar tokens únicos de reset
   - Enviar emails con enlace de reset
   - Endpoint para establecer nueva contraseña

3. **OAuth/Social Login:**
   - Integración con Google
   - Integración con Facebook
   - Integración con Apple Sign In

4. **Two-Factor Authentication (2FA):**
   - TOTP (Google Authenticator, Authy)
   - SMS verification
   - Backup codes

5. **Rate Limiting:**
   - Limitar intentos de login por IP
   - Limitar registros por IP/día

---

## Testing con cURL

### Registrar un nuevo paciente
```bash
curl -X POST https://admin.heartguard.live/api/patient-auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "org_id": "UUID_DE_ORG",
    "person_name": "Test User",
    "email": "test@example.com",
    "password": "Password123!"
  }'
```

### Login
```bash
curl -X POST https://admin.heartguard.live/api/patient-auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "maria.delgado@example.com",
    "password": "Test123!"
  }'
```

### Verificar email
```bash
curl -X POST https://admin.heartguard.live/api/patient-auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "UUID_DEL_PACIENTE",
    "token": "TOKEN_DE_VERIFICACION"
  }'
```

---

## Changelog

### 2025-11-01
- ✅ Implementación inicial de Patient Auth API
- ✅ Stored procedures para autenticación
- ✅ Handlers para login/register/verify/reset
- ✅ Integración con session manager
- ✅ Datos de prueba en seed.sql
- ✅ Documentación completa
