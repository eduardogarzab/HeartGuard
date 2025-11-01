# Actualización del User Service

## Cambios Realizados

Se actualizó el `user_service` para conectarse a la base de datos real y obtener usuarios de una organización específica.

### Nuevo Endpoint
- **GET /users?org_code=FAM-001** - Lista usuarios filtrados por organización
- **POST /users/count** - Cuenta usuarios por organización

## Pasos para Actualizar

### 1. Reconstruir el Servicio

Desde la carpeta `Microservicios/`:

```powershell
# Detener el servicio actual
docker-compose stop user_service

# Reconstruir la imagen
docker-compose build user_service

# Iniciar el servicio
docker-compose up -d user_service
```

### 2. Verificar que el Servicio está Corriendo

```powershell
# Ver logs
docker-compose logs -f user_service

# Verificar health check
docker-compose ps user_service
```

### 3. Probar el Endpoint

```powershell
# Primero obtener un token
$loginBody = @"
<login_request>
  <email>ana.ruiz@heartguard.com</email>
  <password>Demo#2025</password>
</login_request>
"@

$loginResponse = Invoke-WebRequest -Uri "http://136.115.53.140:5000/auth/login" -Method POST -Headers @{"Content-Type"="application/xml"; "Accept"="application/xml"} -Body $loginBody

# Extraer el token de la respuesta XML (o usa el frontend)
# Luego probar el endpoint de usuarios
$token = "TU_TOKEN_AQUI"

Invoke-WebRequest -Uri "http://136.115.53.140:5000/users?org_code=FAM-001" -Method GET -Headers @{"Accept"="application/xml"; "Authorization"="Bearer $token"}
```

## Alternativa: Reiniciar Todos los Servicios

Si prefieres reiniciar todo:

```powershell
cd Microservicios
docker-compose down
docker-compose up -d --build
```

## Frontend

El frontend ya está actualizado para:
- Filtrar usuarios por organización FAM-001
- Mostrar nombre, email, roles, estatus y fecha de creación
- Manejar errores correctamente
- Mostrar mensajes cuando no hay usuarios

## Verificación

1. Abre el frontend: `http://localhost:8000`
2. Haz login con `ana.ruiz@heartguard.com` / `Demo#2025`
3. Navega a la sección "Usuarios" 👥
4. Deberías ver los usuarios de la organización FAM-001

### Usuarios Esperados en FAM-001:
- Dra. Ana Ruiz (org_admin)
- Martin Ops (org_user)
