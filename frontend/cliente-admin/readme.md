# 🚀 Guía de uso – HeartGuard Cliente Web (Demo)

Este documento describe cómo levantar y probar el **cliente web** de HeartGuard en su versión **demo**.  
El cliente corresponde al **panel del administrador de familia**, donde se visualizan métricas, alertas y ubicación de los miembros.

---

## 📂 Estructura del cliente

```
cliente-admin/
├─ login.html
├─ dashboard.html
└─ assets/
   ├─ js/
      ├─ styles.css
      ├─ utils.js
      ├─ auth.js
      ├─ login.js
      ├─ api.js
      ├─ charts.js
      ├─ map.js
      ├─ notifications.js
      └─ dashboard.js
   ├─ styles.css
```

---

## ▶️ Cómo levantar el cliente en modo demo

1. Abrir una terminal en la carpeta y ejecutar un servidor estático simple, por ejemplo con Python:

    ```bash
    cd frontend/cliente-admin
    python -m http.server 8082
    ```

2. Abrir en el navegador:

    - [http://localhost:8082/login.html](http://localhost:8082/login.html)

3. **Iniciar sesión** con las credenciales de prueba:

    - Usuario: `maria_admin`
    - Contraseña: `admin123`

4. Serás redirigido al **dashboard** de demo, donde podrás visualizar:
    - Número de miembros, alertas activas y críticas.
    - Lista de miembros de la familia (mock “Familia Garza”).
    - Gráfica de métricas diarias (HR, presión arterial, SpO₂).
    - Gráfica de actividad (reposo, caminar, activo).
    - Alertas recientes con detalle y ubicación en el mapa.

---

## ⚠️ Limitaciones de la demo actual

-   Los datos son **mock estáticos**, no provienen de sensores ni bases de datos reales.
-   La autenticación es **ficticia**: se guarda un token en `localStorage`, pero no se valida contra un backend.
-   El refresco de datos es simulado cada 20 segundos, no hay conexión con un sistema en tiempo real.
-   Las gráficas muestran tendencias generadas de manera aleatoria para efectos visuales.
-   No es posible agregar/eliminar miembros de forma persistente; los botones son placeholders de UI.

---

## 🔮 Actualizaciones y mejoras futuras

-   **Conexión con el backend Go + microservicios** para datos reales (InfluxDB para series de tiempo, Redis para alertas).
-   **Autenticación JWT real** contra el servicio de login, con validación de roles y permisos.
-   **Integración en tiempo real** mediante WebSockets o SSE, evitando el polling.
-   **Gestión completa de miembros**: altas, bajas y edición persistente.
-   **Series históricas completas** para cada miembro (no solo las últimas 12 horas).
-   **Alertas accionables**: posibilidad de marcar como resueltas y generar reportes.
-   **Optimización para móviles** con mejoras de usabilidad en pantallas pequeñas.

---

## ✅ Conclusión

El cliente actual cumple como **prototipo funcional** de la interfaz web, permitiendo demostrar la visión del proyecto:  
un panel domiciliario para administradores familiares que facilite la **prevención y reacción temprana** ante emergencias cardiovasculares.  
Las próximas iteraciones conectarán el demo con datos reales y funcionalidades completas.
