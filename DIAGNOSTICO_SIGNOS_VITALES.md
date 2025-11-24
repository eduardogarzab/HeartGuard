# 🔍 Guía de Diagnóstico: Signos Vitales desde InfluxDB

## 📋 Estado Actual

He añadido **logs de debugging extensivos** al cliente org-admin que te mostrarán exactamente qué está pasando con los datos de InfluxDB.

## 🛠️ Pasos para Diagnosticar el Problema

### 1️⃣ Verificar que tus servicios estén corriendo

Primero, necesito que me confirmes las **URLs de tus servicios**:

```
❓ ¿Cuál es la URL de tu Gateway? (ej: http://192.168.1.100:8080)
❓ ¿Cuál es la URL del servicio Realtime? (ej: http://192.168.1.101:5007)
❓ ¿Cuál es la URL de InfluxDB? (ej: http://192.168.1.102:8086)
```

### 2️⃣ Abrir el cliente org-admin en el navegador

1. Abre el navegador (Chrome/Firefox/Edge)
2. Ve a la URL donde está el cliente org-admin
3. **Abre la consola del navegador presionando F12**
4. Ve a la pestaña "Console"

### 3️⃣ Iniciar sesión y abrir un perfil de paciente

1. Inicia sesión con tus credenciales de `org_admin`
2. Selecciona una organización
3. Ve a la pestaña "Pacientes"
4. Haz clic en cualquier paciente de la tabla

### 4️⃣ Observar los logs en la consola

Deberías ver una secuencia de logs como esta:

```
🔍 Verificando dispositivos en perfil: 2
🚀 Iniciando carga de signos vitales para dispositivo: abc-123
🎨 renderVitalSignsCharts llamado: { patientId: "...", deviceCount: 2 }
✅ Generando contenedor de signos vitales: vital-signs-...
⏰ Ejecutando loadVitalSignsData...
🔍 Iniciando carga de signos vitales: { patientId: "...", deviceId: "...", containerId: "..." }
📡 Llamando a API con token: ✅ Token presente
📊 Respuesta completa de signos vitales: { ... }
```

### 5️⃣ Copia TODA la información de la consola

**Necesito que me envíes:**

1. **Todos los logs** que aparecen en la consola (cópialos completos)
2. **Cualquier mensaje de error** en rojo
3. El resultado del log que dice: `📊 Respuesta completa de signos vitales:`

## 🔎 Posibles Escenarios

### ✅ Escenario 1: Todo funciona
```
📊 Respuesta completa de signos vitales: {
  patient_id: "550e8400-...",
  device_id: "dev-001",
  measurement: "vital_signs",
  readingsCount: 45,
  readings: [...]
}
✅ Procesando 45 lecturas
📝 Primera lectura: { time: "2025-11-23T...", heart_rate: 72, spo2: 98, ... }
📈 Frecuencia Cardíaca: 45 puntos de datos
📈 SpO₂: 45 puntos de datos
...
```
**→ Los gráficos deberían aparecer**

### ⚠️ Escenario 2: No hay datos en InfluxDB
```
📊 Respuesta completa de signos vitales: {
  patient_id: "550e8400-...",
  device_id: null,
  measurement: "vital_signs",
  readingsCount: 0,
  readings: []
}
⚠️ Array de readings está vacío
```
**→ Significa que InfluxDB no tiene datos para ese paciente**

### ❌ Escenario 3: Error de conexión
```
❌ Error crítico cargando signos vitales: TypeError: ...
   Status: 500
```
**→ Hay un problema de comunicación con el servicio**

### ❌ Escenario 4: Error de autenticación
```
❌ Error crítico cargando signos vitales: Error: Error 401
   Status: 401
```
**→ El token no es válido para el servicio realtime**

## 🧪 Script de Prueba Manual

También actualicé el script de prueba Python. Ejecuta esto:

```bash
cd C:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard
python test_influx_vital_signs.py
```

Te pedirá las URLs de tus servicios y probará la conexión directamente.

## 📝 Información que Necesito

Para ayudarte mejor, necesito que me proporciones:

1. **Las URLs exactas** de tus servicios (Gateway, Realtime, InfluxDB)
2. **Los logs completos** de la consola del navegador (F12 → Console)
3. **El resultado** del script de prueba Python
4. **¿Qué mensaje ves** en la sección de "Signos Vitales en Tiempo Real" del perfil del paciente?

## 🔧 Posibles Soluciones

Dependiendo de lo que veas en los logs, aquí están las soluciones:

### Si el problema es "No hay datos en InfluxDB":
- Necesitas ejecutar el generador de datos o asignar dispositivos al paciente
- Verifica que el servicio `realtime-data-generator` esté escribiendo a InfluxDB

### Si el problema es "Error de conexión":
- Verifica que el Gateway esté redirigiendo correctamente al servicio realtime
- Revisa la configuración del Gateway (routes para `/realtime/*`)

### Si el problema es "Error 401/403":
- El token del org_admin podría no tener permisos para el servicio realtime
- Verifica la configuración de autenticación en el Gateway

### Si el problema es "Chart.js no está disponible":
- Recarga la página con Ctrl+F5 (limpia la caché)
- Verifica que haya internet (Chart.js se carga desde CDN)

---

**¿Qué logs ves en la consola del navegador?** Cópialos aquí y podré ayudarte a resolver el problema específico.
