# HeartGuard Desktop (Tkinter)

Nueva implementación del cliente de escritorio de HeartGuard utilizando Python y Tkinter. La aplicación replica los flujos del cliente JavaFX original y se comunica con el gateway Flask existente para interactuar con los microservicios de autenticación, usuarios y pacientes.

## Estructura de carpetas

```
clients/desktop-tk/
├── api/              # Cliente REST contra el gateway
├── controllers/      # Coordinadores de lógica de negocio por módulo
├── ui/               # Vistas Tkinter (ventanas, frames, diálogos)
├── utils/            # Helpers compartidos (configuración, logging, tokens)
├── main.py           # Punto de entrada de la aplicación
└── requirements.txt  # Dependencias necesarias
```

## Requisitos

* Python 3.10+
* Dependencias Python listadas en `requirements.txt`
* Gateway Flask ejecutándose (por defecto en `http://127.0.0.1:8080`)

Instala las dependencias con:

```bash
python -m venv .venv
source .venv/bin/activate  # o .venv\\Scripts\\activate en Windows
pip install -r requirements.txt
```

## Ejecución

```bash
python clients/desktop-tk/main.py
```

La aplicación detecta tokens almacenados en `~/.heartguard/session.dat`, cifrados con Fernet. Los tokens se refrescan automáticamente mediante `/auth/refresh` y se validan con `/auth/verify` al iniciar.

## Características principales

* Login y registro para usuarios (staff) y pacientes.
* Persistencia cifrada de tokens de acceso y refresco.
* Dashboard organizacional con métricas y gráficas embebidas (Matplotlib).
* Gestión de pacientes, alertas, dispositivos e invitaciones para personal médico.
* Vistas dedicadas para pacientes: perfil, alertas, dispositivos, equipo de cuidado, lecturas y ubicaciones.
* Mapa interactivo de ubicaciones utilizando Folium + tkhtmlview.
* Interfaz coherente con la identidad visual de HeartGuard: barra superior, barra lateral, panel con scroll y estilos médicos.
