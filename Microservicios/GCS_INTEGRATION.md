# Media Service Placeholder - Integración diferida

El microservicio de media continúa en estado **placeholder** mientras se rediseña la estrategia de almacenamiento. Toda la integración previa con Google Cloud Storage se encuentra suspendida.

## Situación actual
- No se realizan cargas ni descargas de archivos.
- Las rutas principales responden con `501 Not Implemented` para dejar claro que la funcionalidad aún no existe.
- No es necesario provisionar buckets ni credenciales de GCS en esta etapa.

## Impacto en la infraestructura
- Los contenedores pueden desplegarse sin secretos adicionales.
- La arquitectura reserva el espacio para futuras integraciones (volúmenes y variables de entorno), pero permanecen inactivos.
- Los planes de backup solo consideran PostgreSQL e InfluxDB por ahora.

## Próximas actividades
1. Elegir almacenamiento definitivo (GCS, S3 u opción on-premise).
2. Reintroducir dependencia de `google-cloud-storage` (u otra librería equivalente) y ajustes de infraestructura.
3. Redactar nuevamente esta guía con pasos de configuración, ejemplos de cURL y matrices de pruebas.

## Referencias útiles
- Health check para monitorear el servicio: `curl http://136.115.53.140:5000/media/health | jq .`
- Documentación de diseño general: `Microservicios/PLAN.md`.

> **Nota:** Conserva este archivo como recordatorio del estado actual. Una vez que la funcionalidad se active, se restaurarán los apartados originales con instrucciones detalladas.
