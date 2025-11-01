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

## Modelos

El servicio define modelos SQLAlchemy para `organizations`, `org_roles`, `users` (mínimo) y `org_invitations`, con propiedades convenientes para serializar el estado de las invitaciones y su relación con organizaciones y roles.

## Pruebas

Ejecuta `pytest` desde la raíz del proyecto para validar la lógica del servicio.
