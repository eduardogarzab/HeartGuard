# Nuevos endpoints y extensiones del panel Superadmin

## Invitaciones de organización

### `GET /v1/superadmin/organizations/{id}/invitations`
- **Query**: `limit` (opcional, <=200), `offset` (opcional).
- **Respuesta 200**: arreglo de invitaciones con campos `status`, `revoked_at`, `org_role_code`.
- **Errores**: `500 db_error` si falla la consulta.
- **Auditoría**: solo lectura, no genera evento.
- **Rate-limit**: encabezados `X-RateLimit-*` y `Retry-After` cuando aplica.

### `DELETE /v1/superadmin/invitations/{id}`
- **Acción**: marca una invitación como revocada cuando no fue usada.
- **Respuesta 204**.
- **Errores**:
  - `404 not_found` si la invitación no existe o ya se usó/revocó.
  - `500 db_error` en fallas inesperadas.
- **Auditoría**: `INVITE_CANCEL` con `entity_id` la invitación revocada.

### `POST /v1/superadmin/organizations/{id}/invitations`
- **Extensión**: el payload existente ahora persiste `revoked_at` y expone `status` calculado en la respuesta.
- **Auditoría**: `INVITE_CREATE` con `org_id`.

## Membresías de organización

### `GET /v1/superadmin/organizations/{id}/members`
- **Query**: `limit`, `offset`.
- **Respuesta 200**: arreglo de miembros con campos `email`, `name`, `org_role_code`, `joined_at`.
- **Errores**: `500 db_error`.
- **Auditoría**: solo lectura.

### `POST /v1/superadmin/organizations/{id}/members`
- **Extensión**: al crear/actualizar membresía se registra `user_id` en detalles de auditoría.

### `DELETE /v1/superadmin/organizations/{id}/members/{userId}`
- **Extensión**: auditoría incluye `user_id` en detalles.

## Rate limit global
- El middleware ahora agrega `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` en todas las respuestas.
- En caso de exceso se devuelve `429` con `Retry-After` en segundos.

## Auditoría
- Nuevas acciones: `INVITE_CANCEL`, `MEMBER_ADD`/`MEMBER_REMOVE` incluyen `user_id` en los detalles.
- Se centralizó la escritura de auditoría con helper que respeta `audit.Ctx`.

## Seguridad
- Todas las rutas siguen protegidas por `RequireSuperadmin` y el rate-limit descrito arriba.
- El endpoint de revocación de invitación verifica que no esté usada ni revocada previamente.

