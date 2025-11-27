# User Service - HeartGuard

Microservicio destinado a gestionar la información del usuario autenticado dentro del ecosistema HeartGuard. Provee endpoints JSON para consultar y actualizar datos del perfil, así como revisar las membresías de organización a las que pertenece el usuario.

## 🎯 Propósito

- Exponer el perfil consolidado del usuario autenticado.
- Permitir la actualización controlada de atributos personales (nombre, foto de perfil, estado de 2FA).
- Listar las organizaciones en las que participa el usuario y sus roles asignados.
- Consultar los detalles de membresía para una organización específica.

## 🏗️ Arquitectura

- **Puerto por defecto:** 5003
- **Framework:** Flask 3 + Blueprints
- **Base de datos:** PostgreSQL (esquema HeartGuard)
- **Autenticación:** JWT emitidos por Auth Service, validados con middleware compartido.
- **Respuesta:** Exclusivamente JSON con cabecera `Content-Type: application/json`.

## 📡 Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/users/me` | Devuelve el perfil del usuario autenticado. |
| `PATCH` | `/users/me` | Actualiza nombre, foto de perfil o bandera de 2FA. |
| `GET` | `/users/me/org-memberships` | Lista organizaciones y roles vinculados al usuario. |
| `GET` | `/orgs/{org_id}/members/{user_id}` | Devuelve los detalles de la membresía en una organización. |
| `GET` | `/orgs/{org_id}/dashboard` | Resumen operativo de la organización y métricas clave. |
| `GET` | `/orgs/{org_id}/care-teams` | Equipos de cuidado y sus integrantes. |
| `GET` | `/orgs/{org_id}/care-team-patients` | Pacientes agrupados por equipo de cuidado. |
| `GET` | `/orgs/{org_id}/patients/{patient_id}` | Perfil clínico del paciente dentro de la organización. |
| `GET` | `/orgs/{org_id}/patients/{patient_id}/alerts` | Alertas recientes del paciente (paginadas). |
| `GET` | `/orgs/{org_id}/patients/{patient_id}/notes` | Notas / ground-truth registrados para el paciente. |
| `GET` | `/orgs/{org_id}/metrics` | Métricas agregadas de pacientes y alertas. |
| `GET` | `/caregiver/patients` | Pacientes disponibles para el cuidador autenticado. |
| `GET` | `/caregiver/patients/{patient_id}` | Detalle del paciente y relación de cuidador. |
| `GET` | `/caregiver/patients/{patient_id}/alerts` | Alertas del paciente visibles para el cuidador. |
| `GET` | `/caregiver/patients/{patient_id}/notes` | Notas del paciente visibles para el cuidador. |
| `POST` | `/caregiver/patients/{patient_id}/notes` | Registra una nueva nota/ground-truth asociada al paciente. |
| `GET` | `/caregiver/metrics` | Métricas resumidas para el cuidador. |
| `GET` | `/health` | Estado básico del servicio (sin autenticación). |

Cada respuesta incluye los campos `status`, `message`, `error`, `data` y `trace_id`.

### Nuevas capacidades

- **Panel organizacional**: métricas agregadas, equipos de cuidado, pacientes y alertas filtradas por organización.
- **Flujos de cuidador**: listado de pacientes asignados, detalle y creación de notas ground-truth con validación de permisos.
- **Seguridad**: todos los endpoints verifican membresías de organización o relaciones de cuidador antes de exponer datos sensibles.

## 🔒 Autenticación

- Todas las rutas bajo `/users/*` y `/orgs/*` requieren un JWT válido en el encabezado `Authorization: Bearer <token>`.
- El payload debe contener `account_type = "user"` y `user_id`.

## 🌐 Variables de Entorno

```bash
DATABASE_URL=postgresql://heartguard_app:password@host:5432/heartguard
JWT_SECRET=change-me
PORT=5003
FLASK_ENV=development
LOG_LEVEL=INFO
```

## 📦 Dependencias

```txt
Flask==3.0.0
Flask-CORS==4.0.0
PyJWT==2.8.0
psycopg2-binary==2.9.0
python-dotenv==1.0.0
```

## 🚀 Uso rápido

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar en modo desarrollo
python -m flask --app src.user.app run --port 5003 --reload
```

## 🧪 Pruebas

Se recomienda agregar suites de pruebas `pytest` enfocadas en cada blueprint y capa de servicio. El comando `make test` ejecuta las pruebas en `tests/`.

## 🔐 Seguridad

- Valida tokens con secreto compartido proveniente de Auth Service.
- Impide manipular roles o membresías desde este servicio.
- Respuestas homogéneas con `trace_id` para facilitar el seguimiento en logs.

## 📄 Licencia

Propiedad de HeartGuard - Todos los derechos reservados.
