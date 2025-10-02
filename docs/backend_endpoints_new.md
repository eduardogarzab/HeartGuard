# Nuevos endpoints y extensiones del panel Superadmin

## Invitaciones de organización

### `GET /v1/superadmin/invitations`
- **Query**: `org_id` (requerido para filtrar por organización), `status` (`pending|used|revoked|expired`), `limit` (<=200), `offset`.
- **Respuesta 200**: arreglo de invitaciones con `status`, `org_role_code`, `expires_at`, `created_at` y campos de auditoría (`used_at`, `revoked_at`).
- **Errores**: `400 bad_request` por filtros inválidos, `500 db_error` ante fallos de consulta.
- **Auditoría**: solo lectura, sin registro.
- **Seguridad**: requiere sesión superadmin y respeta encabezados `X-RateLimit-*`/`Retry-After`.
- **Implementación**: utiliza la función `heartguard.fn_invitation_list` para resolver filtros y paginación.

### `POST /v1/superadmin/invitations`
- **Body**: `{ org_id (uuid), org_role_id (uuid), email?, ttl_hours (1-720) }`.
- **Validaciones**: `uuid4`, email opcional, TTL dentro del rango permitido.
- **Respuesta 201**: invitación creada con `status` calculado y token generado en servidor.
- **Errores**: `422 invalid_fields` si falta `weight` según rol, `500 db_error` en errores de inserción, `409 conflict` en colisiones de token.
- **Auditoría**: `INVITE_CREATE` con detalles `{ org_id }` y `duration_ms`.
- **Stored procedure**: `heartguard.fn_invitation_create` encapsula la lógica (token aleatorio, TTL y retorno atomizado).

### `DELETE /v1/superadmin/invitations/{id}`
- **Acción**: marca invitación como revocada si está vigente.
- **Respuesta 204**.
- **Errores**: `404 not_found` cuando ya fue usada/revocada, `500 db_error` en fallos inesperados.
- **Auditoría**: `INVITE_CANCEL` con `entity_id` y `duration_ms`.
- **Stored procedure**: `heartguard.fn_invitation_cancel` asegura idempotencia.

### `POST /v1/superadmin/invitations/{token}/consume`
- **Body**: `{ user_id }` (uuid).
- **Respuesta 204** al vincular o actualizar la membresía.
- **Errores**: `400 invalid_token` cuando expiró o fue usada, `500 db_error` para fallos.
- **Auditoría**: `INVITE_CONSUME` con token y duración.

## Catálogos administrativos

### `GET /v1/superadmin/catalogs`
- **Acción**: devuelve el catálogo de catálogos (slug, label, descripción, `has_weight`).
- **Auditoría**: lectura, sin registro.
- **Stored procedure**: `heartguard.fn_catalog_resolve` centraliza la resolución de slugs.

### `GET /v1/superadmin/catalogs/{slug}`
- **Query**: `limit`, `offset`.
- **Respuesta**: filas `{ id, code, label, weight? }` ordenadas por label.
- **Errores**: `404 not_found` si el slug es inválido, `500 db_error` en fallos.
- **Stored procedure**: `heartguard.fn_catalog_list` aplica la lógica de paginación y peso opcional.

### `POST /v1/superadmin/catalogs/{slug}`
- **Body**: `{ code, label, weight? }` (`weight` obligatorio cuando `has_weight=true`).
- **Respuesta 201** con la fila creada.
- **Errores**: `422 invalid_fields` si falta `weight`, `409 conflict` en duplicados, `500 db_error` para otros casos.
- **Auditoría**: `CATALOG_CREATE` con `duration_ms` y `code`.
- **Stored procedure**: `heartguard.fn_catalog_create` asegura inserciones tipadas por slug.

### `PATCH /v1/superadmin/catalogs/{slug}/{id}`
- **Body**: campos opcionales `code`, `label`, `weight`.
- **Respuesta 200** con valores actualizados.
- **Errores**: `404 not_found` si la fila no existe, `409 conflict` por códigos duplicados, `500 db_error` en fallos.
- **Auditoría**: `CATALOG_UPDATE` con `entity_id` y `duration_ms`.
- **Stored procedure**: `heartguard.fn_catalog_update` maneja columnas condicionales.

### `DELETE /v1/superadmin/catalogs/{slug}/{id}`
- **Acción**: elimina elemento del catálogo.
- **Respuesta 204**.
- **Errores**: `404 not_found` si no existe, `500 db_error` para fallos.
- **Auditoría**: `CATALOG_DELETE` registra la eliminación con duración.
- **Stored procedure**: `heartguard.fn_catalog_delete` devuelve bool para idempotencia.

## Métricas y actividad reciente

### `GET /v1/superadmin/metrics/overview`
- **Query**: `window_minutes` (>=5, default 1440), `recent_limit` (1-50).
- **Respuesta 200**:
  ```json
  {
    "average_response_ms": 42.5,
    "operation_counts": [{"action": "ORG_CREATE", "count": 3}],
    "active_users": 5,
    "active_organizations": 3,
    "total_users": 20,
    "total_organizations": 7,
    "pending_invitations": 2,
    "recent_activity": [{"ts": "2024-05-15T12:34:00Z", "action": "APIKEY_CREATE", "entity": "api_key", "user_id": "..."}]
  }
  ```
- **Errores**: `500 db_error` ante fallos en agregados.
- **Auditoría**: sólo lectura.
- **Stored procedures**: `heartguard.fn_metrics_overview` consolida promedios/conteos usando `audit_logs`; `heartguard.fn_metrics_recent_activity` entrega la ventana de eventos.

## Notas de auditoría y seguridad
- Todas las mutaciones usan `writeAuditWithDuration`, agregando `duration_ms` a los detalles.
- `RequireSuperadmin` continúa protegiendo las rutas; el middleware de rate-limit añade `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` y `Retry-After` cuando corresponde.
- Las funciones almacenadas viven en el esquema `heartguard` y se otorgan a `:dbuser`, permitiendo reutilización desde otras herramientas administrativas.
