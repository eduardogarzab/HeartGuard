# 🎯 PRUEBAS FRONTEND - CONTROL DE ACCESO BASADO EN ROLES (RBAC)

## 📋 Resumen de Cambios Implementados

Se ha mejorado el frontend del **user-portal** para mostrar claramente el rol del usuario y proporcionar mensajes contextuales sobre qué información está viendo cada usuario según su rol.

### ✅ Mejoras Implementadas

1. **Dashboard (Pacientes)**
   - Banner informativo con nombre y rol del usuario
   - Mensaje contextual según el rol:
     - **Superadmin**: "Acceso completo - Visualizando todos los pacientes"
     - **Admin/Clinician**: "Visualizando pacientes de tu organización"
     - **Caregiver**: "Visualizando tus pacientes asignados"
   - Mensajes específicos cuando no hay pacientes según el rol

2. **Alertas y Dispositivos**
   - Badge de usuario mostrando nombre y rol
   - Navegación consistente entre módulos

3. **Código Backend**
   - Controladores actualizados para pasar información del usuario (nombre, rol)
   - Método auxiliar `getRoleMessage()` para generar mensajes contextuales

---

## 🧪 PRUEBAS A REALIZAR

### Pre-requisito
- La aplicación debe estar corriendo en `http://localhost:8081`
- Los microservicios deben estar activos en `136.115.53.140:5000`

### Usuario de Prueba Principal
**Email**: `admin@heartguard.com`  
**Password**: `Admin#2025`  
**Rol**: `superadmin`  
**Expectativa**: Ver 3 pacientes (María Delgado, José Hernández, Valeria Ortiz)

---

## 📝 Pasos de Prueba

### PRUEBA 1: Dashboard - Banner Informativo
1. Navega a `http://localhost:8081/login`
2. Inicia sesión con `admin@heartguard.com` / `Admin#2025`
3. **Verifica**:
   - [ ] Ves un **banner morado con gradiente** en la parte superior
   - [ ] El banner muestra: "👋 Bienvenido, Super Admin"
   - [ ] Se muestra el badge con el rol: "superadmin"
   - [ ] El mensaje dice: "Acceso completo al sistema - Visualizando todos los pacientes (3 en total)"

### PRUEBA 2: Lista de Pacientes
1. En la misma página del dashboard
2. **Verifica**:
   - [ ] Ves **3 pacientes** en el grid
   - [ ] Los nombres son: María Delgado, José Hernández, Valeria Ortiz
   - [ ] Cada tarjeta muestra el nivel de riesgo

### PRUEBA 3: Navegación - Alertas
1. Click en **"Alertas"** en la barra superior
2. **Verifica**:
   - [ ] Ves un **badge azul** arriba con "Super Admin · superadmin"
   - [ ] El título dice "Alertas del Sistema"
   - [ ] Se muestran las alertas (o mensaje "No hay alertas" si está vacío)

### PRUEBA 4: Navegación - Dispositivos
1. Click en **"Dispositivos"** en la barra superior
2. **Verifica**:
   - [ ] Ves el mismo **badge azul** con tu nombre y rol
   - [ ] El título dice "Dispositivos Registrados"
   - [ ] Se muestran los dispositivos (o mensaje de vacío)

### PRUEBA 5: Consistencia Visual
1. Navega entre las 4 páginas: Pacientes → Alertas → Dispositivos → Mi Perfil
2. **Verifica**:
   - [ ] La navegación superior se mantiene consistente
   - [ ] El indicador de página activa funciona correctamente
   - [ ] En cada página se muestra tu rol de alguna forma

### PRUEBA 6: Mensaje Sin Pacientes (Simulación)
**Nota**: Esta prueba requiere un usuario sin pacientes asignados, pero puedes verificar el código.

Si tuvieras un usuario **caregiver** sin pacientes:
- Vería: "📋 No hay pacientes disponibles"
- Mensaje: "No tienes pacientes asignados actualmente. Contacta con tu administrador si esto es un error."

---

## 🎨 Elementos Visuales a Verificar

### Banner del Dashboard
```
┌─────────────────────────────────────────────────────────┐
│ 👋 Bienvenido, Super Admin                             │
│ [superadmin] Acceso completo al sistema - Visualiz...  │
└─────────────────────────────────────────────────────────┘
```
- **Color**: Gradiente morado (#667eea → #764ba2)
- **Texto**: Blanco
- **Badge del rol**: Fondo translúcido blanco

### Badge en Alertas/Dispositivos
```
┌────────────────────────────┐
│ Super Admin · superadmin   │
└────────────────────────────┘
```
- **Color**: Fondo azul claro (#667eea con 10% opacidad)
- **Texto**: Azul (#667eea)

---

## 🔍 Verificación en Consola del Navegador

1. Abre las **DevTools** (F12)
2. Ve a la pestaña **Console**
3. Al navegar al dashboard, deberías ver logs como:
   ```
   ########## DASHBOARD REQUEST ##########
   Usuario en sesión OK - Role: superadmin
   Llamando apiClient.getAssignedPatients()...
   getAssignedPatients() retornó: 3 pacientes
   ########## DASHBOARD REQUEST COMPLETADO ##########
   ```

---

## ✅ Checklist de Funcionalidad

- [ ] El banner del dashboard es visible y atractivo
- [ ] El nombre del usuario se muestra correctamente
- [ ] El rol se muestra en el badge
- [ ] El mensaje contextual cambia según el rol
- [ ] Los pacientes se cargan y muestran correctamente
- [ ] La navegación entre páginas funciona
- [ ] Los badges de rol aparecen en Alertas y Dispositivos
- [ ] Los mensajes de "sin datos" son claros y apropiados
- [ ] No hay errores en la consola del navegador
- [ ] No hay errores 500 en las peticiones

---

## 📊 Resultados Esperados por Rol

| Rol | Pacientes Visibles | Mensaje |
|-----|-------------------|---------|
| **superadmin** | 3 (todos) | "Acceso completo al sistema - Visualizando todos los pacientes (3 en total)" |
| **clinician** (FAM-001) | 2 (María, Valeria) | "Visualizando pacientes de tu organización (2 pacientes)" |
| **caregiver** | 1 (su asignado) | "Visualizando tus pacientes asignados (1 pacientes)" |

**Nota**: Para probar con otros roles, necesitarías credenciales de otros usuarios. Los microservicios ya están configurados con RBAC, solo el frontend actual muestra todos los datos del superadmin.

---

## 🐛 Qué Hacer Si Algo Falla

### Error: No veo el banner morado
- Verifica que `userName` y `userRole` estén en el modelo
- Abre DevTools → Network → busca la petición al dashboard
- Revisa que la sesión tenga los datos del usuario

### Error: Sale "null" en el rol
- Verifica en la consola de Spring Boot que el login guardó el rol
- Busca el log: "Login response received from gateway"

### Error: Los pacientes no cargan
- Abre DevTools → Console → busca errores JavaScript
- Verifica en la consola de Spring Boot los logs de `getAssignedPatients()`
- Confirma que el gateway responde correctamente

---

## 📸 Capturas Esperadas

1. **Dashboard con banner**: Banner morado arriba, grid de 3 pacientes abajo
2. **Alertas con badge**: Badge azul claro arriba, lista de alertas
3. **Dispositivos con badge**: Badge azul claro arriba, grid de dispositivos

---

## ✨ Próximos Pasos (Opcional)

Si quieres mejorar aún más:

1. **Iconos por rol**: Agregar íconos diferentes según el rol (👨‍⚕️ clinician, 👨‍👩‍👧 caregiver, 👑 superadmin)
2. **Filtros visuales**: Botones para filtrar pacientes por riesgo
3. **Estadísticas**: Agregar tarjetas con contadores (total pacientes, alertas activas, etc.)
4. **Colores por rol**: Usar colores diferentes en el banner según el rol del usuario

---

## 📞 Soporte

Si encuentras algún problema durante las pruebas, verifica:
1. Los logs de Spring Boot en la terminal
2. Los logs del navegador (DevTools → Console)
3. Las peticiones HTTP (DevTools → Network)
4. Que los microservicios estén activos en el servidor

---

**¡Listo para probar!** 🚀

Abre tu navegador en `http://localhost:8081/login` y sigue las pruebas paso a paso.
