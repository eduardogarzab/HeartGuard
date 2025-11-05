# HeartGuard Org Admin Client

Panel administrativo para usuarios con rol `org_admin`. Es una aplicacion estatica (HTML, CSS, JavaScript) que consume exclusivamente los microservicios de **Auth** y **Admin** a traves del Gateway.

## Caracteristicas principales

- Autenticacion contra `/auth/login/user` (Auth Service).
- Validacion de sesion con `/auth/me`.
- Consumo de los endpoints XML del Admin Service a traves del gateway (`/admin/...`).
- Dashboard con:
   - Listado de organizaciones asignadas.
   - Resumen general de la organizacion seleccionada (estadisticas, riesgos, dispositivos, alertas).
   - Pestanas para staff, pacientes, equipos, cuidadores y alertas.
- Manejo de tokens en `sessionStorage` y restauracion de sesion.
- Manejo de errores y notificaciones visuales.

## Estructura

```
clients/org-admin/
├── index.html
├── README.md
└── assets/
    ├── css/
    │   └── app.css
    └── js/
        ├── app.js
        ├── api.js
        ├── config.js
        └── xml.js
```

## Configuracion

El archivo `assets/js/config.js` define los parametros principales:

```js
window.ORG_ADMIN_CONFIG = {
  gatewayBaseUrl: "http://localhost:8080",
  authLoginPath: "/auth/login/user",
  authMePath: "/auth/me",
  adminBasePath: "/admin",
  requestTimeoutMs: 15000
};
```

Puedes sobrescribirlos antes de cargar `config.js` estableciendo `window.ORG_ADMIN_CONFIG` en el HTML o inyectandolo desde el servidor.

## Requisitos

- Servicios Auth, Admin y Gateway corriendo (recomendado: `cd services && make start`).
- Navegador moderno con soporte para ES2020.

## Como levantar el cliente

1. Inicia los servicios necesarios:
   ```bash
   cd services
   make start
   ```
2. Sirve la carpeta estatica. Ejemplo con Python:
   ```bash
   cd clients/org-admin
   python -m http.server 8085
   ```
3. Abre `http://localhost:8085` en el navegador.

> **Nota:** si sirves el HTML desde un puerto distinto a 8080, asegurate de que el gateway permita CORS o usa una herramienta como `devserver`/`http-serve` con proxy. Para desarrollo rapido se puede abrir el `index.html` directamente en el navegador si este soporta fetch a `http://localhost:8080` (algunas configuraciones bloquean CORS al abrir archivos locales).

## Flujo de autenticacion

1. Login -> `POST /auth/login/user`.
2. Guardar `access_token` en `sessionStorage`.
3. Validar sesion -> `GET /auth/me`.
4. Listar organizaciones -> `GET /admin/organizations/` (XML).
5. Al seleccionar una organizacion se consultan:
   - `GET /admin/organizations/{org_id}`
   - `GET /admin/organizations/{org_id}/dashboard`
   - Y las pestanas bajo `/staff/`, `/patients/`, `/care-teams/`, `/caregivers/assignments`, `/alerts/`.

## Proximos pasos sugeridos

- Anadir formularios para crear pacientes, invitar staff o asignar cuidadores.
- Guardar y renovar refresh tokens cuando Auth Service lo exponga publicamente.
- Integrar graficas (ej. Chart.js) para las metricas de riesgo y alertas.
- Internacionalizacion y modo oscuro siguiendo la linea visual del backend superadmin.

## Soporte

Ante dudas sobre los endpoints revisa `services/admin/README.md`. Para reportar problemas contacta al equipo de plataforma HeartGuard.
