# Sistema de Alertas IA y Ground Truth - Desktop App

## 📋 Descripción

Este documento describe la implementación del flujo completo de **IA → Alertas → Ground Truth** en la aplicación de escritorio HeartGuard para usuarios no pacientes (caregivers, médicos, enfermeras).

## 🎯 Funcionalidades Implementadas

### 1. **Modelos de Datos** (`com.heartguard.desktop.models.alert`)

#### `Alert.java`
- Representa una alerta generada por IA o manualmente
- Contiene información completa: paciente, tipo, nivel, estado, ubicación GPS, timestamps
- Builder pattern para construcción flexible

#### `AlertType.java` (Enum)
- Tipos de alerta soportados:
  - `GENERAL_RISK` - Riesgo general de salud
  - `ARRHYTHMIA` - Arritmia cardíaca
  - `DESAT` - Desaturación de oxígeno
  - `HYPERTENSION` - Hipertensión
  - `HYPOTENSION` - Hipotensión
  - `FEVER` - Fiebre
  - `HYPOTHERMIA` - Hipotermia
- Cada tipo tiene emoji, color y descripción asociados

#### `AlertLevel.java` (Enum)
- Niveles de severidad:
  - `LOW` - Bajo (verde)
  - `MEDIUM` - Medio (amarillo)
  - `HIGH` - Alto (naranja)
  - `CRITICAL` - Crítico (rojo)

#### `AlertStatus.java` (Enum)
- Estados del ciclo de vida:
  - `CREATED` - Creada
  - `NOTIFIED` - Notificada
  - `ACKNOWLEDGED` - Reconocida
  - `RESOLVED` - Resuelta
  - `CLOSED` - Cerrada

#### `EventType.java` (Enum)
- Tipos de eventos médicos para Ground Truth
- Correspondencia 1:1 con AlertType pero para validación

#### `GroundTruthLabel.java`
- Etiqueta de validación de predicciones del modelo
- Registra si un evento fue real (True Positive) o falso (False Positive)
- Incluye notas clínicas, médico que validó, timestamps

#### `GroundTruthSource.java` (Enum)
- Origen de la etiqueta:
  - `AI_MODEL` - Validación de predicción de IA
  - `MANUAL` - Anotación manual
  - `MEDICAL_RECORD` - Extraído de historial médico

### 2. **Servicios de API**

#### `AlertService.java` (`com.heartguard.desktop.api`)

Métodos principales:
```java
// Obtener alertas de una organización
List<Alert> getOrganizationAlerts(String orgId);
List<Alert> getOrganizationAlerts(String orgId, List<AlertStatus> statuses, List<AlertLevel> levels);

// Obtener alertas de un paciente
List<Alert> getPatientAlerts(String patientId);
List<Alert> getPatientAlerts(String patientId, List<AlertStatus> statuses, List<AlertLevel> levels);

// Gestión de alertas
Alert acknowledgeAlert(String alertId, String userId);
Alert resolveAlert(String alertId, String userId, String notes);
Alert closeAlert(String alertId, String userId);
Alert getAlert(String alertId);
```

#### `GroundTruthService.java` (`com.heartguard.desktop.api`)

Métodos principales:
```java
// Validar como verdadero positivo (crea registro de ground truth)
GroundTruthLabel validateAsTruePositive(
    String alertId,
    String patientId,
    EventType eventType,
    Instant onset,
    Instant offsetAt,
    String annotatedByUserId,
    String note
);

// Marcar como falso positivo (no crea ground truth)
void validateAsFalsePositive(
    String alertId,
    String userId,
    String reason
);

// Crear ground truth manual (sin alerta asociada)
GroundTruthLabel createManualGroundTruth(
    String patientId,
    EventType eventType,
    Instant onset,
    Instant offsetAt,
    String annotatedByUserId,
    String note
);

// Obtener etiquetas de un paciente
List<GroundTruthLabel> getPatientGroundTruthLabels(String patientId);

// Obtener estadísticas de precisión del modelo
JsonObject getModelAccuracyStats(Instant startDate, Instant endDate);
```

### 3. **Interfaz de Usuario**

#### `AlertsPanel.java` (`com.heartguard.desktop.ui.user`)

Panel principal de alertas con:
- **Tabla de alertas** con información completa
- **Filtros**:
  - Por estado (Creada, Notificada, Reconocida, Resuelta)
  - Por nivel (Crítico, Alto, Medio, Bajo)
  - Búsqueda por nombre de paciente
- **Auto-refresh** cada 30 segundos
- **Acciones**:
  - Reconocer alerta
  - Validar alerta (abre diálogo de validación)
- **Estadísticas** de alertas activas
- **Color coding** según nivel de severidad

#### `AlertValidationDialog.java` (`com.heartguard.desktop.ui.user`)

Diálogo modal para validar alertas:
- **Información de la alerta**: paciente, tipo, nivel, descripción, GPS, timestamp
- **Opciones de validación**:
  - ✅ **Verdadero Positivo**: El evento es REAL
    - Crea registro de ground truth
    - Útil para medir precisión del modelo
  - ❌ **Falso Positivo**: La IA se equivocó
    - Marca la alerta como error
    - Ayuda a mejorar el modelo
- **Notas clínicas**: campo de texto para agregar observaciones
- **Explicación de Ground Truth**: panel informativo sobre su importancia
- **Acciones**:
  - Validar y resolver (marca alerta como resuelta)
  - Cancelar

### 4. **Integración en Dashboard**

El panel de alertas se agregó como **tercera pestaña** en `MainDashboardPanel`:

```
┌─────────────────────────────────────────────────────────┐
│  👤 Mis Pacientes  │  🏥 Organizaciones  │  🚨 Alertas IA │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Cómo Usar

### Para Caregivers/Médicos

1. **Ver Alertas**
   - Iniciar sesión en la aplicación desktop
   - Ir a la pestaña "🚨 Alertas IA"
   - Ver lista de alertas activas de todos los pacientes de la organización

2. **Filtrar Alertas**
   - Usar filtro de estado para ver solo alertas nuevas o reconocidas
   - Usar filtro de nivel para ver solo alertas críticas/altas
   - Buscar por nombre de paciente

3. **Reconocer Alerta**
   - Seleccionar una alerta
   - Click en "✓ Reconocer Seleccionadas"
   - La alerta cambia a estado "Reconocida"

4. **Validar Alerta (Ground Truth)**
   - Click en botón "Validar" de la alerta
   - Se abre diálogo de validación
   - Seleccionar:
     - **Verdadero Positivo**: Si el evento fue real
       - Agregar notas clínicas (opcional)
       - El sistema crea registro de ground truth
     - **Falso Positivo**: Si la IA se equivocó
       - Agregar razón (opcional)
       - El sistema marca la alerta como error
   - Click en "✓ Validar y Resolver"
   - La alerta se marca como resuelta automáticamente

5. **Auto-Refresh**
   - El panel se actualiza automáticamente cada 30 segundos
   - También puede hacer click en "🔄 Actualizar" manualmente

## 📊 Flujo Completo del Sistema

```
1. DATOS EN INFLUXDB
   ↓
2. SERVICIO DE IA analiza y detecta problema
   ↓
3. BACKEND crea ALERTA en PostgreSQL
   ↓
4. DESKTOP APP muestra alerta en tabla
   ↓
5. CAREGIVER valida la alerta
   ↓
6. GROUND TRUTH LABEL se crea en PostgreSQL
   ↓
7. ESTADÍSTICAS de precisión del modelo
```

## 🔧 Configuración Requerida

### Backend (debe implementar endpoints):

```
GET  /admin/organizations/{org_id}/alerts
GET  /patient/{patient_id}/alerts
GET  /alerts/{alert_id}
PUT  /alerts/{alert_id}/acknowledge
PUT  /alerts/{alert_id}/resolve
PUT  /alerts/{alert_id}/close

POST /ground-truth/validate-true-positive
POST /ground-truth/validate-false-positive
POST /ground-truth/create-manual
GET  /ground-truth/patient/{patient_id}
GET  /ground-truth/stats
```

### Base de Datos (PostgreSQL):

Tablas requeridas:
- `alerts`
- `alert_types`
- `alert_levels`
- `alert_status`
- `event_types`
- `ground_truth_labels`

Ver `db/seed.sql` para estructura completa.

## 📝 Ejemplo de Uso en Código

```java
// Crear servicio de alertas
AlertService alertService = new AlertService(gatewayUrl);
alertService.setAccessToken(accessToken);

// Obtener alertas activas
List<AlertStatus> activeStatuses = List.of(
    AlertStatus.CREATED, 
    AlertStatus.NOTIFIED, 
    AlertStatus.ACKNOWLEDGED
);
List<Alert> alerts = alertService.getOrganizationAlerts(orgId, activeStatuses, null);

// Reconocer una alerta
Alert updatedAlert = alertService.acknowledgeAlert(alertId, userId);

// Validar como verdadero positivo
GroundTruthService gtService = new GroundTruthService(gatewayUrl);
gtService.setAccessToken(accessToken);

GroundTruthLabel label = gtService.validateAsTruePositive(
    alertId,
    patientId,
    EventType.ARRHYTHMIA,
    Instant.now(),
    null,
    userId,
    "Arritmia confirmada mediante ECG de 12 derivaciones"
);

// Resolver la alerta
alertService.resolveAlert(alertId, userId, "Paciente estabilizado");
```

## 🎨 Características de UI

- **Diseño profesional** con paleta médica
- **Color coding** por nivel de severidad
- **Emojis** para tipos de alerta (💓 arritmia, 🫁 desaturación, etc.)
- **Tabla responsiva** con ordenamiento
- **Filtros en tiempo real**
- **Auto-refresh** configurable
- **Tooltips** informativos
- **Diálogos modales** con información completa

## 🔐 Seguridad

- Todas las peticiones requieren **JWT token** válido
- Validación de permisos en backend
- Solo caregivers de la organización pueden ver sus alertas
- Auditoría completa: quién validó qué y cuándo

## 📈 Métricas y Estadísticas

Con los datos de ground truth el sistema puede:
- Calcular **precisión del modelo** (% de true positives)
- Identificar **tipos de alerta con más falsos positivos**
- Generar **reportes de calidad** del servicio de IA
- **Reentrenar modelos** con datos validados

## 🚧 Próximos Pasos (Pendientes en Backend)

1. Implementar endpoints REST mencionados
2. Crear job que lea InfluxDB y llame al modelo de IA
3. Crear sistema de notificaciones (email, SMS, push)
4. Implementar estadísticas y dashboard de métricas
5. Agregar exportación de reportes

---

**Autor**: GitHub Copilot  
**Fecha**: 2025-11-24  
**Versión**: 1.0
