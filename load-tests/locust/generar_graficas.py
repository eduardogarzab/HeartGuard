#!/usr/bin/env python3
"""
Script para generar gráficas PNG de los resultados de las pruebas de carga.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# Crear directorio de gráficas
os.makedirs('resultados/graficas', exist_ok=True)

# Datos de las pruebas (recopilados de la ejecución) - 8 TESTS COMPLETOS
pruebas = {
    'Smoke Test': {
        'requests': 153,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 5.25,
        'avg_response': 126,
        'min_response': 92,
        'max_response': 522,
        'users': 5
    },
    'Write Heavy': {
        'requests': 129,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 4.41,
        'avg_response': 155,
        'min_response': 93,
        'max_response': 501,
        'users': 10
    },
    'Ramp Test': {
        'requests': 10301,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 33.30,
        'avg_response': 228,
        'min_response': 90,
        'max_response': 1268,
        'users': 20
    },
    'Breakpoint': {
        'requests': 3146,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 38.92,
        'avg_response': 242,
        'min_response': 90,
        'max_response': 1193,
        'users': 50
    },
    'Spike Test': {
        'requests': 650,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 13.54,
        'avg_response': 168,
        'min_response': 90,
        'max_response': 563,
        'users': 20
    },
    'Baseline': {
        'requests': 132,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 4.48,
        'avg_response': 136,
        'min_response': 94,
        'max_response': 335,
        'users': 10
    },
    'Read Heavy': {
        'requests': 291,
        'failures': 0,
        'error_rate': 0.00,
        'rps': 9.92,
        'avg_response': 148,
        'min_response': 92,
        'max_response': 357,
        'users': 15
    },
    'Soak Test': {
        'requests': 158,
        'failures': 2,
        'error_rate': 1.27,
        'rps': 2.71,
        'avg_response': 151,
        'min_response': 93,
        'max_response': 348,
        'users': 10
    }
}

nombres = list(pruebas.keys())
colores = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e91e63', '#00bcd4']

# Configurar estilo global
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['legend.fontsize'] = 9

# 1. Gráfica de Total de Requests
fig, ax = plt.subplots(figsize=(10, 6))
requests = [pruebas[n]['requests'] for n in nombres]
bars = ax.bar(nombres, requests, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Número de Requests')
ax.set_title('📊 Total de Requests por Prueba de Carga', fontweight='bold', pad=15)
ax.set_ylim(0, max(requests) * 1.15)

# Agregar valores en las barras
for bar, val in zip(bars, requests):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + max(requests)*0.02,
            f'{val:,}', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('resultados/graficas/01_total_requests.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 01_total_requests.png")

# 2. Gráfica de Tasa de Errores
fig, ax = plt.subplots(figsize=(10, 6))
error_rates = [pruebas[n]['error_rate'] for n in nombres]
bars = ax.bar(nombres, error_rates, color='#27ae60', edgecolor='black', linewidth=0.5)
ax.set_ylabel('Tasa de Errores (%)')
ax.set_title('✅ Tasa de Errores por Prueba (0% = Éxito Total)', fontweight='bold', pad=15)
ax.set_ylim(0, 5)
ax.axhline(y=1, color='orange', linestyle='--', alpha=0.7, label='Umbral aceptable (1%)')
ax.axhline(y=0, color='green', linestyle='-', alpha=0.5, linewidth=2)

# Agregar valores
for bar, val in zip(bars, error_rates):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 0.15,
            f'{val:.2f}%', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.legend(loc='upper right')
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('resultados/graficas/02_tasa_errores.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 02_tasa_errores.png")

# 3. Gráfica de Tiempo de Respuesta Promedio
fig, ax = plt.subplots(figsize=(10, 6))
avg_responses = [pruebas[n]['avg_response'] for n in nombres]
bars = ax.bar(nombres, avg_responses, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Tiempo de Respuesta (ms)')
ax.set_title('⏱️ Tiempo de Respuesta Promedio por Prueba', fontweight='bold', pad=15)
ax.set_ylim(0, max(avg_responses) * 1.2)
ax.axhline(y=200, color='orange', linestyle='--', alpha=0.7, label='Umbral medio (200ms)')
ax.axhline(y=500, color='red', linestyle='--', alpha=0.7, label='Umbral alto (500ms)')

for bar, val in zip(bars, avg_responses):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + max(avg_responses)*0.02,
            f'{val}ms', ha='center', va='bottom', fontweight='bold', fontsize=11)

ax.legend(loc='upper right')
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('resultados/graficas/03_tiempo_respuesta_promedio.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 03_tiempo_respuesta_promedio.png")

# 4. Gráfica de Requests por Segundo (RPS)
fig, ax = plt.subplots(figsize=(10, 6))
rps_values = [pruebas[n]['rps'] for n in nombres]
bars = ax.bar(nombres, rps_values, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Requests por Segundo (RPS)')
ax.set_title('🚀 Throughput: Requests por Segundo', fontweight='bold', pad=15)
ax.set_ylim(0, max(rps_values) * 1.2)

for bar, val in zip(bars, rps_values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + max(rps_values)*0.02,
            f'{val:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=11)

plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('resultados/graficas/04_requests_por_segundo.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 04_requests_por_segundo.png")

# 5. Gráfica de Distribución de Tiempos (Min, Avg, Max)
fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(nombres))
width = 0.25

min_vals = [pruebas[n]['min_response'] for n in nombres]
avg_vals = [pruebas[n]['avg_response'] for n in nombres]
max_vals = [pruebas[n]['max_response'] for n in nombres]

bars1 = ax.bar(x - width, min_vals, width, label='Mínimo', color='#27ae60', edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x, avg_vals, width, label='Promedio', color='#3498db', edgecolor='black', linewidth=0.5)
bars3 = ax.bar(x + width, max_vals, width, label='Máximo', color='#e74c3c', edgecolor='black', linewidth=0.5)

ax.set_ylabel('Tiempo de Respuesta (ms)')
ax.set_title('📈 Distribución de Tiempos de Respuesta (Min/Avg/Max)', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(nombres, rotation=15, ha='right')
ax.legend(loc='upper left')
ax.set_ylim(0, max(max_vals) * 1.15)

# Agregar valores en barras
for bars, vals in [(bars1, min_vals), (bars2, avg_vals), (bars3, max_vals)]:
    for bar, val in zip(bars, vals):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(max_vals)*0.01,
                f'{val}', ha='center', va='bottom', fontsize=8, rotation=45)

plt.tight_layout()
plt.savefig('resultados/graficas/05_distribucion_tiempos.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 05_distribucion_tiempos.png")

# 6. Gráfica de Usuarios vs RPS
fig, ax1 = plt.subplots(figsize=(10, 6))

users = [pruebas[n]['users'] for n in nombres]
rps = [pruebas[n]['rps'] for n in nombres]

ax1.set_xlabel('Prueba de Carga')
ax1.set_ylabel('Usuarios Concurrentes', color='#3498db')
bars = ax1.bar(nombres, users, color='#3498db', alpha=0.7, label='Usuarios', edgecolor='black', linewidth=0.5)
ax1.tick_params(axis='y', labelcolor='#3498db')
ax1.set_ylim(0, max(users) * 1.3)

ax2 = ax1.twinx()
ax2.set_ylabel('RPS', color='#e74c3c')
line = ax2.plot(nombres, rps, color='#e74c3c', marker='o', linewidth=2, markersize=8, label='RPS')
ax2.tick_params(axis='y', labelcolor='#e74c3c')
ax2.set_ylim(0, max(rps) * 1.3)

# Agregar valores
for bar, u in zip(bars, users):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + max(users)*0.02,
            f'{u}', ha='center', va='bottom', fontweight='bold', color='#3498db', fontsize=10)

for i, (nombre, r) in enumerate(zip(nombres, rps)):
    ax2.annotate(f'{r:.1f}', (i, r), textcoords="offset points", xytext=(0, 10),
                ha='center', fontweight='bold', color='#e74c3c', fontsize=10)

ax1.set_title('👥 Usuarios Concurrentes vs Throughput (RPS)', fontweight='bold', pad=15)

# Leyenda combinada
from matplotlib.lines import Line2D
legend_elements = [
    mpatches.Patch(facecolor='#3498db', alpha=0.7, edgecolor='black', label='Usuarios'),
    Line2D([0], [0], color='#e74c3c', marker='o', linewidth=2, label='RPS')
]
ax1.legend(handles=legend_elements, loc='upper left')

plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig('resultados/graficas/06_usuarios_vs_rps.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 06_usuarios_vs_rps.png")

# 7. Dashboard Resumen
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Subplot 1: Requests totales
ax = axes[0, 0]
bars = ax.bar(nombres, requests, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Requests')
ax.set_title('Total de Requests', fontweight='bold')
ax.tick_params(axis='x', rotation=25)
for bar, val in zip(bars, requests):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(requests)*0.02,
            f'{val:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Subplot 2: Tasa de errores (pie chart - casi todo verde, pequeño rojo para soak)
ax = axes[0, 1]
total_requests = sum([pruebas[n]['requests'] for n in nombres])
total_failures = sum([pruebas[n]['failures'] for n in nombres])
success_rate = ((total_requests - total_failures) / total_requests) * 100
error_rate = 100 - success_rate
sizes = [success_rate, error_rate] if error_rate > 0 else [100]
colors_pie = ['#27ae60', '#e74c3c'] if error_rate > 0 else ['#27ae60']
ax.pie(sizes, colors=colors_pie, startangle=90,
       wedgeprops=dict(width=0.5, edgecolor='white'))
ax.text(0, 0, f'{error_rate:.2f}%\nErrores', ha='center', va='center', fontsize=18, fontweight='bold', color='#27ae60' if error_rate < 1 else '#e74c3c')
ax.set_title('Tasa de Errores Global', fontweight='bold')

# Subplot 3: Tiempo de respuesta
ax = axes[1, 0]
bars = ax.bar(nombres, avg_responses, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('Tiempo (ms)')
ax.set_title('Tiempo de Respuesta Promedio', fontweight='bold')
ax.axhline(y=200, color='orange', linestyle='--', alpha=0.7)
ax.tick_params(axis='x', rotation=25)
for bar, val in zip(bars, avg_responses):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(avg_responses)*0.02,
            f'{val}ms', ha='center', va='bottom', fontsize=9, fontweight='bold')

# Subplot 4: RPS
ax = axes[1, 1]
bars = ax.bar(nombres, rps_values, color=colores, edgecolor='black', linewidth=0.5)
ax.set_ylabel('RPS')
ax.set_title('Throughput (Requests/Segundo)', fontweight='bold')
ax.tick_params(axis='x', rotation=25)
for bar, val in zip(bars, rps_values):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + max(rps_values)*0.02,
            f'{val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

fig.suptitle('🏥 HeartGuard API - Dashboard de Pruebas de Carga', fontsize=16, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig('resultados/graficas/07_dashboard_resumen.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 07_dashboard_resumen.png")

# 8. Gráfica de escalabilidad (usuarios vs métricas)
fig, ax = plt.subplots(figsize=(10, 6))

# Ordenar por usuarios
datos_ordenados = sorted([(pruebas[n]['users'], pruebas[n]['rps'], pruebas[n]['avg_response'], n) 
                          for n in nombres])
usuarios_ord = [d[0] for d in datos_ordenados]
rps_ord = [d[1] for d in datos_ordenados]
resp_ord = [d[2] for d in datos_ordenados]
nombres_ord = [d[3] for d in datos_ordenados]

ax.plot(usuarios_ord, rps_ord, 'o-', color='#3498db', linewidth=2, markersize=10, label='RPS')
ax.set_xlabel('Usuarios Concurrentes')
ax.set_ylabel('Requests por Segundo', color='#3498db')
ax.tick_params(axis='y', labelcolor='#3498db')

ax2 = ax.twinx()
ax2.plot(usuarios_ord, resp_ord, 's--', color='#e74c3c', linewidth=2, markersize=10, label='Tiempo Resp.')
ax2.set_ylabel('Tiempo de Respuesta (ms)', color='#e74c3c')
ax2.tick_params(axis='y', labelcolor='#e74c3c')

# Anotar puntos
for u, r, t, n in zip(usuarios_ord, rps_ord, resp_ord, nombres_ord):
    ax.annotate(f'{n}\n{r:.1f} RPS', (u, r), textcoords="offset points", xytext=(0, 15),
                ha='center', fontsize=8, color='#3498db')

ax.set_title('📊 Escalabilidad: Usuarios vs Rendimiento', fontweight='bold', pad=15)
ax.legend(loc='upper left')
ax2.legend(loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('resultados/graficas/08_escalabilidad.png', dpi=150, bbox_inches='tight')
plt.close()
print("✅ Generada: 08_escalabilidad.png")

print("\n" + "="*60)
print("🎉 ¡Todas las gráficas generadas exitosamente!")
print("="*60)
print(f"\nUbicación: resultados/graficas/")
print("\nArchivos generados:")
for i, nombre in enumerate([
    "01_total_requests.png",
    "02_tasa_errores.png", 
    "03_tiempo_respuesta_promedio.png",
    "04_requests_por_segundo.png",
    "05_distribucion_tiempos.png",
    "06_usuarios_vs_rps.png",
    "07_dashboard_resumen.png",
    "08_escalabilidad.png"
], 1):
    print(f"  {i}. {nombre}")
