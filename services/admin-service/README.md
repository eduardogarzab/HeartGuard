# Admin Service

El servicio **admin-service** proporciona las APIs necesarias para gestionar organizaciones, usuarios, pacientes y equipos de cuidado desde el panel administrativo. Está construido con Flask y sigue los patrones de diseño del resto del ecosistema HeartGuard.

## Características
- Inicialización mediante `create_app` utilizando el patrón Factory.
- Estructura modular basada en Blueprints, Services y Repositories.
- Integración con `auth-service` para validar tokens JWT.
- Validación de entradas y salidas con Pydantic.
- Conexión a PostgreSQL usando SQLAlchemy.

## Configuración

1. Copia el archivo `.env.example` a `.env` y ajusta las variables de entorno.
2. Crea un entorno virtual e instala las dependencias:

```bash
make install
```

3. Ejecuta el servicio en modo desarrollo:

```bash
make run
```

4. Ejecuta las pruebas:

```bash
make test
```

## Tests

Las pruebas utilizan `pytest` y se ubican en el directorio `tests/`.
