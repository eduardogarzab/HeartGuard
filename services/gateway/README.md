# HeartGuard API Gateway

Gateway principal de la plataforma HeartGuard que centraliza el acceso a todos los microservicios del sistema.

## Descripción

El Gateway actúa como único punto de entrada (single entry point) para todas las peticiones HTTP hacia la plataforma HeartGuard. Se encarga de:

- **Enrutamiento**: Distribuye las peticiones a los microservicios correspondientes
- **Proxy transparente**: Reenvía requests/responses sin modificar payloads
- **CORS**: Gestiona políticas de acceso desde clientes web
- **Logging centralizado**: Registra todas las peticiones para auditoría
- **Manejo de errores**: Normaliza respuestas de error entre microservicios

## Arquitectura

\`\`\`
Cliente (Web/Mobile)
        ↓
   [Gateway :8000]
        ↓
   ┌────┴────┐
   │         │
Auth       (Otros
Service    Servicios)
:5001
\`\`\`

## Requisitos

- Python 3.10+
- PostgreSQL (compartida con microservicios)
- Auth Service corriendo en puerto 5001

## Instalación y Uso

\`\`\`bash
# Instalar dependencias
make install

# Iniciar gateway en modo desarrollo
make dev

# El gateway estará disponible en http://localhost:8000
\`\`\`

## Configuración

Crear archivo \`.env\` basado en \`.env.example\`:

\`\`\`env
FLASK_DEBUG=1
FLASK_SECRET_KEY=your-secret-key-here
GATEWAY_SERVICE_TIMEOUT=10
AUTH_SERVICE_URL=http://localhost:5001
ADMIN_SERVICE_URL=http://localhost:5002
USER_SERVICE_URL=http://localhost:5003
\`\`\`

## Testing

\`\`\`bash
# Ejecutar suite completa de pruebas
./test_gateway.sh
\`\`\`

## Endpoints Disponibles

### Health Check
\`\`\`bash
GET /health/
\`\`\`

### Autenticación (Proxy a Auth Service)

Todos los endpoints bajo \`/auth/*\` son proxies transparentes al Auth Service:

- \`POST /auth/register/user\` - Registro de usuario (staff)
- \`POST /auth/register/patient\` - Registro de paciente
- \`POST /auth/login/user\` - Login de usuario
- \`POST /auth/login/patient\` - Login de paciente
- \`GET /auth/verify\` - Verificar token JWT
- \`GET /auth/me\` - Obtener datos de cuenta autenticada
- \`POST /auth/refresh\` - Renovar access token

Ver documentación completa en [Auth Service README](../auth/README.md)

### Usuarios (Proxy a User Service)

Las rutas expuestas por el User Service pueden consumirse a través del gateway sin cambiar el path. Ejemplos:

- `GET /users/me` - Perfil del usuario autenticado
- `PATCH /users/me` - Actualización del perfil
- `GET /users/me/org-memberships` - Membresías del usuario
- `GET /orgs/<org_id>/dashboard` - Dashboard de la organización
- `GET /caregiver/patients` - Pacientes asignados al cuidador
- `POST /users/me/push-devices` - Registro de dispositivo push

Para la lista completa de endpoints revisa el [User Service README](../user/README.md).

## Estructura del Proyecto

\`\`\`
services/gateway/
├── src/gateway/
│   ├── app.py              # Factory de Flask app
│   ├── config.py           # Configuración
│   ├── extensions.py       # CORS
│   ├── routes/
│   │   ├── health.py        # Health check
│   │   ├── auth_proxy.py    # Proxy para Auth Service
│   │   ├── admin_proxy.py   # Proxy para Admin Service
│   │   └── user_proxy.py    # Proxy para User Service
│   └── services/
│       ├── auth_client.py   # Cliente HTTP para Auth Service
│       ├── admin_client.py  # Cliente HTTP para Admin Service
│       └── user_client.py   # Cliente HTTP para User Service
├── tests/
├── .env.example
├── Makefile
├── README.md
├── requirements.txt
└── test_gateway.sh
\`\`\`

## Seguridad

- **CORS**: Habilitado para todos los orígenes (configurar en producción)
- **Tokens JWT**: Validación delegada a Auth Service
- **HTTPS**: Recomendado usar proxy reverso (nginx/traefik) en producción

## Producción

\`\`\`bash
pip install gunicorn
PYTHONPATH=src gunicorn -w 4 -b 0.0.0.0:8000 "gateway.app:create_app()"
\`\`\`

## Licencia

Propiedad de HeartGuard. Todos los derechos reservados.
