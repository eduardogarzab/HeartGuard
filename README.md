# HeartGuard - Sistema de Monitoreo de Salud para Colonias

## 🏥 Descripción del Sistema

HeartGuard es un sistema de monitoreo de salud para colonias privadas con tres niveles de roles jerárquicos:

- **Admin de admin** → encargado de la colonia
- **Admin** → cabeza de familia  
- **Usuarios** → miembros de la familia

### 🏗️ Arquitectura del Backend

```
                    ┌─────────────────┐
                    │  Backend Go     │
                    │ (Administradores)│
                    │   Puerto 8080   │
                    └─────────────────┘
                           │
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
            ┌─────────────┐ ┌─────────────┐
            │ PostgreSQL  │ │    Redis    │
            │ Puerto 5432 │ │ Puerto 6379 │
            │             │ │             │
            │ - Colonias  │ │ - Sesiones  │
            │ - Familias  │ │ - Alertas   │
            │ - Usuarios  │ │ - Cache     │
            │ - Contactos │ │             │
            │ - Alertas   │ │             │
            └─────────────┘ └─────────────┘
                    │
                    │ (futuro)
                    ▼
            ┌─────────────┐
            │   InfluxDB  │
            │ Puerto 8086 │
            │             │
            │ - Métricas  │
            │   Fisiológicas│
            │ - GPS       │
            │ - Actividad │
            └─────────────┘
```

## 🚀 Inicio Rápido

### Prerrequisitos

- **Docker Desktop** (instalar desde [docker.com](https://www.docker.com/products/docker-desktop/))
- **Git** (opcional, para clonar repositorio)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard
```

### 2. Levantar los Servicios

```bash
cd backend
docker-compose up -d
```

Esto iniciará:
- **PostgreSQL** (puerto 5432) - Base de datos principal
- **InfluxDB** (puerto 8086) - Base de datos de series de tiempo
- **Redis** (puerto 6379) - Cache y sesiones
- **Backend Go** (puerto 8080) - API REST

### 3. Probar el Sistema

#### En Mac/Linux:
```bash
# Ejecutar pruebas completas
./test.sh
```

#### En Windows:
```cmd
# Script nativo de Windows
test.bat

# O con Git Bash (si lo tienes instalado)
./test.sh

# O simplemente abrir en navegador
# http://localhost:8080/
```

### 4. Verificar que Funciona

**Verificar en navegador:**
- Abrir: http://localhost:8080/

**Verificar con curl:**
```bash
curl http://localhost:8080/
```

**Ver estado de servicios:**
```bash
cd backend
docker-compose ps
```

## 🔄 Comandos de Gestión

### Reiniciar el Sistema
```bash
# Detener servicios
cd backend
docker-compose down

# Iniciar servicios nuevamente
docker-compose up -d

# O todo en uno
docker-compose down && docker-compose up -d
```

### Ver Logs
```bash
cd backend
# Todos los servicios
docker-compose logs

# Solo el backend
docker-compose logs backend-go

# Seguir logs en tiempo real
docker-compose logs -f
```

### Detener el Sistema
```bash
cd backend
docker-compose down
```

### Limpiar Todo (Eliminar datos)
```bash
cd backend
docker-compose down -v
```

## 📡 API Endpoints

### Backend Go (Administradores) - Puerto 8080

#### Autenticación
- `POST /api/v1/login` - Iniciar sesión
- `POST /api/v1/logout` - Cerrar sesión

#### Colonias
- `GET /api/v1/colonias` - Listar colonias
- `POST /api/v1/colonias` - Crear colonia
- `GET /api/v1/colonias/:id` - Obtener colonia
- `PUT /api/v1/colonias/:id` - Actualizar colonia
- `DELETE /api/v1/colonias/:id` - Eliminar colonia

#### Familias
- `GET /api/v1/familias` - Listar familias
- `POST /api/v1/familias` - Crear familia
- `GET /api/v1/familias/:id` - Obtener familia
- `PUT /api/v1/familias/:id` - Actualizar familia
- `DELETE /api/v1/familias/:id` - Eliminar familia

#### Usuarios
- `GET /api/v1/usuarios` - Listar usuarios
- `POST /api/v1/usuarios` - Crear usuario
- `GET /api/v1/usuarios/:id` - Obtener usuario
- `PUT /api/v1/usuarios/:id` - Actualizar usuario
- `DELETE /api/v1/usuarios/:id` - Eliminar usuario

#### Contactos de Emergencia
- `GET /api/v1/usuarios/:id/contactos` - Listar contactos
- `POST /api/v1/usuarios/:id/contactos` - Crear contacto
- `PUT /api/v1/contactos/:id` - Actualizar contacto
- `DELETE /api/v1/contactos/:id` - Eliminar contacto

#### Alertas
- `GET /api/v1/alertas` - Listar todas las alertas
- `GET /api/v1/usuarios/:id/alertas` - Alertas de usuario
- `PUT /api/v1/alertas/:id/resolver` - Resolver alerta

## 🧪 Pruebas con cURL

### 1. Verificar Estado del Sistema

```bash
curl http://localhost:8080/
```

### 2. Iniciar Sesión

```bash
curl -X POST http://localhost:8080/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "maria_admin",
    "password": "admin123"
  }'
```

### 3. Listar Colonias (con token)

```bash
curl -X GET http://localhost:8080/api/v1/colonias \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

### 4. Crear Usuario (con token)

```bash
curl -X POST http://localhost:8080/api/v1/usuarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "familia_id": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "email": "juan@example.com",
    "rol": "usuario",
    "username": "juan_user",
    "password": "password123"
  }'
```

## 🗄️ Estructura de Base de Datos

### PostgreSQL (Datos Estructurados)

#### Tabla: colonias
- `colonia_id` (SERIAL PRIMARY KEY)
- `nombre` (VARCHAR)
- `direccion` (TEXT)
- `encargado_id` (INT)
- `fecha_creacion` (TIMESTAMP)
- `activa` (BOOLEAN)

#### Tabla: familias
- `familia_id` (SERIAL PRIMARY KEY)
- `colonia_id` (INT, FK)
- `nombre` (VARCHAR)
- `admin_id` (INT)
- `fecha_creacion` (TIMESTAMP)
- `activa` (BOOLEAN)

#### Tabla: usuarios
- `usuario_id` (SERIAL PRIMARY KEY)
- `familia_id` (INT, FK)
- `nombre` (VARCHAR)
- `apellido` (VARCHAR)
- `email` (VARCHAR, UNIQUE)
- `telefono` (VARCHAR)
- `fecha_nacimiento` (DATE)
- `rol` (VARCHAR) - 'admin_colonia', 'admin_familia', 'usuario'
- `username` (VARCHAR, UNIQUE)
- `password_hash` (VARCHAR)
- `activo` (BOOLEAN)
- `fecha_registro` (TIMESTAMP)

#### Tabla: contactos_emergencia
- `contacto_id` (SERIAL PRIMARY KEY)
- `usuario_id` (INT, FK)
- `nombre` (VARCHAR)
- `relacion` (VARCHAR)
- `telefono` (VARCHAR)
- `email` (VARCHAR)
- `es_principal` (BOOLEAN)

#### Tabla: alertas
- `alerta_id` (SERIAL PRIMARY KEY)
- `usuario_id` (INT, FK)
- `tipo` (VARCHAR)
- `nivel` (VARCHAR)
- `mensaje` (TEXT)
- `datos_adicionales` (JSONB)
- `resuelta` (BOOLEAN)
- `fecha_creacion` (TIMESTAMP)

### Redis (Cache y Sesiones)

#### Claves de Sesión
- `session:{usuario_id}` → Token JWT

#### Alertas en Tiempo Real
- `alertas:{usuario_id}` → Lista de alertas pendientes

### InfluxDB (Preparado para Métricas)

El sistema incluye InfluxDB configurado y listo para almacenar métricas fisiológicas cuando se implemente el microservicio de métricas.

## 🔒 Seguridad

### Autenticación
- JWT tokens con expiración de 24 horas
- Contraseñas encriptadas con bcrypt
- Middleware de autenticación en endpoints protegidos

### Autorización
- Sistema de roles jerárquico
- Admin de colonia: acceso completo
- Admin de familia: acceso a su familia
- Usuario: acceso limitado a sus datos

### Validación
- Validación de entrada en todos los endpoints
- Sanitización de datos
- Manejo de errores consistente

## 🛠️ Desarrollo

### Estructura del Proyecto

```
HeartGuard/
├── backend/                    # Backend Go para administradores
│   ├── docker-compose.yml     # Orquestación de servicios
│   ├── Dockerfile             # Imagen Docker para Go
│   ├── main.go               # Aplicación principal
│   ├── init.sql              # Inicialización de PostgreSQL
│   └── go.mod                # Dependencias Go
├── dataset.xlsx              # Dataset de ejemplo (opcional)
├── test.sh                   # Script de pruebas (Mac/Linux)
├── test.bat                  # Script de pruebas (Windows)
└── README.md                 # Este archivo
```

### Comandos de Desarrollo

```bash
# Levantar solo las bases de datos
docker-compose up -d postgres influxdb redis

# Reconstruir solo el backend
docker-compose up -d --build backend-go

# Ver logs del backend
docker-compose logs -f backend-go

# Entrar al contenedor de PostgreSQL
docker-compose exec postgres psql -U heartguard -d heartguard
```

### Variables de Entorno

#### Backend Go
```bash
DB_HOST=postgres
DB_PORT=5432
DB_USER=heartguard
DB_PASSWORD=heartguard123
DB_NAME=heartguard
REDIS_HOST=redis
REDIS_PORT=6379
JWT_SECRET=heartguard-jwt-secret-key-123
```

## 🌐 Servicios Disponibles

- **Backend Go**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **InfluxDB**: http://localhost:8086
- **Redis**: localhost:6379

## 🆘 Solución de Problemas

### Error: "Backend no está corriendo"
```bash
# Verificar que Docker esté corriendo
docker --version

# Verificar estado de servicios
cd backend
docker-compose ps

# Ver logs
docker-compose logs
```

### Error: "Puerto ya en uso"
```bash
# Verificar qué está usando el puerto
lsof -i :8080  # Mac/Linux
netstat -ano | findstr :8080  # Windows

# Cambiar puerto en docker-compose.yml si es necesario
```

### Error: "No se puede conectar a la base de datos"
```bash
# Esperar a que PostgreSQL se inicialice
docker-compose logs postgres

# Verificar que esté "healthy"
docker-compose ps
```

### Error: "Contenedor no inicia"
```bash
# Ver logs detallados
docker-compose logs backend-go

# Reconstruir imagen
docker-compose up -d --build backend-go
```

## 🚀 Próximos Pasos

### 🔄 Funcionalidades Pendientes de Implementar

#### 1. **Sistema de Auto-Registro con Creación de Colonias**
**Problema actual:** No hay forma de que nuevos usuarios se registren sin un admin de colonia existente.

**Solución propuesta:**
- **Flujo de registro inteligente**: El primer usuario que busque una colonia inexistente la crea automáticamente
- **Auto-asignación de roles**: El creador de la colonia se convierte en `admin_colonia`
- **Escalabilidad orgánica**: Las colonias se crean según la demanda real

**Implementación necesaria:**
```go
// Nuevo endpoint de registro público
POST /api/v1/register
{
  "nombre": "Juan Pérez",
  "email": "juan@email.com",
  "telefono": "+52-55-1234-5678",
  "colonia_nombre": "Colonia Las Palmas",
  "colonia_direccion": "Av. Principal 123, Ciudad de México",
  "password": "password123"
}
```

**Lógica del sistema:**
1. Usuario busca colonia por nombre
2. Si existe → Se registra como familia normal
3. Si NO existe → Crea la colonia y se convierte en `admin_colonia`
4. Puede crear familias y usuarios dentro de su colonia

**Beneficios:**
- ✅ **Escalable**: No requiere super admin manual
- ✅ **Automático**: Los usuarios crean sus propias colonias
- ✅ **Orgánico**: Crecimiento basado en demanda real
- ✅ **Simple**: Un solo flujo de registro

#### 2. **Microservicio de Métricas Fisiológicas**
- Implementar microservicio Flask/Python para manejo de datos fisiológicos
- Integración con InfluxDB para métricas en tiempo real
- Endpoints para ingesta de datos de dispositivos IoT

#### 3. **App Android**
- Desarrollar aplicación móvil que consuma los microservicios
- Interfaz para usuarios finales (no administradores)
- Notificaciones push para alertas

#### 4. **Mejoras del Sistema Actual**
- Agregar más validaciones y reglas de negocio
- Implementar notificaciones en tiempo real
- Sistema de reportes y analytics

## 📝 Notas Importantes

- El sistema está **completamente funcional** como backend base
- Todas las bases de datos están configuradas y listas
- El sistema de autenticación y autorización está implementado
- Los datos de ejemplo se cargan automáticamente al iniciar
- El proyecto está **contenedorizado** para fácil despliegue

## 🤝 Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature
3. Hacer commit de tus cambios
4. Push a la rama
5. Crear un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

---

**¡El sistema está listo para usar!** 🎉

Para empezar, ejecuta:
```bash
cd backend
docker-compose up -d
cd ..
./test.sh  # Mac/Linux
# o
test.bat   # Windows
```