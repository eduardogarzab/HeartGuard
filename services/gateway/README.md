# HeartGuard Gateway Service

Servicio gateway para el ecosistema HeartGuard basado en Flask. Este microservicio expone un punto de acceso unificado para paneles de organizaciones y clientes finales, orquestando llamadas hacia otros servicios internos.

## Características

- Arquitectura basada en `Flask` con patrón de aplicación por fábrica.
- Configuración por entorno mediante variables de entorno y archivo `.env` opcional.
- Rutas organizadas en *blueprints* para facilitar la modularidad.
- Cliente HTTP interno preparado para delegar llamadas a microservicios.
- Pruebas rápidas con `pytest` y servidor de desarrollo autorecargable.

## Requisitos

- Python 3.11+
- `pip` y `virtualenv` (o gestor equivalente)

## Instalación y ejecución en desarrollo

```bash
cd services/gateway
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make dev
```

El comando `make dev` levanta el servidor en modo debug escuchando en `http://localhost:5000`.

## Estructura

```
services/gateway
├── Makefile
├── README.md
├── requirements.txt
├── src/
│   └── gateway/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── extensions.py
│       ├── routes/
│       │   ├── __init__.py
│       │   └── health.py
│       └── services/
│           └── __init__.py
└── tests/
    ├── __init__.py
    └── test_health.py
```

## Próximos pasos sugeridos

1. Definir contratos entre el gateway y los microservicios de organizaciones, pacientes y usuarios.
2. Implementar autenticación delegada (por ejemplo JWT) y autorización basada en roles en el gateway.
3. Añadir clientes específicos dentro de `src/gateway/services/` para cada microservicio.
4. Integrar el gateway a la orquestación existente en `docker-compose.yml` cuando esté listo.
