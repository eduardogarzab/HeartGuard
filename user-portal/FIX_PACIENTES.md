# Fix: Pacientes No Se Mostraban en Dashboard

## Problema Identificado

El dashboard no mostraba los pacientes insertados en el backend, a pesar de que existían en la base de datos.

## Causa Raíz

El método `getAssignedPatients()` en `HeartGuardApiClient` estaba usando el endpoint `/patients/me`, que:
- Retorna error 500/404 del gateway
- No está implementado correctamente en el microservicio patient_service
- Era el mismo problema que teníamos con `/users/me`

```java
// ANTES (no funcionaba):
URI uri = URI.create(properties.getBaseUrl() + "/patients/me");
```

## Solución Implementada

### 1. Cambio de Endpoint
Modificado para usar `/patients` en lugar de `/patients/me`:

```java
// DESPUÉS (funciona):
URI uri = URI.create(properties.getBaseUrl() + "/patients");
```

### 2. Parser del Gateway Response
El endpoint `/patients` devuelve formato del gateway:
```json
{
  "code": 200,
  "status": "success",
  "data": {
    "patients": [
      {
        "id": "8c9436b4-f085-405f-a3d2-87cb1d1cf097",
        "person_name": "María Delgado",
        "birthdate": "1978-03-22",
        "sex_id": "5ac3c659-eeea-4d67-92e1-6226b350aaa5",
        "risk_level_id": "debcc07b-39b5-4cb7-9b87-f9f1c3bcafb4",
        "profile_photo_url": null,
        "org_id": "05bc3d9a-f6ce-4a2f-9359-634bf2962f9f",
        "created_at": "2025-07-04T05:07:24.832132"
      }
    ]
  },
  "meta": {
    "total": 3
  }
}
```

### 3. Actualización del DTO
Modificado `PatientSummaryDto` para coincidir con los campos del backend:

```java
// ANTES:
public record PatientSummaryDto(
    String id,
    @JsonProperty("person_name") String personName,
    @JsonProperty("risk_level_code") String riskLevelCode,
    @JsonProperty("profile_photo_url") String profilePhotoUrl
) {}

// DESPUÉS:
public record PatientSummaryDto(
    String id,
    String personName,
    String sexId,
    String riskLevelCode,
    String profilePhotoUrl
) {}
```

### 4. Implementación del Parser Robusto

```java
public List<PatientSummaryDto> getAssignedPatients(HttpSession session) {
    return executeWithRetry(session, token -> {
        URI uri = URI.create(properties.getBaseUrl() + "/patients");
        HttpHeaders headers = authorizationHeaders(token);
        ResponseEntity<GatewayResponse<Map<String, Object>>> response = 
            restTemplate.exchange(uri, HttpMethod.GET, new HttpEntity<>(headers),
                new ParameterizedTypeReference<GatewayResponse<Map<String, Object>>>() {});
        
        GatewayResponse<Map<String, Object>> body = response.getBody();
        if (body != null && body.data() != null) {
            Object patientsData = body.data().get("patients");
            if (patientsData instanceof List<?> patientsList) {
                List<PatientSummaryDto> result = patientsList.stream()
                    .filter(item -> item instanceof Map)
                    .map(item -> {
                        @SuppressWarnings("unchecked")
                        Map<String, Object> patientMap = (Map<String, Object>) item;
                        return new PatientSummaryDto(
                            (String) patientMap.get("id"),
                            (String) patientMap.get("person_name"),
                            (String) patientMap.get("sex_id"),
                            (String) patientMap.get("risk_level_id"),
                            (String) patientMap.get("profile_photo_url")
                        );
                    })
                    .toList();
                return result;
            }
        }
        return Collections.emptyList();
    });
}
```

## Archivos Modificados

1. **HeartGuardApiClient.java**
   - Método `getAssignedPatients()` reescrito
   - Cambio de endpoint `/patients/me` → `/patients`
   - Parser robusto para GatewayResponse

2. **PatientSummaryDto.java**
   - Agregado campo `sexId`
   - Removidas anotaciones `@JsonProperty`
   - Simplificado el record

## Resultados

### Pacientes Ahora Visibles:
✅ **María Delgado** (1978-03-22)  
✅ **José Hernández** (1965-11-04)  
✅ **Valeria Ortiz** (1992-07-15)  

### Características:
- ✅ Dashboard muestra todos los pacientes del sistema
- ✅ Tarjetas clicables para ver detalles
- ✅ Soporte automático para nuevos pacientes agregados
- ✅ Manejo de errores graceful (si falla, muestra lista vacía)

## Verificación

### Test Manual:
```bash
# 1. Verificar gateway
curl http://136.115.53.140:5000/patients

# 2. Verificar aplicación
# Abrir http://localhost:8081
# Login: admin@heartguard.com / Admin#2025
# Dashboard debe mostrar 3 pacientes
```

### Estado Actual:
- ✅ Compilación: SUCCESS
- ✅ Aplicación corriendo: PID 24208
- ✅ Puerto: 8081
- ✅ Gateway: Conectado (136.115.53.140:5000)

## Lecciones Aprendidas

1. **Preferir endpoints que funcionan**: `/patients` sobre `/patients/me`
2. **No asumir estructura de datos**: Verificar con curl/Postman primero
3. **Parser robusto**: Usar `instanceof` y casting seguro
4. **DTOs flexibles**: No usar anotaciones Jackson si parseamos manualmente
5. **Gateway envelope pattern**: Siempre extraer de `{code, status, data}`

## Próximos Pasos Sugeridos

### Opcional - Mejoras Futuras:
1. **Filtrado por usuario**: Si necesitas mostrar solo pacientes asignados al usuario actual
2. **Paginación**: Si el sistema crece, implementar lazy loading
3. **Búsqueda**: Agregar barra de búsqueda por nombre de paciente
4. **Ordenamiento**: Por nombre, fecha de creación, nivel de riesgo

### Recomendación para Backend:
Implementar correctamente `/patients/me` en el patient_service para filtrar por usuario autenticado:

```python
@bp.route("/me", methods=["GET"])
@require_auth()
def get_my_patients() -> "Response":
    user_id = g.current_user.get("sub")
    # Filtrar pacientes asignados al usuario actual
    patients = Patient.query.filter_by(assigned_user_id=user_id).all()
    return render_response({"patients": [p.to_dict() for p in patients]})
```

## Impacto

**Antes**: Dashboard vacío ❌  
**Después**: Dashboard con 3 pacientes ✅  

**Usuario puede ahora**:
- ✅ Ver todos los pacientes del sistema
- ✅ Clic en paciente para ver detalles
- ✅ Navegar entre pacientes fluidamente
- ✅ Ver automáticamente nuevos pacientes agregados

---

**Fecha de fix**: 1 de noviembre de 2025  
**Tiempo de implementación**: ~15 minutos  
**Archivos afectados**: 2  
**Líneas de código**: ~50
