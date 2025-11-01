# 🎯 Organización Dinámica - Cambios Implementados

## Problema Original
El código de organización estaba hardcodeado como `"FAM-001"`, lo que significa que todos los usuarios verían los mismos datos, independientemente de su organización real.

## Solución Implementada

### 📦 Backend Changes

#### 1. **Auth Service - models.py**
Agregado método para obtener organizaciones del usuario:

```python
def get_organizations(self) -> list[dict]:
    """Fetch user organizations and their roles."""
    # Consulta a user_org_membership para obtener todas las organizaciones
    # del usuario con sus roles correspondientes
```

Actualizado `to_dict()` para incluir organizaciones:
```python
def to_dict(self):
    return {
        'id': str(self.id),
        'name': self.name,
        'email': self.email,
        # ... otros campos
        'organizations': self.get_organizations()  # ← NUEVO
    }
```

#### 2. **Respuesta de Login Actualizada**
Ahora el login devuelve:
```xml
<response>
  <data>
    <tokens>...</tokens>
    <user>
      <id>...</id>
      <name>Dra. Ana Ruiz</name>
      <email>ana.ruiz@heartguard.com</email>
      <organizations>
        <item>
          <id>uuid...</id>
          <code>FAM-001</code>
          <name>Familia García</name>
          <role_code>org_admin</role_code>
          <role_name>Organization Admin</role_name>
        </item>
      </organizations>
    </user>
  </data>
</response>
```

### 🎨 Frontend Changes

#### 1. **auth.js - Extracción de Organizaciones**
Al hacer login, ahora extraemos y guardamos las organizaciones:

```javascript
// Guardar todas las organizaciones del usuario
localStorage.setItem("organizations", JSON.stringify(organizations));

// Guardar la primera como organización activa (por defecto)
localStorage.setItem("current_org_code", organizations[0].code);
localStorage.setItem("current_org_name", organizations[0].name);
localStorage.setItem("current_org_role", organizations[0].role_code);
```

#### 2. **dashboard.js - Uso Dinámico**
Ahora obtenemos el código de organización dinámicamente:

```javascript
// ANTES (HARDCODED ❌)
const orgCode = "FAM-001";

// AHORA (DINÁMICO ✅)
const orgCode = localStorage.getItem("current_org_code");
```

El header del dashboard muestra:
```javascript
`${userName} - ${currentOrgName}`  // Ej: "Dra. Ana Ruiz - Familia García"
```

#### 3. **Validación de Organización**
Si un usuario no tiene organización asignada:
```javascript
if (!orgCode) {
  console.warn("No se encontró código de organización...");
  tbody.innerHTML = `<tr><td colspan="5">No se encontró organización asignada</td></tr>`;
  return;
}
```

## 📊 Datos en LocalStorage

Después del login, se guardan:

| Key | Ejemplo | Descripción |
|-----|---------|-------------|
| `jwt` | `eyJhbG...` | Token de autenticación |
| `user_id` | `uuid` | ID del usuario |
| `user_name` | `Dra. Ana Ruiz` | Nombre del usuario |
| `user_email` | `ana.ruiz@...` | Email del usuario |
| `organizations` | `[{code: "FAM-001", ...}]` | Array con todas las organizaciones |
| `current_org_code` | `FAM-001` | Código de la org activa |
| `current_org_name` | `Familia García` | Nombre de la org activa |
| `current_org_role` | `org_admin` | Rol del usuario en esta org |

## 🧪 Flujo Completo

### Escenario 1: Usuario con FAM-001
1. Ana hace login con `ana.ruiz@heartguard.com`
2. Backend devuelve sus organizaciones: `[{code: "FAM-001", ...}]`
3. Frontend guarda `current_org_code = "FAM-001"`
4. Al navegar a "Usuarios", muestra solo usuarios de FAM-001

### Escenario 2: Usuario con FAM-002
1. Otro usuario hace login
2. Backend devuelve sus organizaciones: `[{code: "FAM-002", ...}]`
3. Frontend guarda `current_org_code = "FAM-002"`
4. Al navegar a "Usuarios", muestra solo usuarios de FAM-002

### Escenario 3: Usuario sin organización
1. Usuario sin membresía hace login
2. Backend devuelve `organizations: []`
3. Frontend detecta `current_org_code = null`
4. Muestra mensaje: "No se encontró organización asignada"

## 🔄 Próximas Mejoras (Futuras)

### Selector de Organización
Si un usuario pertenece a múltiples organizaciones, podríamos agregar:

```html
<select id="orgSelector">
  <option value="FAM-001">Familia García</option>
  <option value="FAM-002">Familia López</option>
</select>
```

Y al cambiar la selección, actualizar `current_org_code` y recargar datos.

## 📝 Pasos para Aplicar

1. **Ejecuta el script de actualización:**
   ```powershell
   cd d:\Usuarios\jeser\OneDrive\Documentos\UDEM\HeartGuard\Microservicios
   .\update-auth-user-services.ps1
   ```

2. **⚠️ IMPORTANTE: Cierra sesión en el frontend**
   - Los datos viejos en localStorage no tienen las organizaciones
   - Debes hacer logout y volver a hacer login

3. **Verifica en la consola del navegador:**
   - Deberías ver: "Organizaciones del usuario: [{code: 'FAM-001', ...}]"
   - Verifica que `localStorage.getItem("current_org_code")` devuelva el código correcto

4. **Navega a Usuarios:**
   - Ahora deberías ver solo los usuarios de TU organización
   - El header mostrará: "Tu Nombre - Nombre de Organización"

## 🐛 Troubleshooting

### "No se encontró organización asignada"
**Causa:** El usuario no tiene membresía en ninguna organización.

**Solución:** Verifica en la base de datos:
```sql
SELECT u.email, o.code, o.name
FROM users u
JOIN user_org_membership uom ON u.id = uom.user_id
JOIN organizations o ON uom.org_id = o.id
WHERE u.email = 'ana.ruiz@heartguard.com';
```

### Los datos no cambian después de actualizar
**Causa:** localStorage tiene datos viejos.

**Solución:**
1. Abre la consola del navegador (F12)
2. Ve a Application > Local Storage
3. Borra todo o solo haz logout
4. Vuelve a hacer login

### "current_org_code is null"
**Causa:** La respuesta XML no incluye organizaciones.

**Solución:**
1. Verifica los logs de auth_service: `docker-compose logs auth_service`
2. Asegúrate que el servicio se haya reconstruido correctamente
3. Prueba el endpoint directamente para ver la respuesta
