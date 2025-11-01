# Organization Service

Este microservicio gestiona entidades de organización, incluyendo la emisión y ciclo de vida de invitaciones.

## Endpoints relevantes

### `GET /organization/invitations`

Lista invitaciones existentes. Parámetros:

- `org_id` (opcional): UUID de la organización para filtrar resultados.

Respuesta de ejemplo:

```json
{
  "status": "success",
  "code": 200,
  "data": {
    "invitations": [
      {
        "id": "8f6a…",
        "org_id": "d91c…",
        "email": "user@example.com",
        "role": "org_admin",
        "status": "pending",
        "token": "fc3b…",
        "created_at": "2024-05-18T12:00:00+00:00",
        "expires_at": "2024-05-20T12:00:00+00:00",
        "used_at": null,
        "revoked_at": null
      }
    ]
  },
  "meta": {"total": 1}
}
```

### `POST /organization/invitations`

Crea una invitación para una organización. Cuerpo JSON o XML con los campos:

- `org_id` (UUID) – requerido.
- `role` u `org_role_id` – requerido. Puede ser el código o el UUID del rol.
- `email` (opcional) – correo de la persona invitada.
- `ttl_hours` (int) – requerido, entre 1 y 720.

Ejemplo JSON:

```json
{
  "org_id": "d91c…",
  "role": "org_admin",
  "email": "user@example.com",
  "ttl_hours": 24
}
```

Respuesta `201 Created`:

```json
{
  "status": "success",
  "code": 201,
  "data": {
    "invitation": {
      "id": "8f6a…",
      "org_id": "d91c…",
      "email": "user@example.com",
      "role": "org_admin",
      "status": "pending",
      "token": "fc3b…",
      "created_at": "2024-05-18T12:00:00+00:00",
      "expires_at": "2024-05-19T12:00:00+00:00",
      "used_at": null,
      "revoked_at": null
    }
  }
}
```

### `POST /organization/invitations/<invitation_id>/cancel`

Revoca una invitación pendiente. No acepta cuerpo. Devuelve `204 No Content` si la invitación estaba activa. Las invitaciones ya usadas o canceladas responden `404`.

### `GET /organization/invitations/<token>/validate`

Endpoint orientado a integraciones externas que siempre responde en XML. Devuelve el estado de la invitación asociada al token (`pending`, `used`, `revoked`, `expired`) junto con metadatos relevantes.

Ejemplo de respuesta para una invitación activa:

```xml
<response>
  <invitation>
    <token>fc3b…</token>
    <result>valid</result>
    <state>pending</state>
    <org_id>d91c…</org_id>
    <role>org_admin</role>
    <expires_at>2024-05-19T12:00:00+00:00</expires_at>
  </invitation>
</response>
```

Si la invitación no existe, la respuesta es `404` con `result="invalid"` y `reason="not_found"`.

### `POST /organization/invitations/<token>/consume`

Marca la invitación como usada si está pendiente y responde en XML describiendo el resultado.

- `200 OK` con `result="used"` cuando el token estaba pendiente.
- `409 Conflict` con `result="revoked"`, `"used"` o `"expired"` si el token ya no es válido.
- `404 Not Found` cuando el token no existe.

El endpoint no requiere cuerpo y respeta la cabecera `Accept: application/xml`.

## Modelos

El servicio define modelos SQLAlchemy para `organizations`, `org_roles`, `users` (mínimo) y `org_invitations`, con propiedades convenientes para serializar el estado de las invitaciones y su relación con organizaciones y roles.

## Flujo de invitaciones

1. **Creación**: el servicio delega la inserción a la función SQL `heartguard.sp_org_invitation_create`, evitando duplicar la generación del token y asegurando el cálculo de expiraciones en un único punto. En entornos sin PostgreSQL (por ejemplo, pruebas SQLite) existe un modo de compatibilidad que replica el comportamiento esencial.
2. **Validación**: `/organization/invitations/<token>/validate` permite consultar el estado vigente sin modificar la invitación.
3. **Consumo**: `/organization/invitations/<token>/consume` marca el token como usado y devuelve inmediatamente el nuevo estado.
4. **Revocación**: `/organization/invitations/<invitation_id>/cancel` establece `revoked_at` y los otros endpoints reflejan la transición al estado `revoked`.

## Pruebas

Ejecuta `pytest` desde la raíz del proyecto para validar la lógica del servicio.
