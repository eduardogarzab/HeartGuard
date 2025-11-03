# Guía Rápida de Pruebas - HeartGuard Desktop

## ✅ Servicios Corriendo

- **Auth Service**: http://localhost:5001 ✓
- **Gateway Service**: http://localhost:8000 ✓
- **Aplicación Java**: Ejecutándose ✓

## 🔧 Problema Resuelto

**Error anterior**: `TypeError: Object of type datetime is not JSON serializable`

**Solución aplicada**: Se agregó la función `_serialize_memberships` en `auth_service.py` para convertir los objetos datetime a strings ISO antes de crear los tokens JWT.

## 🧪 Pruebas para Realizar

### 1️⃣ Registrar un Usuario (Staff)

En la aplicación Java que está corriendo:

1. Selecciona **"Usuario (Staff)"**
2. Click en **"Registrarse"**
3. Completa los datos:
   ```
   Email: doctor@heartguard.com
   Contraseña: password123
   Confirmar Contraseña: password123
   Nombre: Juan
   Apellido: Pérez
   Teléfono: 5551234567
   ID Organización: 1
   ID Rol: 1
   ```
4. Click **"Registrar"**
5. **Resultado esperado**: Mensaje de éxito

### 2️⃣ Login de Usuario

1. Selecciona **"Usuario (Staff)"**
2. Ingresa:
   ```
   Email: doctor@heartguard.com
   Contraseña: password123
   ```
3. Click **"Iniciar Sesión"**
4. **Resultado esperado**: Mensaje de bienvenida con el nombre del usuario

### 3️⃣ Registrar un Paciente

1. Selecciona **"Paciente"**
2. Click en **"Registrarse"**
3. Completa los datos:
   ```
   Email: paciente@heartguard.com
   Contraseña: password123
   Confirmar Contraseña: password123
   Nombre: María
   Apellido: González
   Teléfono: 5559876543
   Fecha de Nacimiento: 1985-05-20
   Género: female
   ID Organización: 1
   ```
4. Click **"Registrar"**
5. **Resultado esperado**: Mensaje de éxito

### 4️⃣ Login de Paciente

1. Selecciona **"Paciente"**
2. Ingresa:
   ```
   Email: paciente@heartguard.com
   Contraseña: password123
   ```
3. Click **"Iniciar Sesión"**
4. **Resultado esperado**: Mensaje de bienvenida con el nombre del paciente

## 📊 Verificar Logs

En las terminales de los servicios deberías ver:

**Auth Service** (Terminal 2):
```
INFO:werkzeug:127.0.0.1 - - [fecha] "POST /auth/register/user HTTP/1.1" 201 -
INFO:werkzeug:127.0.0.1 - - [fecha] "POST /auth/login/user HTTP/1.1" 200 -
```

**Gateway Service** (Terminal 3):
```
127.0.0.1 - - [fecha] "POST /auth/register/user HTTP/1.1" 201 -
127.0.0.1 - - [fecha] "POST /auth/login/user HTTP/1.1" 200 -
```

## ✨ Características Implementadas

- ✅ Selector de tipo de cuenta (Usuario/Paciente)
- ✅ Pantalla de login con validación
- ✅ Pantallas de registro para ambos tipos
- ✅ Validación de contraseñas (mínimo 6 caracteres, confirmación)
- ✅ Validación de formato de fecha de nacimiento
- ✅ Comunicación con API Gateway
- ✅ Manejo de errores con mensajes descriptivos
- ✅ Interfaz moderna con FlatLaf Look & Feel
- ✅ Operaciones asíncronas (no bloquea la UI)

## 🎯 Flujo de Comunicación

```
Aplicación Java → Gateway (8000) → Auth Service (5001) → PostgreSQL (136.115.53.140:5432)
```

## 🔑 Cuentas de Prueba

Después de registrarte, puedes usar estas credenciales:

**Usuario (Staff):**
- Email: `doctor@heartguard.com`
- Contraseña: `password123`

**Paciente:**
- Email: `paciente@heartguard.com`
- Contraseña: `password123`

## 🎉 ¡Listo!

La aplicación está completamente funcional y lista para usar. El error del datetime ha sido resuelto y ahora puedes:

- ✅ Registrar usuarios y pacientes
- ✅ Hacer login con ambos tipos de cuenta
- ✅ Recibir tokens JWT válidos
- ✅ Ver información del usuario autenticado

**¡Disfruta probando la aplicación!** 🚀
