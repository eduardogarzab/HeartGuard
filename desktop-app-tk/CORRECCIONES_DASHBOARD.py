"""
RESUMEN DE CORRECCIONES - Dashboard de Usuario (Staff)
=======================================================

PROBLEMA IDENTIFICADO:
----------------------
Los datos del dashboard de staff (Ana Ruiz) no se mostraban correctamente porque:
1. El backend devuelve los datos dentro de un objeto 'data', pero el código estaba
   intentando acceder directamente a las propiedades de primer nivel.
2. El campo 'risk_level' viene como objeto {code: "high", label: "Alto"} pero
   el código esperaba un string simple.

ESTRUCTURA REAL DEL BACKEND:
----------------------------
{
  "data": {
    "overview": { ... },
    "metrics": { ... },
    "care_teams": [ ... ]
  }
}

CAMBIOS REALIZADOS:
-------------------

1. heartguard_tk/ui/user_dashboard.py - _render_metrics():
   - Agregado: dashboard_data = _dict_from(dashboard, "data")
   - Agregado: metrics_data = _dict_from(metrics_payload, "data")
   - Ahora extrae correctamente overview de data.overview
   - Ahora extrae correctamente metrics de data.metrics

2. heartguard_tk/ui/user_dashboard.py - _render_care_teams():
   - Agregado: care_teams_data = _dict_from(care_teams_payload, "data")
   - Agregado: patients_data = _dict_from(patients_payload, "data")
   - Ahora busca care_teams dentro de data
   - Maneja risk_level como objeto o string:
     ```python
     risk = patient.get("risk_level")
     if isinstance(risk, dict):
         risk_str = risk.get("label", risk.get("code", ""))
     else:
         risk_str = str(risk or "")
     ```

3. heartguard_tk/ui/user_dashboard.py - _render_alerts():
   - Agregado: dashboard_data = _dict_from(dashboard, "data")
   - Ahora busca alertas dentro de data.recent_alerts o data.alerts

4. heartguard_tk/ui/user_dashboard.py - Corrección del mapa:
   - Cambiado fit_bounding_box() para usar el orden correcto de coordenadas:
     top_left = (max_lat, min_lon), bottom_right = (min_lat, max_lon)

DATOS DE PRUEBA (seed.sql):
---------------------------
Organización FAM-001 (Familia García):
- 2 pacientes: María Delgado (riesgo Alto), Valeria Ortiz (riesgo Bajo)
- 1 equipo: "Equipo Cardiología Familiar" con 2 miembros
- 2 cuidadores
- 5 alertas en últimos 7 días (0 abiertas)
- Promedio 2.5 alertas por paciente

Ubicaciones del mapa:
- Martín López: (22.558549999999997, -99.72805)
- José Hernández: en CDMX

CREDENCIALES DE PRUEBA:
-----------------------
Staff:
- ana.ruiz@heartguard.com / Demo#2025
- martin.ops@heartguard.com / Demo#2025

Pacientes:
- maria.delgado@patients.heartguard.com / Paciente#2025
- jose.hernandez@patients.heartguard.com / Paciente#2025
- valeria.ortiz@patients.heartguard.com / Paciente#2025

VERIFICACIÓN:
-------------
✓ Todas las pruebas automatizadas pasaron exitosamente
✓ El parsing de datos funciona correctamente
✓ Los contadores muestran los valores correctos
✓ Los equipos y pacientes se listan correctamente
✓ El nivel de riesgo se muestra correctamente (Alto, Bajo)
✓ El mapa se renderiza sin errores

PARA PROBAR MANUALMENTE:
------------------------
1. Iniciar sesión con ana.ruiz@heartguard.com / Demo#2025
2. Verificar que aparezca "Familia García" en el selector de organización
3. Verificar métricas:
   - Pacientes: 2
   - Equipos: 1
   - Cuidadores: 2
   - Alertas abiertas: 0
   - Alertas 7d: 5
   - Promedio alertas/paciente: 2.50
4. Verificar pestaña "Equipos":
   - Debe mostrar "Equipo Cardiología Familiar" con 2 integrantes
5. Verificar pestaña "Pacientes":
   - María Delgado - Equipo Cardiología Familiar - Alto
   - Valeria Ortiz - Equipo Cardiología Familiar - Bajo
6. Verificar mapa:
   - Debe mostrar ubicaciones de miembros del equipo
   - Botón "Actualizar mapa" debe funcionar
"""

print(__doc__)
