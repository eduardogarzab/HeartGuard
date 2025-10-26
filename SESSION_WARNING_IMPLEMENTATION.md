# Implementación de Aviso de Expiración de Sesión

## Resumen

Se ha implementado un sistema de aviso de expiración de sesión que notifica al usuario 5 minutos antes de que su sesión expire automáticamente, permitiéndole extender la sesión con un clic.

## Cambios Realizados

### Backend

#### 1. Session Manager (`backend/internal/session/manager.go`)

-   Ya existían los métodos `Refresh()` y `RemainingTTL()` que permiten extender sesiones y obtener el tiempo restante
-   No se requirieron cambios adicionales

#### 2. Auth Handlers (`backend/internal/auth/handlers.go`)

-   **Agregado**: Método `RefreshSession()` que:
    -   Valida que el usuario tenga una sesión activa
    -   Extiende el TTL de la sesión en Redis
    -   Retorna el nuevo tiempo de expiración en JSON
    -   Endpoint: `POST /session/refresh`

#### 3. Router (`backend/internal/http/router.go`)

-   **Agregado**: Ruta `POST /session/refresh` con middleware de autenticación de superadmin

#### 4. Middleware Auth (`backend/internal/middleware/auth.go`)

-   **Agregado**: Constante `CtxSessionExpiresAtKey` para almacenar tiempo de expiración en contexto
-   **Modificado**: `SessionLoader()` ahora calcula y almacena el tiempo de expiración en el contexto
-   **Agregado**: Función `SessionExpiresAtFromContext()` para extraer tiempo de expiración del contexto

#### 5. UI Renderer (`backend/internal/ui/renderer.go`)

-   **Agregado**: Campo `SessionExpiresAt *time.Time` a la estructura `ViewData`

#### 6. Superadmin Handlers (`backend/internal/superadmin/handlers_ui.go`)

-   **Modificado**: Método `render()` ahora obtiene el tiempo de expiración del contexto y lo pasa al ViewData

### Frontend

#### 7. Layout Template (`backend/templates/layout.html`)

-   **Agregado**: Script inline que inyecta `window.sessionExpiresAt` con timestamp de expiración (en milisegundos)
-   **Agregado**: Modal HTML para mostrar la advertencia con:
    -   Título de advertencia
    -   Countdown en tiempo real
    -   Botón "Extender sesión"
    -   Botón "Cerrar sesión ahora"

#### 8. JavaScript (`backend/ui/assets/js/app.js`)

-   **Agregado**: Sistema de monitoreo de sesión con las siguientes funciones:
    -   `hgInitSessionMonitor()`: Inicializa el monitoreo cada 30 segundos
    -   `hgCheckSession()`: Verifica tiempo restante y muestra advertencia si es necesario
    -   `hgShowSessionWarning()`: Muestra modal con countdown y maneja interacciones
    -   Threshold de advertencia: 5 minutos antes de expiración
    -   Auto-redirección a login si la sesión expira
    -   Llamada AJAX a `/session/refresh` para extender sesión
    -   Feedback visual con mensaje flash de éxito

#### 9. CSS (`backend/ui/assets/css/app.css`)

-   **Agregado**: Estilos completos para el modal de advertencia:
    -   `.hg-modal`: Overlay con backdrop blur
    -   `.hg-modal-content`: Tarjeta del modal con animaciones
    -   `.hg-modal-header/body/footer`: Secciones del modal
    -   `.hg-btn`, `.hg-btn-primary`, `.hg-btn-secondary`: Botones estilizados
    -   Animaciones de entrada (fade-in y slide-up)
    -   Responsive design para móviles

## Flujo de Funcionamiento

1. **Al cargar la página**: El middleware `SessionLoader` calcula el tiempo de expiración y lo inyecta en el contexto
2. **Renderizado**: El handler `render()` pasa el tiempo de expiración al template
3. **Template**: El layout.html inyecta `window.sessionExpiresAt` en JavaScript
4. **Monitoreo**: JavaScript verifica cada 30 segundos el tiempo restante
5. **Advertencia**: Cuando quedan ≤5 minutos, se muestra el modal con countdown
6. **Extensión**: Si el usuario hace clic en "Extender sesión":
    - Se hace POST a `/session/refresh`
    - El backend extiende el TTL en Redis
    - Retorna nuevo tiempo de expiración
    - JavaScript actualiza `window.sessionExpiresAt`
    - Se cierra el modal y muestra mensaje de éxito
7. **Expiración**: Si el tiempo llega a 0, se redirige automáticamente a `/login`

## Características

-   ✅ **Proactivo**: Avisa con 5 minutos de anticipación
-   ✅ **No intrusivo**: Solo aparece cuando es necesario
-   ✅ **Countdown visual**: Muestra tiempo exacto restante
-   ✅ **Un clic para extender**: Experiencia fluida sin necesidad de recargar
-   ✅ **Fallback de seguridad**: Auto-logout si la sesión expira
-   ✅ **Feedback visual**: Mensaje flash de confirmación
-   ✅ **Responsive**: Funciona en móviles y escritorio
-   ✅ **Animaciones suaves**: UX pulida y profesional

## Configuración

El tiempo de expiración de sesión se configura mediante `AccessTokenTTL` en la configuración del sistema. El threshold de advertencia (5 minutos) está definido como constante `SESSION_WARNING_THRESHOLD_MS` en `app.js` y puede ajustarse según necesidades.

## Notas Técnicas

-   El middleware ya refrescaba automáticamente las sesiones en cada request, por lo que la navegación normal extiende la sesión
-   El nuevo endpoint `/session/refresh` permite extensión manual sin necesidad de navegación
-   El sistema es compatible con múltiples pestañas (cada una monitorea independientemente)
-   Los errores del linter en `layout.html` son falsos positivos (el linter intenta parsear templates Go como JavaScript)
