# 🫀 HeartGuard – Signal Service

Microservicio Flask encargado de **administrar señales biomédicas** (frecuencia cardíaca, presión
arterial, saturación de oxígeno, etc.) asociadas a los pacientes de una organización. Expone una
API REST bajo `/v1/signals`, con soporte **JSON/XML**, autenticación **JWT** emitida por
`auth_service` y auditoría mediante logs.

---

## 📦 Estructura

```
signal_service/
├─ app.py                 # Punto de entrada del microservicio
├─ config.py              # Configuración y carga de variables de entorno compartidas
├─ db/                    # Pool de conexiones PostgreSQL
│  └─ __init__.py
├─ repository/            # Consultas SQL (señales y membresías)
│  ├─ __init__.py
│  ├─ memberships.py
│  └─ signals.py
├─ responses/             # Respuestas unificadas JSON/XML
│  └─ __init__.py
├─ routes/                # Blueprints de Flask
│  └─ signals.py
├─ utils/                 # Autenticación JWT y utilidades de payload
│  ├─ __init__.py
│  ├─ auth.py
│  └─ payloads.py
├─ requirements.txt       # Dependencias específicas del servicio
└─ README.md
```

---

## ⚙️ Configuración

El servicio lee el archivo `.env` compartido ubicado en `microservicios/.env`. Variables principales:

```bash
SIGNAL_SERVICE_PORT=5007
SIGNAL_JWT_SECRET=super_secret
SIGNAL_DBHOST=localhost
SIGNAL_DBPORT=5432
SIGNAL_DBNAME=heartguard
SIGNAL_DBUSER=heartguard_app
SIGNAL_DBPASS=dev_change_me
SIGNAL_DBSCHEMA=heartguard
```

Si no se declaran, se reutilizan los valores genéricos (`PGHOST`, `DATABASE_URL`, `JWT_SECRET`, etc.).

---

## ▶️ Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r microservicios/signal_service/requirements.txt
python microservicios/signal_service/app.py
```

Health check:

```
GET http://localhost:5007/health
```

---

## 🔐 Autenticación

Todas las rutas requieren un **JWT válido** emitido por `auth_service`. El token debe incluir un
`identity` con `user_id` (y opcionalmente `org_id`). La pertenencia del usuario a la organización se
verifica mediante la tabla `user_org_membership`.

Header obligatorio:

```
Authorization: Bearer <ACCESS_TOKEN>
```

---

## 📡 Endpoints principales

- `POST /v1/signals` – Registra una nueva señal biomédica.
- `GET /v1/signals?patient_id=<uuid>` – Lista las señales de un paciente.
- `GET /v1/signals/<id>` – Obtiene el detalle de una señal concreta.
- `DELETE /v1/signals/<id>` – Elimina una señal registrada.

Todos los endpoints aceptan payloads en **JSON** y opcionalmente en **XML**.

---

## 🗄️ Esquema esperado

```sql
CREATE TABLE signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL,
    org_id UUID NOT NULL,
    signal_type TEXT NOT NULL,
    value NUMERIC NOT NULL,
    unit TEXT NOT NULL,
    recorded_at TIMESTAMPTZ,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

La relación del usuario se valida con la tabla `user_org_membership` ya existente en HeartGuard.
