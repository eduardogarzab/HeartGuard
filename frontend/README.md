# Frontend HeartGuard - Panel Administrativo

Panel de administración web para HeartGuard que se conecta a los microservicios mediante el API Gateway.

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.x (para servir archivos estáticos)
- Acceso al API Gateway en `http://136.115.53.140:5000`

### Levantar el Frontend

1. Navega a la carpeta del frontend:
   ```powershell
   cd frontend
   ```

2. Inicia un servidor HTTP simple:
   ```powershell
   python -m http.server 8000
   ```

3. Abre tu navegador en: `http://localhost:8000`

## 📁 Estructura de Archivos

```
frontend/
├── index.html              # Página de login
├── dashboard.html          # Panel principal
├── test-auth.html          # Herramienta de diagnóstico
├── assets/
│   └── logo.svg           # Logo de HeartGuard
├── css/
│   ├── styles.css         # Estilos del login
│   └── dashboard.css      # Estilos del dashboard
└── js/
    ├── config.js          # Configuración de URLs del API
    ├── xmlClient.js       # Cliente para peticiones XML
    ├── auth.js            # Lógica de autenticación
    └── dashboard.js       # Lógica del dashboard
```

## 🔑 Usuarios de Prueba

### Administrador de Organización
- **Email:** `ana.ruiz@heartguard.com`
- **Password:** `Demo#2025`
- **Rol:** `org_admin` en organización FAM-001

## 🔧 Configuración del API

El frontend se conecta al API Gateway centralizado. La configuración está en `js/config.js`:

```javascript
export const API_CONFIG = {
  BASE_URL: "http://136.115.53.140:5000",
  // ...endpoints
};
```

### Cambiar la URL del API

Si necesitas cambiar la URL del servidor, edita el archivo `js/config.js` y modifica `BASE_URL`.

## 🧪 Diagnóstico de Problemas

### 1. Test de Autenticación

Abre `http://localhost:8000/test-auth.html` para probar el endpoint de login y ver la respuesta completa del servidor.

### 2. Verificar Conectividad al Gateway

```powershell
Invoke-WebRequest -Uri "http://136.115.53.140:5000/health" -Method GET
```

### 3. Consola del Navegador

Abre las DevTools (F12) y revisa la pestaña Console para ver:
- Respuestas XML completas
- Tokens JWT decodificados
- Errores de red o parseo

## 📡 Endpoints Utilizados

| Servicio | Endpoint | Método | Descripción |
|----------|----------|--------|-------------|
| Auth | `/auth/login` | POST | Autenticación de usuarios |
| Users | `/users/count` | POST | Contador de usuarios |
| Patients | `/patients/count` | POST | Contador de pacientes |
| Devices | `/devices/count` | POST | Contador de dispositivos |
| Inferences | `/inferences/count` | POST | Contador de inferencias |

## ⚠️ Notas Importantes

1. **Usa el Gateway**: Todas las peticiones van a través del puerto 5000 (gateway), no a los puertos individuales de cada servicio.

2. **CORS**: El gateway está configurado con CORS habilitado para aceptar peticiones del frontend.

3. **Módulos ES6**: Los archivos JS usan `import/export`, por lo que las etiquetas script incluyen `type="module"`.

4. **LocalStorage**: Los tokens JWT se guardan en localStorage del navegador.

## 🐛 Problemas Comunes

### "NetworkError when attempting to fetch resource"

**Causa:** El gateway no está accesible o no está corriendo.

**Solución:** Verifica que los microservicios estén corriendo:
```bash
cd Microservicios
docker-compose ps
```

### "Error: Respuesta de autenticación inválida"

**Causa:** El XML no se está parseando correctamente.

**Solución:** 
1. Abre test-auth.html para ver la respuesta real del servidor
2. Revisa la consola del navegador para logs detallados

### No se muestran las métricas en el dashboard

**Causa:** Los endpoints de métricas pueden no estar implementados o requieren datos en la base de datos.

**Solución:** Revisa la consola del navegador para ver qué endpoints fallan específicamente.

## 🔐 Seguridad

⚠️ **IMPORTANTE**: Este es un entorno de desarrollo. En producción:

1. Usa HTTPS en lugar de HTTP
2. Implementa refresh tokens
3. Valida tokens en el backend
4. Implementa rate limiting
5. Usa variables de entorno para las URLs

## 📝 TODO

- [ ] Implementar refresh automático de tokens
- [ ] Agregar más vistas al dashboard (lista de pacientes, etc.)
- [ ] Implementar manejo de roles y permisos
- [ ] Agregar paginación a las listas
- [ ] Implementar búsqueda y filtros
