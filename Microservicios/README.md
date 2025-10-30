# HeartGuard Microservicios

Este documento explica cómo preparar el entorno local, levantar la plataforma de microservicios y realizar peticiones de prueba a través del API Gateway. Mantén este archivo actualizado cada vez que cambien los pasos de despliegue o las rutas disponibles.

## 1. Prerrequisitos

- Docker y Docker Compose v2.
- Python 3.11+ (solo si deseas ejecutar servicios o scripts fuera de Docker).
- Acceso al archivo `.env` con secretos reales. Puedes partir de `.env.example`.

## 2. Preparar variables de entorno

1. Copia el archivo de ejemplo:
   ```bash
   cp Microservicios/.env.example Microservicios/.env
   ```
2. Genera valores seguros para:
   - `JWT_SECRET`
   - `POSTGRES_PASSWORD`
   - `RABBITMQ_DEFAULT_PASS`
   - `DOCKER_INFLUXDB_INIT_PASSWORD`
   - `INFLUX_TOKEN`
3. Ajusta los puertos si es necesario. El Gateway se expone en `GATEWAY_PORT` (por defecto 5000).
4. Revisa que cada servicio tenga su `DATABASE_URL` asignada. El archivo de ejemplo declara un esquema por servicio usando `POSTGRES_URL_*`.

## 3. Levantar la plataforma completa

Dentro del directorio `Microservicios/` ejecuta:
```bash
cd Microservicios
docker compose up --build
```
Esto iniciará Postgres, RabbitMQ, InfluxDB y los microservicios (que se comunican por la red interna). Solo el Gateway, RabbitMQ (puerto 15672) e InfluxDB (puerto 8086) quedan expuestos fuera del cluster Docker.

> **Nota:** La primera vez que suba el stack, SQLAlchemy generará las tablas automáticamente. Si añades nuevos modelos recuerda aplicar las migraciones correspondientes.

## 4. Flujos básicos de prueba

Todas las peticiones externas deben ir al Gateway (`http://localhost:5000`). La cabecera `Content-Type: application/json` es obligatoria y se recomienda propagar `X-Request-ID` para trazabilidad.

### 4.1 Registrar un usuario administrador
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
        "email": "admin@example.com",
        "password": "ChangeMe123!",
        "roles": ["admin"]
      }'
```
La respuesta incluye los tokens `access_token` y `refresh_token`.

### 4.2 Autenticarse
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
        "email": "admin@example.com",
        "password": "ChangeMe123!"
      }'
```
Guarda el `access_token` para futuras peticiones.

### 4.3 Crear un paciente
```bash
ACCESS_TOKEN="<token devuelto por /auth/login>"

curl -X POST http://localhost:5000/patient/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -d '{
        "first_name": "Jane",
        "last_name": "Doe",
        "mrn": "MRN-001",
        "birth_date": "1980-05-16",
        "notes": "Paciente demo"
      }'
```

### 4.4 Listar pacientes
```bash
curl -X GET http://localhost:5000/patient/patients \
  -H "Authorization: Bearer ${ACCESS_TOKEN}"
```

## 5. Comprobaciones de salud
Cada servicio expone un endpoint `/health` detrás del Gateway, por ejemplo:
```bash
curl http://localhost:5000/auth/health
curl http://localhost:5000/patient/health
```
Un estado distinto a `200 OK` indica que el contenedor podría haber fallado su `healthcheck`.

## 6. Detener servicios

```bash
docker compose down
```
Usa `--volumes` solo si deseas borrar los datos persistidos de Postgres, RabbitMQ o InfluxDB.

## 7. Solución de problemas

- Verifica los logs: `docker compose logs -f <nombre_servicio>`.
- Asegúrate de que `DATABASE_URL` esté definido; de lo contrario, el servicio registrará una advertencia y no podrá acceder a Postgres.
- Comprueba que los puertos 5000 (Gateway), 15672 (RabbitMQ UI) y 8086 (InfluxDB UI) no estén ocupados por otros procesos.

Mantén este README sincronizado con cualquier cambio de infraestructura, dependencias o endpoints relevantes.
