# Media Service

Servicio responsable de gestionar archivos multimedia dentro de HeartGuard. Permite subir, consultar y eliminar archivos privados alojados en Google Cloud Storage, manteniendo el acceso restringido por organización.

## Endpoints principales

- `POST /v1/media/<entity>`: Subida de archivos (por ejemplo `patients` o `users`). Requiere enviar el archivo en `multipart/form-data` con el campo `file`.
- `GET /v1/media/<entity>/<object_name>`: Genera una URL firmada temporal para acceder al archivo.
- `DELETE /v1/media/<entity>/<object_name>`: Elimina el archivo del bucket.

Todos los endpoints requieren un JWT válido emitido por `auth_service` y solo permiten operar dentro de la organización del usuario.

## Dependencias

Consultar `requirements.txt` para la lista completa de librerías necesarias.
