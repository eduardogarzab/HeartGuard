# 🏥 HeartGuard - Portal del Paciente - Guía de Implementación Completa

## 📋 Resumen

Se ha implementado un **servicio completo de portal del paciente** que incluye:

1. ✅ **Patient Service** (Microservicio en Python/Flask)
2. ✅ **Gateway actualizado** con rutas del patient service
3. ✅ **Desktop App** con dashboard interactivo para pacientes

---

## 🏗️ Arquitectura

```
┌─────────────────┐
│  Desktop App    │ (Java Swing)
│  Puerto: N/A    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Gateway   │ (Flask)
│  Puerto: 8000   │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┐
    │         │              │
    ▼         ▼              ▼
┌─────┐  ┌─────────┐  ┌──────────┐
│Auth │  │ Patient │  │  Otros   │
│5001 │  │  5002   │  │servicios │
└──┬──┘  └────┬────┘  └──────────┘
   │          │
   └────┬─────┘
        │
        ▼
┌──────────────────┐
│   PostgreSQL     │
│ 136.115.53.140   │
│    Puerto 5432   │
└──────────────────┘
```

---

## 🚀 Cómo Iniciar los Servicios

### 1. Base de Datos (Ya está corriendo)
```
Host: 136.115.53.140
Puerto: 5432
Base de datos: heartguard
Usuario: heartguard_app
Password: heartguard2025
```

### 2. Auth Service (Puerto 5001)

**Ubicación:** `services/auth/`

**PowerShell:**
```powershell
cd services/auth
.\restart.ps1
```

**Bash/Linux:**
```bash
cd services/auth
source venv/bin/activate
python -m flask --app src.auth.app run --port 5001 --reload
```

### 3. Patient Service (Puerto 5004) ⭐ NUEVO

**Ubicación:** `services/patient/`

**PowerShell:**
```powershell
cd services/patient
.\start.ps1
```

**Bash/Linux:**
```bash
cd services/patient
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m flask --app src.patient.app run --port 5004 --reload
```

**Verificar que funciona:**
```powershell
curl http://localhost:5002/health
```

Debe responder:
```json
{
  "status": "healthy",
  "service": "patient-service"
}
```

### 4. Gateway (Puerto 8000)

**Ubicación:** `services/gateway/`

**Crear archivo `.env` en `services/gateway/`:**
```bash
FLASK_DEBUG=1
FLASK_SECRET_KEY=your-secret-key
GATEWAY_SERVICE_TIMEOUT=10
AUTH_SERVICE_URL=http://localhost:5001
PATIENT_SERVICE_URL=http://localhost:5004
```

**Iniciar gateway:**
```bash
cd services/gateway
source venv/bin/activate  # o .\venv\Scripts\Activate.ps1 en Windows
python -m flask --app src.gateway.app run --port 8000 --reload
```

**Verificar que funciona:**
```powershell
curl http://localhost:8000/health
```

### 5. Desktop App (Java)

**Ubicación:** `desktop-app/`

**Compilar:**
```bash
cd desktop-app
mvn clean package
```

**Ejecutar:**
```bash
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar
```

---

## 📡 Endpoints del Patient Service

### Base URL (a través del Gateway)
```
http://localhost:8000/patient
```

### 1. Dashboard Completo
```http
GET /patient/dashboard
Authorization: Bearer <patient-token>
```

**Respuesta:**
```json
{
  "patient": {
    "id": "uuid",
    "name": "María González",
    "email": "maria@example.com",
    "birthdate": "1990-01-15",
    "sex": "Femenino",
    "risk_level": "Medio",
    "org_name": "Hospital Central"
  },
  "stats": {
    "total_alerts": 5,
    "pending_alerts": 2,
    "devices_count": 2,
    "last_reading": "2025-11-03T10:30:00"
  },
  "recent_alerts": [...],
  "care_team": [...]
}
```

### 2. Perfil del Paciente
```http
GET /patient/profile
Authorization: Bearer <patient-token>
```

### 3. Alertas con Paginación
```http
GET /patient/alerts?status=pending&limit=20&offset=0
Authorization: Bearer <patient-token>
```

**Query params:**
- `status` (opcional): `new`, `ack`, `resolved`
- `limit` (opcional): default 20, max 100
- `offset` (opcional): default 0

### 4. Dispositivos
```http
GET /patient/devices
Authorization: Bearer <patient-token>
```

### 5. Historial de Lecturas
```http
GET /patient/readings?limit=50&offset=0
Authorization: Bearer <patient-token>
```

### 6. Equipo de Cuidado
```http
GET /patient/care-team
Authorization: Bearer <patient-token>
```

### 7. Última Ubicación
```http
GET /patient/location/latest
Authorization: Bearer <patient-token>
```

---

## 🖥️ Desktop App - Dashboard del Paciente

### Características Implementadas

#### 1. **Información Personal**
- Nombre completo
- Email
- Fecha de nacimiento
- Nivel de riesgo (con colores):
  - 🟢 Bajo (verde)
  - 🟡 Medio (amarillo)
  - 🟠 Alto (naranja)
  - 🔴 Crítico (rojo)
- Organización asignada

#### 2. **Estadísticas de Salud**
- Total de alertas (badge azul)
- Alertas pendientes (badge rojo)
- Número de dispositivos (badge verde)
- Última lectura (badge morado)

#### 3. **Alertas Recientes (Top 5)**
- Tipo de alerta
- Nivel de severidad con colores
- Descripción
- Fecha y hora
- Estado actual

#### 4. **Equipo de Cuidado**
- Nombre del equipo
- Miembros con:
  - Nombre
  - Rol
  - Email de contacto

#### 5. **Acciones Rápidas**
- Botón "Ver Todas las Alertas" (próximamente)
- Botón "Ver Dispositivos" (próximamente)
- Botón "Actualizar" (recarga datos)
- Botón "Cerrar Sesión"

### Nuevos Archivos Creados

1. **`PatientDashboardPanel.java`**
   - Ubicación: `desktop-app/src/main/java/com/heartguard/desktop/ui/`
   - Función: Panel principal del dashboard del paciente
   - Características:
     - Interfaz gráfica con Swing
     - Scroll vertical para contenido largo
     - Colores y badges según nivel de riesgo/alerta
     - Formateo de fechas ISO a dd/MM/yyyy HH:mm

2. **Actualizado: `LoginFrame.java`**
   - Método agregado: `openPatientDashboard()`
   - Ahora cuando un paciente inicia sesión, se abre automáticamente el dashboard

3. **Actualizado: `ApiClient.java`**
   - Método agregado: `getPatientDashboard(String token)`
   - Conecta con el gateway en `/patient/dashboard`

---

## 🔒 Seguridad

### JWT Validation
- Cada request al Patient Service requiere JWT válido
- El middleware `@require_patient_token` valida:
  - ✅ Token no expirado
  - ✅ `account_type === 'patient'`
  - ✅ Presencia de `patient_id` en payload

### Acceso a Datos
- Un paciente **SOLO** puede ver sus propios datos
- El `patient_id` se extrae del JWT, no del request body
- No hay forma de que un paciente acceda a datos de otro

---

## 🧪 Pruebas

### 1. Registro de Paciente

**Desktop App:**
1. Abrir aplicación
2. Clic en "Registrarse como Paciente"
3. Llenar formulario:
   - *Nombre: "Juan Pérez"
   - *Email: "juan.perez@test.com"
   - *Contraseña: "test123"
   - *Organización: "FAM-001" (o UUID de org)
   - Fecha de nacimiento: "1990-05-20"
   - Sexo: "M"
   - Nivel de riesgo: "low"
4. Clic en "Registrar Paciente"
5. Mensaje de éxito

### 2. Login de Paciente

**Desktop App:**
1. Seleccionar "Paciente"
2. Email: "juan.perez@test.com"
3. Contraseña: "test123"
4. Clic en "Iniciar Sesión"
5. **Dashboard se abre automáticamente** ⭐

### 3. Ver Dashboard

Una vez logueado, deberías ver:
- Tu nombre en el encabezado
- Información personal completa
- Estadísticas actualizadas
- Alertas recientes (si tienes)
- Equipo de cuidado (si está asignado)

### 4. Probar con Datos de Seed

**Usuario de prueba en `db/seed.sql`:**
```
Email: test.patient@heartguard.com
Password: password123
Organización: FAM-001
```

Este paciente debería tener:
- ✅ Alertas
- ✅ Dispositivos
- ✅ Equipo de cuidado
- ✅ Lecturas de señales

---

## 📂 Estructura de Archivos Nuevos

```
services/patient/
├── .env                          # Configuración del servicio
├── .env.example                  # Ejemplo de configuración
├── requirements.txt              # Dependencias Python
├── Makefile                      # Comandos útiles
├── start.ps1                     # Script de inicio Windows
├── README.md                     # Documentación del servicio
└── src/
    └── patient/
        ├── __init__.py
        ├── app.py                # Aplicación Flask principal
        ├── config.py             # Configuración
        ├── extensions.py         # Database cursor helper
        ├── blueprints/
        │   ├── __init__.py
        │   └── patient.py        # Endpoints del paciente
        ├── middleware/
        │   ├── __init__.py
        │   └── auth_middleware.py # JWT validation
        ├── services/
        │   ├── __init__.py
        │   └── patient_service.py # Lógica de negocio
        ├── repositories/
        │   ├── __init__.py
        │   └── patient_repo.py   # Acceso a datos
        └── utils/
            ├── __init__.py
            └── jwt_utils.py      # Utilidades JWT

desktop-app/src/main/java/com/heartguard/desktop/
└── ui/
    ├── LoginFrame.java           # ACTUALIZADO
    └── PatientDashboardPanel.java # NUEVO ⭐

services/gateway/src/gateway/
├── config.py                     # ACTUALIZADO (agregó PATIENT_SERVICE_URL)
└── routes/
    ├── __init__.py               # ACTUALIZADO (agregó patient_proxy)
    └── patient_proxy.py          # NUEVO ⭐
```

---

## 🔧 Troubleshooting

### Error: "Token inválido" o "401 Unauthorized"

**Causa:** El JWT expiró o es inválido

**Solución:**
1. Cerrar sesión
2. Volver a iniciar sesión
3. El nuevo token debería funcionar

### Error: "El servicio de pacientes no está disponible"

**Causa:** Patient Service no está corriendo en puerto 5004

**Solución:**
```powershell
cd services/patient
.\start.ps1
```

Verificar:
```powershell
curl http://localhost:5004/health
```

### Error: "Error de conexión con el gateway"

**Causa:** Gateway no está corriendo en puerto 8000

**Solución:**
```bash
cd services/gateway
python -m flask --app src.gateway.app run --port 8000
```

### Dashboard no muestra datos

**Causa:** No hay datos de prueba en la base de datos

**Solución:**
```sql
-- Ejecutar en PostgreSQL
\i db/seed.sql
```

### Error de compilación en Desktop App

**Causa:** Falta actualizar dependencias de Maven

**Solución:**
```bash
cd desktop-app
mvn clean install
mvn package
```

---

## 🎯 Próximos Pasos Sugeridos

### 1. Funcionalidades Adicionales
- [ ] Vista completa de todas las alertas (con paginación)
- [ ] Vista de dispositivos con más detalles
- [ ] Gráficas de señales (ECG, pulso)
- [ ] Notificaciones push para nuevas alertas
- [ ] Perfil editable del paciente
- [ ] Mensajería con el equipo de cuidado

### 2. Dashboard de Staff/Usuario
- [ ] Crear `StaffDashboardPanel.java`
- [ ] Ver lista de todos los pacientes
- [ ] Administrar dispositivos
- [ ] Revisar alertas de todos los pacientes
- [ ] Gestión de equipos de cuidado

### 3. Mejoras de UI
- [ ] Temas (dark mode / light mode)
- [ ] Iconos personalizados
- [ ] Animaciones de carga
- [ ] Gráficas con JFreeChart
- [ ] Exportar reportes a PDF

### 4. Seguridad
- [ ] Refresh token automático
- [ ] Logout desde todos los dispositivos
- [ ] Auditoría de accesos
- [ ] 2FA (autenticación de dos factores)

---

## 📝 Checklist de Verificación

Antes de usar el sistema, verifica:

- [ ] PostgreSQL en 136.115.53.140 está accesible
- [ ] Datos de seed están cargados (`db/seed.sql`)
- [ ] Auth Service corriendo en `localhost:5001`
- [ ] Patient Service corriendo en `localhost:5004`
- [ ] Gateway corriendo en `localhost:8000`
- [ ] Desktop App compilada correctamente
- [ ] Archivo `.env` en `services/patient/` configurado
- [ ] Archivo `.env` en `services/gateway/` configurado (con PATIENT_SERVICE_URL)

**Test de salud:**
```bash
# Auth Service
curl http://localhost:5001/health

# Patient Service
curl http://localhost:5004/health

# Gateway
curl http://localhost:8000/health
```

---

## 🎉 Resultado Final

Ahora tienes:

✅ **Microservicio Patient Service completamente funcional**
✅ **Gateway integrado con rutas del paciente**
✅ **Desktop App con dashboard interactivo**
✅ **Autenticación JWT segura**
✅ **Acceso a datos personales, alertas, dispositivos y equipo de cuidado**
✅ **UI profesional con colores y badges**
✅ **Arquitectura escalable y mantenible**

---

## 📧 Contacto y Soporte

Para dudas o problemas:
- Revisar logs del servicio: `services/patient/`
- Verificar consola del Gateway
- Revisar output de Maven en Desktop App
- Consultar el README de cada componente

---

**¡Todo listo para que los pacientes puedan ver su información de salud completa!** 🏥💙
