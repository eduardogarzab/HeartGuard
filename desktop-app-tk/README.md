# HeartGuard Desktop (Tkinter)

Aplicación de escritorio construida con Python y Tkinter que replica los flujos claves de la aplicación `desktop-app` original (Swing/JavaFX). Utiliza los mismos endpoints del gateway para login, registro y dashboards tanto de pacientes como de personal clínico.

## Requisitos

- Python 3.11 o superior
- Acceso a los servicios de HeartGuard (gateway HTTP)
- Sistema operativo Windows, macOS o Linux con soporte para Tkinter

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> **Nota:** `tkintermapview` requiere acceso a internet para descargar los tiles de OpenStreetMap. Si no puede instalarse o ejecutarse, la aplicación mostrará un mensaje con instrucciones para instalarlo manualmente y seguirá funcionando sin el mapa.

## Ejecución

```bash
python -m heartguard_tk.app
```

## Características principales

- Inicio de sesión para usuarios (staff) y pacientes
- Registro de usuarios y pacientes (campos equivalentes al cliente Java)
- Dashboard de paciente con métricas, alertas, cuidadores y mapa de ubicaciones recientes
- Dashboard de usuario con selector de organización, métricas clínicas, equipos de cuidado, pacientes y alertas
- Cliente HTTP reutilizable con la misma semántica de errores que `ApiClient` en Java
- Diseño modular para poder extender nuevos módulos (por ejemplo, notas clínicas o reportes)

## Configuración

La URL del gateway se toma del valor por defecto usado por `desktop-app` (`http://136.115.53.140:8080`). Puede cambiarse con la variable de entorno `HEARTGUARD_GATEWAY_URL` o enviándola al inicializar `ApiClient`.

```bash
set HEARTGUARD_GATEWAY_URL=http://localhost:8080
python -m heartguard_tk.app
```

## Estructura

```
heartguard_tk/
├── api/             # Cliente HTTP y manejo de errores
├── models/          # Dataclasses para respuestas de autenticación
└── ui/              # Vistas Tkinter (login, registro, dashboards)
```

## Roadmap sugerido

1. Implementar persistencia del token refresh/auto login.
2. Extender dashboard de usuarios con gestión de invitaciones.
3. Añadir tema oscuro utilizando `ttk.Style` o frameworks como `ttkbootstrap`.
4. Empaquetar con `pyinstaller` para distribución.
