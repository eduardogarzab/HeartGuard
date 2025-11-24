# 🔍 Guía de Verificación - Signos Vitales InfluxDB en Cliente Org-Admin

## 📍 Ubicación en la Interfaz

Los signos vitales se muestran en el **perfil del paciente**, específicamente:

```
┌─────────────────────────────────────────┐
│ 👤 Nombre del Paciente                  │
│ Información básica, correo, etc.        │
├─────────────────────────────────────────┤
│ [Estadísticas: Cuidadores, Equipos...]  │ <- ESTADÍSTICAS
├─────────────────────────────────────────┤
│ 📊 Signos Vitales en Tiempo Real        │ <- AQUÍ ESTÁN LOS GRÁFICOS
│ [Gráficas de Chart.js]                  │
├─────────────────────────────────────────┤
│ 📍 Ubicación reciente                   │ <- MAPA
│ [Mapa con ubicación]                    │
└─────────────────────────────────────────┘
```

## 🧪 Pasos de Verificación

### 1. Prueba Básica de Chart.js

Primero, verifica que Chart.js funciona correctamente:

```bash
# Desde /root/HeartGuard
cd clients/org-admin
python3 -m http.server 8082
```

Luego abre en el navegador: `http://localhost:8082/test-vital-signs.html`

**Resultado esperado:**
- ✅ Mensaje: "Chart.js cargado correctamente"
- ✅ Una gráfica de línea con datos de prueba
- ❌ Si sale error, Chart.js no está cargando

### 2. Verificar Servicios

Asegúrate de que todos los servicios estén corriendo:

```bash
cd /root/HeartGuard/services
docker-compose ps
```

**Servicios necesarios:**
- ✅ `gateway` - Puerto 8080
- ✅ `admin` - Puerto interno
- ✅ `realtime-data-generator` - Puerto interno
- ✅ `influxdb` - Puerto 8086
- ✅ `postgres` - Puerto 5432

### 3. Verificar Datos en InfluxDB

Verifica que haya datos de signos vitales:

```bash
# Entrar a InfluxDB
docker exec -it heartguard-influxdb influx

# Dentro de influx
> use heartguard_db
> show measurements
> select * from vital_signs limit 10
```

**Resultado esperado:**
- Debe mostrar mediciones como: `vital_signs`, `heart_rate`, etc.
- Debe haber lecturas recientes con campos como `patient_id`, `device_id`, `value`

### 4. Abrir el Cliente Org-Admin

```bash
# Gateway debería estar corriendo en puerto 8080
# Abre en navegador: http://localhost:8080
```

O si tienes los archivos estáticos:
```bash
cd /root/HeartGuard/clients/org-admin
python3 -m http.server 8083
# Abre: http://localhost:8083
```

### 5. Navegar al Perfil del Paciente

1. **Login**
   - Email: (tu usuario org_admin)
   - Password: (tu contraseña)

2. **Seleccionar Organización**
   - Clic en cualquier tarjeta de organización

3. **Ir a Pacientes**
   - Clic en pestaña "Pacientes"
   - Verás tabla con lista de pacientes

4. **Abrir Perfil**
   - Clic en cualquier fila de la tabla
   - Se abre modal con perfil del paciente

### 6. Verificar en Consola del Navegador (F12)

Al abrir el perfil del paciente, deberías ver estos logs:

```javascript
🔍 Verificando dispositivos en perfil: 2  // o el número de dispositivos
🎨 renderVitalSignsCharts llamado: {patientId: "xxx", deviceCount: 2}
✅ Generando contenedor de signos vitales: vital-signs-xxx
🚀 Iniciando carga de signos vitales para dispositivo: dev-123
⏰ Ejecutando loadVitalSignsData...
📊 Respuesta de signos vitales: {patient_id: "xxx", count: 50, readings: [...]}
```

## 🎯 Casos Posibles

### Caso A: No hay dispositivos
```
Mensaje mostrado:
"📊 No hay dispositivos con datos de signos vitales disponibles"
```
**Solución:** Asignar dispositivos al paciente en la pestaña "Dispositivos"

### Caso B: Hay dispositivos pero no hay datos
```
Mensaje mostrado:
"📊 No hay lecturas recientes de signos vitales"
```
**Solución:** 
- Verificar que el servicio realtime-data-generator esté generando datos
- Revisar logs: `docker-compose logs realtime-data-generator`

### Caso C: Error al cargar datos
```
Mensaje mostrado:
"❌ Error al cargar los datos de signos vitales"
Error: [mensaje de error]
```
**Solución:**
- Verificar en consola el error específico
- Revisar que el endpoint `/realtime/patients/{id}/vital-signs` funcione
- Probar manualmente: `curl -H "Accept: application/xml" http://localhost:8080/realtime/patients/{patient_id}/vital-signs`

### Caso D: Todo correcto - Se muestran gráficas
```
Visualización:
- Selector de dispositivos (si hay más de 1)
- Tarjetas con gráficas para cada signo vital:
  ❤️ Frecuencia Cardíaca
  🫁 SpO₂
  🌡️ Temperatura
  💉 Presión Arterial
  🌬️ Frecuencia Respiratoria
```

## 🔧 Archivos Relevantes

### Frontend (Cliente Org-Admin)
```
clients/org-admin/
├── index.html                    # Incluye Chart.js
├── assets/
│   ├── css/app.css              # Estilos de vital-signs-*
│   └── js/
│       ├── api.js               # getPatientVitalSigns() - XML
│       └── app.js               # renderVitalSignsCharts(), loadVitalSignsData()
└── test-vital-signs.html        # Página de prueba
```

### Backend (Servicios)
```
services/
└── realtime-data-generator/
    └── src/generator/
        ├── app.py               # Endpoint /patients/{id}/vital-signs
        ├── xml.py               # Soporte XML
        └── influx.py            # Consultas a InfluxDB
```

## 📊 Estructura de Datos

### Respuesta XML del Servicio
```xml
<response>
  <patient_id>patient-123</patient_id>
  <device_id>device-456</device_id>
  <measurement>vital_signs</measurement>
  <count>50</count>
  <readings>
    <reading>
      <time>2025-11-24T10:00:00Z</time>
      <heart_rate>75</heart_rate>
      <spo2>98</spo2>
      <temperature>36.5</temperature>
      <systolic_bp>120</systolic_bp>
      <diastolic_bp>80</diastolic_bp>
      <respiratory_rate>16</respiratory_rate>
    </reading>
    ...
  </readings>
</response>
```

### Objeto JavaScript Parseado
```javascript
{
  patient_id: "patient-123",
  device_id: "device-456",
  measurement: "vital_signs",
  count: 50,
  readings: [
    {
      time: "2025-11-24T10:00:00Z",
      heart_rate: 75,
      spo2: 98,
      temperature: 36.5,
      systolic_bp: 120,
      diastolic_bp: 80,
      respiratory_rate: 16
    },
    ...
  ]
}
```

## 🐛 Debugging

### Si no ves la sección en el HTML:

1. **Verificar que el modal se está abriendo:**
   ```javascript
   // En consola del navegador
   document.querySelector('.profile-modal')  // Debe existir
   ```

2. **Verificar que la sección existe:**
   ```javascript
   // Buscar la sección de signos vitales
   document.querySelector('.vital-signs-container')  // Debe existir
   ```

3. **Ver el HTML completo del perfil:**
   ```javascript
   console.log(document.querySelector('.profile-modal').innerHTML)
   ```

### Si la API no responde:

```bash
# Probar endpoint directamente
curl -H "Accept: application/xml" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8080/realtime/patients/PATIENT_ID/vital-signs

# Ver logs del servicio
docker-compose logs -f realtime-data-generator
```

## ✅ Checklist Final

- [ ] Chart.js carga correctamente (test-vital-signs.html funciona)
- [ ] Servicios corriendo (docker-compose ps)
- [ ] InfluxDB tiene datos (influx query)
- [ ] Modal de perfil se abre correctamente
- [ ] Sección "📊 Signos Vitales en Tiempo Real" aparece en HTML
- [ ] Logs en consola muestran ejecución correcta
- [ ] API responde con XML válido
- [ ] Gráficas de Chart.js se renderizan

---

**Autor:** GitHub Copilot  
**Fecha:** 24 Nov 2025  
**Proyecto:** HeartGuard - Cliente Org-Admin
