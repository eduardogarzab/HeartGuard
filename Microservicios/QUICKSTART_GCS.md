# Media Service Placeholder

El servicio de media se encuentra en modo *placeholder* mientras se define la solución de almacenamiento definitiva.

## Estado actual
- `GET /media/health` responde con el estado `placeholder`.
- `GET /media`, `POST /media/upload` y `GET/DELETE /media/{id}` retornan `501 Not Implemented`.
- No se requiere configurar Google Cloud Storage ni archivos de credenciales.

## Cómo verificar que el contenedor esté listo

```bash
curl http://136.115.53.140:5000/media/health | jq .
```

La respuesta incluye `{"implemented": false}` para resaltar que aún no existe funcionalidad de manejo de archivos.

## Próximos pasos planificados
1. Seleccionar la plataforma de almacenamiento (GCS u otra alternativa gestionada).
2. Diseñar flujos de carga/descarga con control de acceso.
3. Documentar nuevamente los comandos de línea de comandos y ejemplos de integración.

Mientras tanto, conserva este archivo como referencia rápida del estado actual del servicio.
