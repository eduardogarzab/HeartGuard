# Guía de Compilación y Ejecución - Sistema de Alertas IA

## 🚀 Inicio Rápido

### Requisitos Previos

- ✅ Java 17 o superior
- ✅ Maven 3.6+
- ✅ Backend HeartGuard corriendo (con endpoints de alertas implementados)
- ✅ PostgreSQL con tablas de alertas y ground truth

### Compilar

```powershell
cd desktop-app
mvn clean package
```

### Ejecutar

```powershell
java -jar target\desktop-app-1.0-SNAPSHOT.jar
```

## 📝 Pasos Detallados

### 1. Verificar Dependencias

El proyecto ya incluye todas las dependencias necesarias en `pom.xml`:

```xml
<!-- OkHttp para HTTP client -->
<dependency>
    <groupId>com.squareup.okhttp3</groupId>
    <artifactId>okhttp</artifactId>
    <version>4.12.0</version>
</dependency>

<!-- Gson para JSON -->
<dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
    <version>2.10.1</version>
</dependency>

<!-- FlatLaf para UI moderna -->
<dependency>
    <groupId>com.formdev</groupId>
    <artifactId>flatlaf</artifactId>
    <version>3.2.5</version>
</dependency>
```

### 2. Configurar URL del Gateway

Editar `desktop-app/src/main/java/com/heartguard/desktop/config/AppConfig.java`:

```java
private static final String DEFAULT_GATEWAY_URL = "http://localhost:8080";
// O la URL de tu servidor
// private static final String DEFAULT_GATEWAY_URL = "http://134.199.204.58:8080";
```

### 3. Compilar con Maven

```powershell
# Limpiar builds anteriores
mvn clean

# Compilar y empaquetar
mvn package

# Si quieres saltar los tests (opcional)
mvn package -DskipTests
```

**Salida esperada:**
```
[INFO] ------------------------------------------------------------------------
[INFO] BUILD SUCCESS
[INFO] ------------------------------------------------------------------------
[INFO] Total time:  15.432 s
[INFO] Finished at: 2025-11-24T10:30:00-06:00
[INFO] ------------------------------------------------------------------------
```

### 4. Ejecutar la Aplicación

```powershell
# Desde desktop-app/
java -jar target\desktop-app-1.0-SNAPSHOT.jar
```

O usando el script de lanzamiento:

```powershell
.\launch.sh  # En Linux/Mac
# o
.\launch.bat # En Windows (si existe)
```

## 🧪 Testing Manual

### Escenario 1: Ver Alertas

1. **Login como caregiver/médico**
   - Email: `doctor@hospital.com`
   - Password: `password123`

2. **Navegar a pestaña "🚨 Alertas IA"**

3. **Verificar que se muestran alertas**
   - Si no hay alertas, verificar que el backend esté respondiendo correctamente

### Escenario 2: Filtrar Alertas

1. **Usar filtro de estado**
   - Seleccionar "Creada" o "Notificada"
   - Verificar que solo se muestran alertas con ese estado

2. **Usar filtro de nivel**
   - Seleccionar "Crítico" o "Alto"
   - Verificar que solo se muestran alertas de alta prioridad

3. **Buscar por paciente**
   - Escribir parte del nombre del paciente
   - Verificar que se filtran los resultados

### Escenario 3: Reconocer Alerta

1. **Seleccionar una alerta de la tabla**

2. **Click en "✓ Reconocer Seleccionadas"**

3. **Confirmar en el diálogo**

4. **Verificar que la alerta cambia de estado a "Reconocida"**

### Escenario 4: Validar Alerta (Ground Truth)

1. **Click en botón "Validar" de una alerta**

2. **Revisar información de la alerta**

3. **Seleccionar validación**:
   - ✅ Verdadero Positivo: Si el evento fue real
   - ❌ Falso Positivo: Si la IA se equivocó

4. **Agregar notas clínicas** (opcional)

5. **Click en "✓ Validar y Resolver"**

6. **Verificar que:**
   - Alerta se marca como resuelta
   - Se crea registro de ground truth
   - Alerta desaparece de la lista de activas

### Escenario 5: Auto-Refresh

1. **Esperar 30 segundos**

2. **Verificar que la tabla se actualiza automáticamente**

3. **Click en "🔄 Actualizar" para actualizar manualmente**

## 🐛 Troubleshooting

### Error: "Cannot connect to backend"

**Síntomas:**
```
Error al cargar alertas: Connection refused
```

**Solución:**
1. Verificar que el backend esté corriendo:
   ```powershell
   curl http://localhost:8080/health
   ```

2. Verificar la URL en `AppConfig.java`

3. Verificar que no haya firewall bloqueando

### Error: "Unauthorized (401)"

**Síntomas:**
```
Error 401: Unauthorized - Token inválido o expirado
```

**Solución:**
1. Hacer logout y login nuevamente
2. Verificar que el token JWT esté siendo enviado correctamente
3. Verificar que el backend acepte el token

### Error: "No alerts found"

**Síntomas:**
- La tabla de alertas está vacía
- Mensaje: "0 alertas activas"

**Solución:**
1. Verificar que hay alertas en la base de datos:
   ```sql
   SELECT * FROM alerts WHERE status_id IN (
     SELECT id FROM alert_status WHERE code IN ('created', 'notified', 'ack')
   );
   ```

2. Verificar que el endpoint del backend esté implementado:
   ```powershell
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/admin/organizations/YOUR_ORG_ID/alerts
   ```

3. Verificar que el usuario tenga membresía en la organización

### Error: "Compilation failed"

**Síntomas:**
```
[ERROR] Failed to execute goal ... compilation failure
```

**Solución:**
1. Verificar versión de Java:
   ```powershell
   java -version
   # Debe ser 17 o superior
   ```

2. Limpiar caché de Maven:
   ```powershell
   mvn clean
   mvn dependency:purge-local-repository
   mvn package
   ```

3. Verificar que no haya errores de sintaxis en archivos Java

## 📊 Logs y Debugging

### Habilitar logs detallados

Agregar al inicio del método `main()` en `Main.java`:

```java
System.setProperty("org.slf4j.simpleLogger.defaultLogLevel", "debug");
```

### Ver requests HTTP

En `AlertService.java`, agregar logging:

```java
import java.util.logging.Logger;

private static final Logger LOGGER = Logger.getLogger(AlertService.class.getName());

// En cada método
LOGGER.info("Llamando a: " + url);
```

### Monitorear auto-refresh

En `AlertsPanel.java`, descomentar:

```java
private void loadAlerts() {
    System.out.println("[AlertsPanel] Cargando alertas... " + new Date());
    // ... resto del código
}
```

## 🔧 Configuración Avanzada

### Cambiar intervalo de auto-refresh

En `AlertsPanel.java`, modificar:

```java
// Cambiar de 30 segundos (30000 ms) a otro valor
autoRefreshTimer = new Timer(60000, e -> loadAlerts()); // 1 minuto
```

### Cambiar tamaño de ventana

En `UserDashboardFrame.java`:

```java
// Cambiar de 0.9, 0.9 a otros valores
Dimension windowSize = ResponsiveUtils.getResponsiveSize(0.8, 0.85, 1200, 800);
```

### Cambiar límite de alertas

Actualmente no hay límite. Para agregar paginación, modificar `AlertService.java`:

```java
public List<Alert> getOrganizationAlerts(String orgId, int page, int pageSize) {
    String url = gatewayUrl + "/admin/organizations/" + orgId 
                + "/alerts?page=" + page + "&page_size=" + pageSize;
    // ... resto del código
}
```

## 📦 Crear Ejecutable Standalone

### Opción 1: JAR con dependencias (recomendado)

Agregar plugin en `pom.xml`:

```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-shade-plugin</artifactId>
    <version>3.5.0</version>
    <executions>
        <execution>
            <phase>package</phase>
            <goals>
                <goal>shade</goal>
            </goals>
            <configuration>
                <transformers>
                    <transformer implementation="org.apache.maven.plugins.shade.resource.ManifestResourceTransformer">
                        <mainClass>com.heartguard.desktop.Main</mainClass>
                    </transformer>
                </transformers>
            </configuration>
        </execution>
    </executions>
</plugin>
```

Compilar:
```powershell
mvn clean package
```

Ejecutar:
```powershell
java -jar target\desktop-app-1.0-SNAPSHOT.jar
```

### Opción 2: Instalador nativo con jpackage

```powershell
# Windows
jpackage --input target --name HeartGuard `
  --main-jar desktop-app-1.0-SNAPSHOT.jar `
  --main-class com.heartguard.desktop.Main `
  --type msi --win-menu --win-shortcut

# macOS
jpackage --input target --name HeartGuard `
  --main-jar desktop-app-1.0-SNAPSHOT.jar `
  --main-class com.heartguard.desktop.Main `
  --type dmg

# Linux
jpackage --input target --name HeartGuard `
  --main-jar desktop-app-1.0-SNAPSHOT.jar `
  --main-class com.heartguard.desktop.Main `
  --type deb
```

## 📚 Recursos Adicionales

- [README_ALERTAS_IA.md](README_ALERTAS_IA.md) - Guía de uso completa
- [IMPLEMENTACION_RESUMEN.md](IMPLEMENTACION_RESUMEN.md) - Resumen de archivos creados
- [BACKEND_API_EXAMPLES.md](BACKEND_API_EXAMPLES.md) - Ejemplos de respuestas del backend
- [FLUJO_IA_ALERTAS_GROUND_TRUTH.md](../FLUJO_IA_ALERTAS_GROUND_TRUTH.md) - Flujo completo del sistema

---

**¿Problemas?** Verifica:
1. ✅ Java 17+ instalado
2. ✅ Backend corriendo
3. ✅ PostgreSQL con datos de prueba
4. ✅ Credenciales de usuario válidas
5. ✅ Red/firewall permitiendo conexión
