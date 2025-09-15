# 🏥 HeartGuard - Vista Web del Superadministrador

Una interfaz web moderna y elegante para el panel de superadministración de HeartGuard.

## ✨ Características

### 🎨 Diseño Moderno
- **Interfaz responsiva** que se adapta a cualquier dispositivo
- **Tema profesional** con colores corporativos
- **Animaciones suaves** y transiciones elegantes
- **Iconografía Font Awesome** para mejor experiencia visual

### 🚀 Funcionalidades Principales

#### 📊 Dashboard Ejecutivo
- **Estadísticas en tiempo real** del sistema
- **Tarjetas informativas** con métricas clave
- **Actividad reciente** y alertas destacadas
- **Actualización automática** cada 30 segundos

#### 👥 Gestión de Usuarios
- **CRUD completo** de usuarios del sistema
- **Filtros avanzados** por rol, familia, estado
- **Creación de usuarios** con modal intuitivo
- **Edición y eliminación** con confirmaciones

#### 🏠 Gestión de Familias
- **Administración de familias** del sistema
- **Visualización de miembros** por familia
- **Estados activo/inactivo** para familias
- **Estadísticas de miembros** en tiempo real

#### 🚨 Sistema de Alertas
- **Monitoreo de alertas** médicas en tiempo real
- **Clasificación por nivel** (crítico, alto, medio, bajo)
- **Gestión de atención** de alertas
- **Badges de notificación** en tiempo real

#### 📍 Ubicaciones
- **Historial de ubicaciones** de usuarios
- **Filtros por usuario** y fechas
- **Visualización geográfica** (preparado para mapas)

#### 📈 Métricas Fisiológicas
- **Integración con InfluxDB** vía microservicio Flask
- **Visualización de datos** en tiempo real
- **Filtros por usuario** y tipo de métrica

#### 📋 Catálogos del Sistema
- **Gestión de catálogos** globales
- **Tipos de alertas**, parámetros médicos, etc.
- **CRUD completo** con validaciones

#### 📝 Logs del Sistema
- **Auditoría completa** de acciones
- **Filtros por usuario** y tipo de acción
- **Timestamps detallados** para trazabilidad

#### 🖥️ Monitoreo de Microservicios
- **Estado en tiempo real** de servicios
- **Control de activación/desactivación**
- **Información de versiones** y última verificación

## 🛠️ Tecnologías Utilizadas

### Frontend
- **HTML5** semántico y accesible
- **CSS3** con variables personalizadas y Grid/Flexbox
- **JavaScript ES6+** con clases y async/await
- **Font Awesome 6.4.0** para iconografía
- **Google Fonts (Inter)** para tipografía

### Backend
- **Go 1.21** con framework Gin
- **PostgreSQL** con stored procedures optimizados
- **Redis** para gestión de sesiones
- **InfluxDB** para métricas en tiempo real
- **JWT** para autenticación segura

## 🚀 Instalación y Uso

### 1. Ejecutar el Sistema Completo
```bash
# Clonar el repositorio (si no lo has hecho)
cd /Users/jesa/Projects/HeartGuard/backend

# Ejecutar el script de prueba completo
./test_web.sh
```

### 2. Acceso Manual
```bash
# Levantar servicios
docker-compose up -d

# Acceder a la aplicación
open http://localhost:8080
```

### 3. Credenciales de Acceso
```
Email: admin@heartguard.com
Password: admin123
```

## 🎯 Navegación del Dashboard

### 📱 Menú Lateral
- **Dashboard** - Vista general del sistema
- **Usuarios** - Gestión de usuarios
- **Familias** - Administración de familias
- **Alertas** - Monitoreo de alertas (con badge)
- **Ubicaciones** - Historial de ubicaciones
- **Métricas** - Datos fisiológicos
- **Catálogos** - Configuración del sistema
- **Logs** - Auditoría del sistema
- **Microservicios** - Estado de servicios

### 🔧 Funcionalidades Interactivas

#### Modal de Creación de Usuario
- Formulario completo con validaciones
- Selector de familia dinámico
- Roles predefinidos (admin_familia, miembro)
- Feedback visual en tiempo real

#### Gestión de Alertas
- Filtros por estado y nivel
- Acciones rápidas (atender, eliminar)
- Actualización automática del badge
- Confirmaciones de seguridad

#### Dashboard Responsivo
- **Desktop**: Vista completa con sidebar
- **Tablet**: Sidebar colapsable
- **Mobile**: Navegación optimizada

## 🎨 Personalización

### Colores del Sistema
```css
:root {
    --primary-color: #2563eb;      /* Azul principal */
    --secondary-color: #64748b;    /* Gris secundario */
    --success-color: #10b981;      /* Verde éxito */
    --warning-color: #f59e0b;      /* Amarillo advertencia */
    --error-color: #ef4444;        /* Rojo error */
    --critical-color: #dc2626;     /* Rojo crítico */
}
```

### Modo Oscuro (Futuro)
El sistema está preparado para implementar modo oscuro con:
```css
@media (prefers-color-scheme: dark) {
    /* Estilos oscuros aquí */
}
```

## 📊 APIs Disponibles

### Autenticación
- `POST /admin/login` - Iniciar sesión
- `POST /admin/logout` - Cerrar sesión

### Dashboard
- `GET /admin/dashboard` - Estadísticas generales

### Usuarios
- `GET /admin/usuarios` - Listar usuarios
- `POST /admin/usuarios` - Crear usuario
- `GET /admin/usuarios/:id` - Obtener usuario
- `PUT /admin/usuarios/:id` - Actualizar usuario
- `DELETE /admin/usuarios/:id` - Eliminar usuario

### Familias
- `GET /admin/familias` - Listar familias
- `POST /admin/familias` - Crear familia
- `GET /admin/familias/:id` - Obtener familia
- `PUT /admin/familias/:id` - Actualizar familia
- `DELETE /admin/familias/:id` - Eliminar familia

### Alertas
- `GET /admin/alertas` - Listar alertas
- `POST /admin/alertas` - Crear alerta
- `PUT /admin/alertas/:id/atender` - Atender alerta
- `DELETE /admin/alertas/:id` - Eliminar alerta

### Catálogos
- `GET /admin/catalogos` - Listar catálogos
- `POST /admin/catalogos` - Crear catálogo
- `PUT /admin/catalogos/:id` - Actualizar catálogo
- `DELETE /admin/catalogos/:id` - Eliminar catálogo

### Logs
- `GET /admin/logs` - Consultar logs del sistema

### Microservicios
- `GET /admin/health` - Estado de microservicios
- `PUT /admin/microservicios/:id/estado` - Actualizar estado

## 🔒 Seguridad

### Autenticación JWT
- Tokens seguros con expiración
- Refresh automático de sesión
- Logout seguro con invalidación

### Validaciones
- Sanitización de inputs
- Validación en frontend y backend
- Protección CSRF (preparado)

### CORS
- Configuración segura de CORS
- Headers de seguridad
- Métodos permitidos controlados

## 🐛 Solución de Problemas

### Error: "Backend no responde"
```bash
# Verificar logs del backend
docker-compose logs backend-go

# Reiniciar servicios
docker-compose restart
```

### Error: "Archivos estáticos no cargan"
```bash
# Verificar que los archivos existan
ls -la static/css/style.css
ls -la static/js/app.js

# Reconstruir imagen
docker-compose build --no-cache backend-go
```

### Error: "Base de datos no conecta"
```bash
# Verificar estado de PostgreSQL
docker-compose logs postgres

# Verificar conexión
docker-compose exec postgres psql -U heartguard -d heartguard -c "SELECT 1;"
```

## 🚀 Próximas Mejoras

### Funcionalidades Planeadas
- [ ] **Gráficos interactivos** con Chart.js
- [ ] **Mapas de ubicaciones** con Leaflet
- [ ] **Notificaciones push** en tiempo real
- [ ] **Exportación de reportes** en PDF/Excel
- [ ] **Modo oscuro** automático
- [ ] **Temas personalizables**
- [ ] **Dashboard personalizable**
- [ ] **Búsqueda global** en tiempo real

### Optimizaciones
- [ ] **Lazy loading** de componentes
- [ ] **Cache inteligente** de datos
- [ ] **Compresión de assets**
- [ ] **Service Worker** para offline
- [ ] **PWA** (Progressive Web App)

## 📞 Soporte

Para soporte técnico o reportar bugs:
1. Revisar los logs con `docker-compose logs`
2. Verificar la documentación de la API
3. Consultar el script de prueba `./test_web.sh`

---

**🎉 ¡Disfruta del panel de superadministración de HeartGuard!**

Una interfaz moderna, segura y funcional para gestionar todo el sistema de monitoreo de salud familiar.
