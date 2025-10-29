# patient_service

Microservicio Flask encargado de administrar pacientes por organización dentro del ecosistema HeartGuard.

## Endpoints principales

- `POST /v1/patients`: crea un paciente para la organización indicada.
- `GET /v1/patients`: lista pacientes filtrando por organización.
- `GET /v1/patients/<id>`: obtiene el detalle de un paciente.
- `PATCH /v1/patients/<id>`: actualiza campos del paciente.
- `DELETE /v1/patients/<id>`: elimina un paciente.

Todas las rutas requieren autenticación mediante JWT emitido por `auth_service`. Las respuestas soportan JSON y XML según el encabezado `Accept`.
