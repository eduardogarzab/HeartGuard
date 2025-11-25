# Mejoras en Visualización de Alertas para Pacientes

## 📋 Resumen

Se han implementado mejoras significativas en la **Desktop App** para que los **pacientes** puedan visualizar:

1. **Indicadores de que las alertas fueron generadas por IA**
2. **Probabilidad de predicción del modelo de IA**
3. **Estado de validación médica (Ground Truth)**
4. **Información del médico que validó la alerta**
5. **Notas clínicas de la validación**

---

## 🎯 Cambios Implementados

### 1. Frontend - Desktop App (Java Swing)

#### **Archivo**: `PatientDashboardPanel.java`

##### ✨ **Nuevas Funcionalidades**

1. **Chip de IA en alertas**
   - Muestra un badge "🤖 IA" cuando la alerta fue generada por el modelo
   - Color morado distintivo (`#673AB7`)
   - Tooltip: "Alerta generada por modelo de Inteligencia Artificial"

2. **Panel de información de IA** (`createAIInfoPanel`)
   - **Probabilidad de IA**: Extrae y muestra la probabilidad de la predicción
   - **Nombre del modelo**: Muestra "RandomForest" cuando está disponible
   - **Colores según probabilidad**:
     - 🔴 Rojo (≥80%): Alta probabilidad de problema
     - 🟠 Naranja (≥60%): Media-alta probabilidad
     - 🟡 Amarillo (≥40%): Media probabilidad
     - 🟢 Verde (<40%): Baja probabilidad

3. **Estado de validación médica**
   - ✅ **Validado**: Muestra "Validado por médico" con nombre del doctor y notas clínicas
   - ⏳ **Pendiente**: Muestra "Pendiente de validación médica" si aún no ha sido revisado
   - Formato visual distintivo con separador y colores específicos

##### 📝 **Métodos Nuevos**

```java
// Crea panel con información de IA y validación médica
private JPanel createAIInfoPanel(JsonObject alert)

// Extrae probabilidad de la descripción
private Double extractProbabilityFromDescription(String description)

// Obtiene color según probabilidad
private Color getProbabilityColor(double probability)
```

##### 🎨 **Ejemplo Visual**

```
┌─────────────────────────────────────────────────────┐
│ ARRHYTHMIA · Alto                                   │
│ Frecuencia cardíaca anormal detectada              │
│ 25 Nov 2025, 14:30  [NUEVA]  [🤖 IA]              │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Probabilidad de IA: 87.3%                       │ │
│ │ Modelo: RandomForest                            │ │
│ │ ─────────────────────────────────────────────── │ │
│ │ ✅ Validado por médico (Dr. García)             │ │
│ │ Nota: Confirmo arritmia, paciente bajo         │ │
│ │       tratamiento                               │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

### 2. Backend - Patient Service (Python/Flask)

#### **Archivo**: `services/patient/src/patient/repositories/patient_repo.py`

##### ✨ **Cambios en Queries SQL**

**Método**: `get_recent_alerts()`

```sql
SELECT 
    a.id,
    at.code as type,
    al.code as level,
    a.description,
    a.created_at,
    ast.code as status,
    ST_Y(a.location) as latitude,
    ST_X(a.location) as longitude,
    -- ✨ NUEVO: Información de IA
    a.created_by_model_id,
    m.name as model_name,
    a.source_inference_id,
    -- ✨ NUEVO: Información de Ground Truth
    gt.id as ground_truth_id,
    gt.event_type_id as ground_truth_event_type,
    et.code as ground_truth_event_code,
    et.label as ground_truth_event_label,
    gt.annotated_by_user_id as ground_truth_doctor_id,
    u.name as ground_truth_doctor,
    gt.note as ground_truth_note,
    gt.created_at as ground_truth_created_at
FROM alerts a
LEFT JOIN alert_types at ON a.type_id = at.id
LEFT JOIN alert_levels al ON a.alert_level_id = al.id
LEFT JOIN alert_status ast ON a.status_id = ast.id
LEFT JOIN models m ON a.created_by_model_id = m.id
-- ✨ NUEVO: Join con ground truth
LEFT JOIN ground_truth_labels gt ON (
    gt.patient_id = a.patient_id 
    AND gt.onset >= (a.created_at - INTERVAL '10 minutes')
    AND gt.onset <= (a.created_at + INTERVAL '10 minutes')
)
LEFT JOIN event_types et ON gt.event_type_id = et.id
LEFT JOIN users u ON gt.annotated_by_user_id = u.id
WHERE a.patient_id = %s
ORDER BY a.created_at DESC
LIMIT %s
```

**Método**: `get_alerts()` - Aplicados los mismos cambios para paginación

---

#### **Archivo**: `services/patient/src/patient/services/patient_service.py`

##### ✨ **Cambios en `_format_alert()`**

```python
def _format_alert(self, alert: Dict) -> Dict:
    """
    Formatea una alerta para respuesta
    Incluye información de IA y ground truth
    """
    formatted = {
        'id': str(alert['id']),
        'type': alert['type'],
        'level': alert['level'],
        'level_label': self._format_alert_level(alert['level']),
        'description': alert['description'],
        'status': alert['status'],
        'status_label': self._format_alert_status(alert['status']),
        'created_at': alert['created_at'].isoformat() if alert['created_at'] else None,
        'location': {...},
        # ✨ NUEVO: Información de IA
        'created_by_model_id': str(alert['created_by_model_id']) if alert.get('created_by_model_id') else None,
        'model_name': alert.get('model_name'),
        'source_inference_id': str(alert['source_inference_id']) if alert.get('source_inference_id') else None,
    }
    
    # ✨ NUEVO: Información de Ground Truth
    if alert.get('ground_truth_id'):
        formatted['ground_truth_validated'] = True
        formatted['ground_truth_id'] = str(alert['ground_truth_id'])
        formatted['ground_truth_event_code'] = alert.get('ground_truth_event_code')
        formatted['ground_truth_event_label'] = alert.get('ground_truth_event_label')
        formatted['ground_truth_doctor'] = alert.get('ground_truth_doctor')
        formatted['ground_truth_doctor_id'] = str(alert['ground_truth_doctor_id']) if alert.get('ground_truth_doctor_id') else None
        formatted['ground_truth_note'] = alert.get('ground_truth_note')
        formatted['ground_truth_created_at'] = alert['ground_truth_created_at'].isoformat() if alert.get('ground_truth_created_at') else None
    else:
        formatted['ground_truth_validated'] = False
    
    return formatted
```

---

## 📊 Estructura de Datos (JSON Response)

### Antes:
```json
{
  "id": "uuid",
  "type": "ARRHYTHMIA",
  "level": "high",
  "description": "...",
  "status": "new",
  "created_at": "2025-11-25T14:30:00Z",
  "location": {...}
}
```

### Después:
```json
{
  "id": "uuid",
  "type": "ARRHYTHMIA",
  "level": "high",
  "description": "Probabilidad: 0.873. FC=125 bpm...",
  "status": "new",
  "created_at": "2025-11-25T14:30:00Z",
  "location": {...},
  
  "created_by_model_id": "988e1fee-e18e-4eb9-9b9d-72ae7d48d8bc",
  "model_name": "RandomForest",
  "source_inference_id": "uuid-inference",
  
  "ground_truth_validated": true,
  "ground_truth_id": "uuid-gt",
  "ground_truth_event_code": "ARRHYTHMIA",
  "ground_truth_event_label": "Arritmia Cardíaca",
  "ground_truth_doctor": "Dr. Juan García",
  "ground_truth_doctor_id": "uuid-doctor",
  "ground_truth_note": "Confirmo arritmia, paciente bajo tratamiento",
  "ground_truth_created_at": "2025-11-25T15:00:00Z"
}
```

---

## 🔄 Flujo de Datos Completo

```
┌─────────────────────┐
│   AI-Monitor        │
│   (Worker)          │
│                     │
│  1. Lee InfluxDB    │
│  2. Llama a IA      │
│  3. Crea alerta     │
│     con model_id    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   PostgreSQL        │
│   tabla: alerts     │
│                     │
│  - created_by_model │
│  - source_inference │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Médico valida     │
│   (Admin Panel)     │
│                     │
│  Crea ground_truth  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   PostgreSQL        │
│   tabla:            │
│   ground_truth_     │
│   labels            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Patient Service   │
│                     │
│  JOIN alerts +      │
│  ground_truth       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Desktop App       │
│   (Paciente)        │
│                     │
│  Muestra alertas    │
│  con IA y validación│
└─────────────────────┘
```

---

## 🎯 Beneficios

### Para Pacientes:
1. **Transparencia**: Saben cuándo una alerta fue generada por IA
2. **Confianza**: Ven si un médico ya la validó
3. **Información**: Pueden leer las notas clínicas del doctor
4. **Contexto**: Entienden la probabilidad de la predicción

### Para el Sistema:
1. **Trazabilidad**: Cada alerta tiene su origen documentado
2. **Calidad**: Se puede medir la precisión del modelo
3. **Mejora continua**: Ground truth permite entrenar mejores modelos
4. **Compliance**: Documentación médica completa

---

## 🧪 Testing

### Casos de Prueba:

1. **Alerta de IA sin validar**
   - ✅ Debe mostrar chip "🤖 IA"
   - ✅ Debe mostrar probabilidad
   - ✅ Debe mostrar "Pendiente de validación"

2. **Alerta de IA validada**
   - ✅ Debe mostrar chip "🤖 IA"
   - ✅ Debe mostrar "Validado por médico"
   - ✅ Debe mostrar nombre del doctor
   - ✅ Debe mostrar notas clínicas

3. **Alerta manual (no IA)**
   - ✅ No debe mostrar chip de IA
   - ✅ No debe mostrar panel de información adicional

4. **Extracción de probabilidad**
   - ✅ Debe extraer de "Probabilidad: 0.85"
   - ✅ Debe extraer de "85%"
   - ✅ Debe manejar ausencia de probabilidad

---

## 📝 Notas Técnicas

### Relación Alerts ↔ Ground Truth

La relación se hace mediante:
- **patient_id**: Mismo paciente
- **timestamp**: Ventana de ±10 minutos
- **event_type**: Compatible con alert_type

```sql
LEFT JOIN ground_truth_labels gt ON (
    gt.patient_id = a.patient_id 
    AND gt.onset >= (a.created_at - INTERVAL '10 minutes')
    AND gt.onset <= (a.created_at + INTERVAL '10 minutes')
)
```

### Extracción de Probabilidad

Se utilizan expresiones regulares para extraer la probabilidad de la descripción:

```java
// Patrón 1: "Probabilidad: 0.85"
Pattern.compile("Probabilidad[:\\s]+([0-9]*\\.?[0-9]+)")

// Patrón 2: "85%"
Pattern.compile("([0-9]+(?:\\.[0-9]+)?)%")
```

---

## 🚀 Próximos Pasos (Opcional)

1. **Gráficos de probabilidad**: Mostrar historial de probabilidades en el tiempo
2. **Filtros avanzados**: Filtrar por alertas validadas/no validadas
3. **Notificaciones**: Alertar al paciente cuando una alerta es validada
4. **Estadísticas**: Mostrar tasa de precisión del modelo (TP/FP)
5. **Exportación**: Permitir descargar reportes de alertas validadas

---

## ✅ Conclusión

Se ha implementado exitosamente un sistema completo de visualización de **alertas inteligentes** que permite a los pacientes:

- 🤖 Ver qué alertas fueron generadas por IA
- 📊 Conocer la probabilidad de la predicción
- ✅ Saber si un médico validó la alerta
- 📝 Leer las notas clínicas de validación

Todo esto manteniendo la **arquitectura existente** y agregando mínimas modificaciones tanto en el frontend (Desktop App) como en el backend (Patient Service).

---

**Fecha de implementación**: 25 de noviembre de 2025  
**Desarrollador**: GitHub Copilot + Usuario
