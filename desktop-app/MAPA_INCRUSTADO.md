# Mapa Incrustado en UserDashboard

## Descripción de los Cambios

Se ha implementado un **mapa interactivo incrustado** directamente en el UserDashboard de la aplicación desktop usando **JxBrowser**, reemplazando el botón "Ver Mapa" que abría el mapa en un navegador externo.

### Ventajas del Nuevo Enfoque con JxBrowser

1. **Chromium Completo**: JxBrowser incrusta un motor Chromium completo, proporcionando el mejor rendimiento y compatibilidad web disponible.

2. **Mejor Experiencia de Usuario**: El mapa se muestra directamente dentro de la aplicación, sin necesidad de abrir un navegador externo.

3. **Hardware Acceleration**: Aprovecha la aceleración por hardware (GPU) para renderizado ultra-rápido del mapa.

4. **Máxima Compatibilidad**: Compatible con todas las tecnologías web modernas (HTML5, CSS3, JavaScript ES6+, WebGL, etc.).

5. **Interfaz Profesional**: La aplicación se siente más integrada y profesional al mantener toda la funcionalidad dentro de una sola ventana.

6. **Actualización en Tiempo Real**: El mapa puede actualizarse dinámicamente mediante JavaScript sin necesidad de recargar toda la página.

## Cambios Técnicos Realizados

### Archivos Nuevos

- **`EmbeddedMapPanel.java`**: Panel personalizado que usa JxBrowser para mostrar el mapa interactivo con Leaflet y Leaflet.markercluster.

### Archivos Modificados

- **`UserDashboardPanel.java`**: 
  - Se reemplazó el componente de mapa antiguo por `EmbeddedMapPanel`
  - Se eliminó el botón "Ver Mapa" y su funcionalidad asociada
  - El mapa ahora se muestra directamente en el dashboard con una altura de 500px
  - Se agregó método `cleanup()` para liberar recursos del navegador

- **`Main.java`**:
  - Se eliminó toda la inicialización de JavaFX (ya no se necesita)
  - Se simplificó el código de arranque de la aplicación

- **`pom.xml`**:
  - Se eliminaron dependencias de JavaFX
  - Se agregaron dependencias de JxBrowser

### Archivos Eliminados

- **`UserMapPanel.java`**: Panel antiguo que ya no se usa

### Dependencias Requeridas

#### JxBrowser (Requiere Licencia Comercial)

```xml
<!-- Repositorio de JxBrowser -->
<repositories>
    <repository>
        <id>com.teamdev</id>
        <url>https://europe-maven.pkg.dev/jxbrowser/releases</url>
    </repository>
</repositories>

<!-- Dependencias de JxBrowser -->
<dependency>
    <groupId>com.teamdev.jxbrowser</groupId>
    <artifactId>jxbrowser</artifactId>
    <version>7.39.2</version>
</dependency>

<dependency>
    <groupId>com.teamdev.jxbrowser</groupId>
    <artifactId>jxbrowser-swing</artifactId>
    <version>7.39.2</version>
</dependency>

<!-- Binarios específicos por plataforma -->
<dependency>
    <groupId>com.teamdev.jxbrowser</groupId>
    <artifactId>jxbrowser-win64</artifactId>
    <version>7.39.2</version>
</dependency>
```

**⚠️ IMPORTANTE SOBRE LICENCIA:**
- JxBrowser es una biblioteca comercial que requiere licencia para uso en producción
- Ofrece una evaluación gratuita de 30 días con marca de agua
- Para uso comercial, se debe adquirir una licencia en: https://www.teamdev.com/jxbrowser#pricing
- Alternativas gratuitas: JavaFX WebView (menos potente) o CEF (Java Chromium Embedded Framework)

## Características del Mapa Incrustado

### Visualización

- **Clusters inteligentes**: Los marcadores se agrupan automáticamente cuando hay muchos en una misma área
- **Colores por riesgo**: Los pacientes se muestran con colores según su nivel de riesgo (verde=bajo, amarillo=medio, rojo=alto)
- **Diferenciación visual**: Pacientes con marcadores circulares, miembros del equipo con marcadores cuadrados
- **Panel informativo**: Badge flotante que muestra el conteo de pacientes y miembros

### Interactividad

- **Popups detallados**: Al hacer clic en un marcador, se muestra información detallada incluyendo:
  - Nombre
  - Organización
  - Equipo de cuidado
  - Nivel de riesgo (para pacientes)
  - Rol (para miembros del equipo)
  - Alertas activas (si las hay)

- **Zoom y navegación**: Control completo de zoom y desplazamiento
- **Auto-ajuste**: El mapa se ajusta automáticamente para mostrar todos los marcadores visibles
- **Animaciones suaves**: Transiciones animadas al actualizar las ubicaciones
- **Aceleración por hardware**: Renderizado ultra-rápido con GPU

### Filtrado

- **Por equipo**: El mapa respeta el filtro de equipo seleccionado en el toolbar
- **Actualización dinámica**: Los datos se actualizan sin recargar todo el HTML, mediante JavaScript

## Uso

El mapa se carga automáticamente cuando se selecciona una organización en el dashboard. Los controles disponibles son:

1. **Selector de equipo**: Filtra las ubicaciones por equipo de cuidado
2. **Botón actualizar (↻)**: Recarga las ubicaciones desde el servidor
3. **Status label**: Muestra el estado de la última actualización

## Tecnologías Utilizadas

- **JxBrowser 7.39.2**: Motor Chromium embebido para máximo rendimiento
- **Leaflet.js 1.9.4**: Librería de mapas interactivos
- **Leaflet.markercluster 1.5.3**: Para agrupación inteligente de marcadores
- **OpenStreetMap**: Proveedor de tiles del mapa

## Notas de Implementación

- El mapa usa una posición inicial en Monterrey (25.6866, -100.3161) con zoom 10
- La altura del mapa es de 500px para dar suficiente espacio de visualización
- El HTML se genera dinámicamente en Java y se carga usando `data:` URL
- La actualización de datos se hace mediante ejecución de JavaScript en el navegador
- Si falla la actualización por JavaScript, se recarga completamente el HTML
- JxBrowser usa renderizado con aceleración por hardware (HARDWARE_ACCELERATED)
- El engine y browser se limpian apropiadamente con el método `dispose()`

## Consideraciones de Rendimiento

- El mapa carga los recursos de CDN (Leaflet) solo una vez
- Los clusters reducen la cantidad de marcadores renderizados en cada zoom
- La actualización incremental por JavaScript es más eficiente que recargar el HTML completo
- Hardware acceleration proporciona renderizado 60 FPS del mapa
- Chromium completo asegura compatibilidad total con JavaScript moderno

## Limpieza de Recursos

Es importante llamar al método `cleanup()` del panel cuando se cierre para liberar recursos:

```java
@Override
public void dispose() {
    dashboardPanel.cleanup(); // Limpia JxBrowser
    super.dispose();
}
```

## Futuras Mejoras Posibles

- [ ] Agregar controles para alternar entre capas de mapa (satélite, terreno, etc.)
- [ ] Implementar búsqueda de ubicaciones específicas
- [ ] Agregar rutas entre ubicaciones
- [ ] Mostrar historial de movimientos
- [ ] Implementar modo de pantalla completa para el mapa
- [ ] Agregar exportación de screenshot del mapa
- [ ] Implementar tracking en tiempo real con WebSockets
