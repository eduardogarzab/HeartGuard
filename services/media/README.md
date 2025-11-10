# Media Service - HeartGuard

Microservicio encargado del ciclo de vida de la foto de perfil (usuario o paciente) almacenada en DigitalOcean Spaces. Expone endpoints JSON o XML dependiendo del encabezado `Accept`.

## 🚀 Capacidades

- Subir una foto de perfil (`POST /media/<entity>/<id>/photo`)
- Reemplazar una foto ya existente (`PUT` o reintentar `POST` sobre la misma ruta)
- Eliminar la foto y limpiar objetos asociados (`DELETE /media/<entity>/<id>/photo`)
- Respuestas en `application/json` (por defecto) u `application/xml`
- Validación de JWT emitidos por Auth Service (tipos `user` y `patient`)

## 🏗️ Arquitectura

| Componente | Descripción |
|------------|-------------|
| Flask 3    | Framework HTTP |
| boto3      | Cliente S3-compatible para DigitalOcean Spaces |
| PyJWT      | Validación local de tokens JWT |

### Estructura

```
media/
├── Makefile
├── requirements.txt
├── README.md
├── .env.example
├── src/
│   └── media/
│       ├── app.py                 # Factory Flask y registro de blueprints
│       ├── config.py              # Carga de entorno y derivación de parámetros de Spaces
│       ├── blueprints/
│       │   └── media.py           # Endpoints principales de foto de perfil
│       ├── middleware/
│       │   └── auth.py            # Decoradores y helpers de autenticación JWT
│       ├── services/
│       │   └── photo_service.py   # Lógica de negocio para guardar/eliminar fotos
│       ├── storage/
│       │   └── spaces_client.py   # Wrapper sobre boto3 para DO Spaces
│       └── utils/
│           ├── jwt_utils.py       # Decodificación de JWT
│           └── responses.py       # Serialización JSON/XML y manejo de trace_id
└── tests/
    ├── test_photo_service.py
    └── test_responses.py
```

## 🔧 Variables de entorno

| Variable | Descripción |
|----------|-------------|
| `ID` | Access key de DigitalOcean Spaces |
| `KEY` | Secret key de DigitalOcean Spaces |
| `ORIGIN_ENDPOINT` | Endpoint público del bucket (p. ej. `https://bucket.region.digitaloceanspaces.com/`) |
| `SPACES_BUCKET` *(opcional)* | Nombre del bucket. Si no se define, se infiere del endpoint |
| `SPACES_REGION` *(opcional)* | Región (`nyc3`, `atl1`, etc.). Se infiere del endpoint si no se define |
| `SPACES_ENDPOINT` *(opcional)* | Endpoint S3 directo (p. ej. `https://atl1.digitaloceanspaces.com`) |
| `MEDIA_CDN_BASE_URL` *(opcional)* | Base URL para construir enlaces públicos. Por defecto `ORIGIN_ENDPOINT` |
| `JWT_SECRET` | Secreto HS256 compartido con Auth Service |
| `MEDIA_MAX_FILE_MB` | Tamaño máximo permitido por archivo (por defecto 5 MB) |
| `MEDIA_ALLOWED_CONTENT_TYPES` | Lista separada por comas de MIME types permitidos |

## ▶️ Ejecución local

```bash
# Instalar dependencias
make install

# Ejecutar en modo desarrollo
make dev

# Probar endpoints (requiere token válido)
curl -X POST \
  http://localhost:5005/media/users/<user_id>/photo \
  -H "Authorization: Bearer <TOKEN>" \
  -F "photo=@/ruta/a/foto.jpg"
```

## 🔒 Seguridad

- Requiere encabezado `Authorization: Bearer <token>`.
- Acepta JWT con `account_type = user` o `patient`.
- Para rutas `/media/users/{id}` exige que el usuario autenticado sea el dueño del token.
- Para `/media/patients/{id}` permite tokens de pacientes (mismo `patient_id`) o tokens de usuario.

## 🧪 Testing

```bash
make test
```

Las pruebas se ejecutan con `pytest` y cubren:
- Validación de tipos de contenido soportados
- Generación del nombre de objeto en Spaces
- Serialización JSON/XML con negotiation por encabezado `Accept`

## 🔁 Health Check

`GET /health` → `status: success` con detalles del servicio.

## 📎 Notas

- El servicio no persiste metadatos en base de datos; devuelve la URL final para que el consumidor la registre.
- La eliminación limpia todas las variantes de foto registradas bajo el prefijo del usuario/paciente en el bucket.
- Respuestas estandarizadas contienen `trace_id` para facilitar trazabilidad.
