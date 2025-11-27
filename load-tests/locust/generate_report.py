#!/usr/bin/env python3
"""
Script para ejecutar todas las pruebas de carga y generar un reporte con gráficas.
"""

import subprocess
import os
import json
import time
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import numpy as np

# Configuración
HOST = "http://129.212.181.53:8080"
OUTPUT_DIR = "resultados/graficas"
RESULTS_DIR = "resultados"

# Definir las pruebas a ejecutar
TESTS = [
    {
        "name": "Smoke Test",
        "file": "smoke_test.py",
        "users": 5,
        "spawn_rate": 1,
        "duration": "30s",
        "description": "Prueba básica de humo para verificar funcionalidad"
    },
    {
        "name": "Write Heavy Test",
        "file": "write_heavy_test.py",
        "users": 10,
        "spawn_rate": 2,
        "duration": "30s",
        "description": "Prueba intensiva de escritura"
    },
    {
        "name": "Ramp Test",
        "file": "ramp_test.py",
        "users": 20,
        "spawn_rate": 2,
        "duration": "60s",
        "description": "Prueba de carga gradual"
    },
    {
        "name": "Breakpoint Test",
        "file": "breakpoint_test.py",
        "users": 15,
        "spawn_rate": 5,
        "duration": "30s",
        "description": "Prueba para encontrar punto de quiebre"
    },
    {
        "name": "Spike Test",
        "file": "spike_test.py",
        "users": 20,
        "spawn_rate": 10,
        "duration": "30s",
        "description": "Prueba de picos de tráfico"
    }
]

def ensure_dirs():
    """Crear directorios necesarios."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

def run_test(test_config):
    """Ejecutar una prueba de Locust y capturar resultados."""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {test_config['name']}")
    print(f"{'='*60}")
    
    csv_prefix = os.path.join(RESULTS_DIR, test_config['file'].replace('.py', ''))
    
    cmd = [
        "locust",
        "-f", test_config['file'],
        "--headless",
        f"--users={test_config['users']}",
        f"--spawn-rate={test_config['spawn_rate']}",
        f"--run-time={test_config['duration']}",
        f"--host={HOST}",
        f"--csv={csv_prefix}",
        "--csv-full-history"
    ]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()
    
    # Parsear resultados del output
    output = result.stdout + result.stderr
    
    # Extraer métricas clave
    metrics = parse_locust_output(output)
    metrics['duration_seconds'] = end_time - start_time
    metrics['test_name'] = test_config['name']
    metrics['description'] = test_config['description']
    metrics['users'] = test_config['users']
    metrics['csv_prefix'] = csv_prefix
    
    return metrics

def parse_locust_output(output):
    """Parsear la salida de Locust para extraer métricas."""
    metrics = {
        'total_requests': 0,
        'failures': 0,
        'failure_rate': 0.0,
        'avg_response_time': 0,
        'min_response_time': 0,
        'max_response_time': 0,
        'requests_per_second': 0.0,
        'p50': 0,
        'p95': 0,
        'p99': 0
    }
    
    lines = output.split('\n')
    for line in lines:
        # Buscar línea de Aggregated
        if 'Aggregated' in line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 10:
                try:
                    # Extraer valores
                    reqs = parts[2].strip()
                    fails = parts[3].strip()
                    
                    metrics['total_requests'] = int(reqs) if reqs.isdigit() else 0
                    
                    # Parsear failures (formato: "0(0.00%)")
                    if '(' in fails:
                        fail_count = fails.split('(')[0].strip()
                        fail_pct = fails.split('(')[1].replace(')', '').replace('%', '').strip()
                        metrics['failures'] = int(fail_count) if fail_count.isdigit() else 0
                        metrics['failure_rate'] = float(fail_pct) if fail_pct else 0.0
                    
                    # Tiempos de respuesta
                    avg_time = parts[4].strip()
                    min_time = parts[5].strip()
                    max_time = parts[6].strip()
                    
                    metrics['avg_response_time'] = int(avg_time) if avg_time.isdigit() else 0
                    metrics['min_response_time'] = int(min_time) if min_time.isdigit() else 0
                    metrics['max_response_time'] = int(max_time) if max_time.isdigit() else 0
                    
                    # Percentiles
                    if len(parts) >= 12:
                        p50 = parts[8].strip()
                        p95 = parts[10].strip()
                        metrics['p50'] = int(p50) if p50.isdigit() else 0
                        metrics['p95'] = int(p95) if p95.isdigit() else 0
                    
                    # RPS
                    rps = parts[-1].strip()
                    try:
                        metrics['requests_per_second'] = float(rps)
                    except:
                        pass
                except Exception as e:
                    print(f"Error parsing line: {e}")
    
    return metrics

def generate_comparison_charts(all_results):
    """Generar gráficas comparativas de todas las pruebas."""
    
    test_names = [r['test_name'].replace(' Test', '') for r in all_results]
    
    # Configuración de estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    colors = ['#2ecc71', '#3498db', '#9b59b6', '#e74c3c', '#f39c12']
    
    # 1. Gráfica de Total de Requests
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(test_names, [r['total_requests'] for r in all_results], color=colors)
    ax.set_xlabel('Tipo de Prueba', fontsize=12)
    ax.set_ylabel('Total de Requests', fontsize=12)
    ax.set_title('Total de Requests por Tipo de Prueba', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, [r['total_requests'] for r in all_results]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50, 
                f'{val:,}', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '01_total_requests.png'), dpi=150)
    plt.close()
    print("✓ Generada: 01_total_requests.png")
    
    # 2. Gráfica de Tasa de Errores
    fig, ax = plt.subplots(figsize=(10, 6))
    failure_rates = [r['failure_rate'] for r in all_results]
    bar_colors = ['#2ecc71' if rate == 0 else '#e74c3c' for rate in failure_rates]
    bars = ax.bar(test_names, failure_rates, color=bar_colors)
    ax.set_xlabel('Tipo de Prueba', fontsize=12)
    ax.set_ylabel('Tasa de Errores (%)', fontsize=12)
    ax.set_title('Tasa de Errores por Tipo de Prueba', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(failure_rates) + 1 if max(failure_rates) > 0 else 1)
    for bar, val in zip(bars, failure_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                f'{val:.2f}%', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '02_failure_rate.png'), dpi=150)
    plt.close()
    print("✓ Generada: 02_failure_rate.png")
    
    # 3. Gráfica de Tiempo de Respuesta Promedio
    fig, ax = plt.subplots(figsize=(10, 6))
    avg_times = [r['avg_response_time'] for r in all_results]
    bars = ax.bar(test_names, avg_times, color=colors)
    ax.set_xlabel('Tipo de Prueba', fontsize=12)
    ax.set_ylabel('Tiempo de Respuesta Promedio (ms)', fontsize=12)
    ax.set_title('Tiempo de Respuesta Promedio por Tipo de Prueba', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, avg_times):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{val} ms', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '03_avg_response_time.png'), dpi=150)
    plt.close()
    print("✓ Generada: 03_avg_response_time.png")
    
    # 4. Gráfica de Requests por Segundo
    fig, ax = plt.subplots(figsize=(10, 6))
    rps = [r['requests_per_second'] for r in all_results]
    bars = ax.bar(test_names, rps, color=colors)
    ax.set_xlabel('Tipo de Prueba', fontsize=12)
    ax.set_ylabel('Requests por Segundo', fontsize=12)
    ax.set_title('Throughput (RPS) por Tipo de Prueba', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, rps):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '04_requests_per_second.png'), dpi=150)
    plt.close()
    print("✓ Generada: 04_requests_per_second.png")
    
    # 5. Gráfica de Tiempos de Respuesta (Min, Avg, Max)
    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(test_names))
    width = 0.25
    
    min_times = [r['min_response_time'] for r in all_results]
    avg_times = [r['avg_response_time'] for r in all_results]
    max_times = [r['max_response_time'] for r in all_results]
    
    bars1 = ax.bar(x - width, min_times, width, label='Mínimo', color='#2ecc71')
    bars2 = ax.bar(x, avg_times, width, label='Promedio', color='#3498db')
    bars3 = ax.bar(x + width, max_times, width, label='Máximo', color='#e74c3c')
    
    ax.set_xlabel('Tipo de Prueba', fontsize=12)
    ax.set_ylabel('Tiempo de Respuesta (ms)', fontsize=12)
    ax.set_title('Distribución de Tiempos de Respuesta', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(test_names)
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '05_response_time_distribution.png'), dpi=150)
    plt.close()
    print("✓ Generada: 05_response_time_distribution.png")
    
    # 6. Gráfica de Usuarios vs RPS
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    users = [r['users'] for r in all_results]
    rps = [r['requests_per_second'] for r in all_results]
    
    color1 = '#3498db'
    ax1.set_xlabel('Tipo de Prueba', fontsize=12)
    ax1.set_ylabel('Usuarios Concurrentes', fontsize=12, color=color1)
    bars1 = ax1.bar(test_names, users, color=color1, alpha=0.7, label='Usuarios')
    ax1.tick_params(axis='y', labelcolor=color1)
    
    ax2 = ax1.twinx()
    color2 = '#e74c3c'
    ax2.set_ylabel('Requests por Segundo', fontsize=12, color=color2)
    line = ax2.plot(test_names, rps, color=color2, marker='o', linewidth=2, markersize=8, label='RPS')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title('Usuarios Concurrentes vs Throughput (RPS)', fontsize=14, fontweight='bold')
    
    # Leyenda combinada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '06_users_vs_rps.png'), dpi=150)
    plt.close()
    print("✓ Generada: 06_users_vs_rps.png")
    
    # 7. Gráfica de Resumen General (Dashboard)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('HeartGuard - Resumen de Pruebas de Carga', fontsize=16, fontweight='bold')
    
    # Total Requests
    axes[0, 0].bar(test_names, [r['total_requests'] for r in all_results], color=colors)
    axes[0, 0].set_title('Total de Requests')
    axes[0, 0].set_ylabel('Requests')
    
    # Failure Rate
    failure_rates = [r['failure_rate'] for r in all_results]
    bar_colors = ['#2ecc71' if rate == 0 else '#e74c3c' for rate in failure_rates]
    axes[0, 1].bar(test_names, failure_rates, color=bar_colors)
    axes[0, 1].set_title('Tasa de Errores (%)')
    axes[0, 1].set_ylabel('Porcentaje')
    
    # Response Time
    axes[1, 0].bar(test_names, [r['avg_response_time'] for r in all_results], color=colors)
    axes[1, 0].set_title('Tiempo de Respuesta Promedio (ms)')
    axes[1, 0].set_ylabel('Milisegundos')
    
    # RPS
    axes[1, 1].bar(test_names, [r['requests_per_second'] for r in all_results], color=colors)
    axes[1, 1].set_title('Requests por Segundo')
    axes[1, 1].set_ylabel('RPS')
    
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '07_dashboard_resumen.png'), dpi=150)
    plt.close()
    print("✓ Generada: 07_dashboard_resumen.png")

def generate_markdown_report(all_results):
    """Generar reporte en Markdown."""
    
    total_requests = sum(r['total_requests'] for r in all_results)
    total_failures = sum(r['failures'] for r in all_results)
    overall_failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    avg_rps = sum(r['requests_per_second'] for r in all_results) / len(all_results)
    
    report = f"""# 📊 Reporte de Pruebas de Carga - HeartGuard

**Fecha de ejecución:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Host probado:** {HOST}

---

## 🎯 Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| **Total de Requests** | {total_requests:,} |
| **Total de Errores** | {total_failures} |
| **Tasa de Error Global** | {overall_failure_rate:.2f}% |
| **RPS Promedio** | {avg_rps:.2f} |
| **Pruebas Ejecutadas** | {len(all_results)} |
| **Estado General** | {'✅ EXITOSO' if overall_failure_rate == 0 else '⚠️ CON ERRORES'} |

---

## 📈 Resultados Detallados por Prueba

"""
    
    for r in all_results:
        status = "✅ PASS" if r['failure_rate'] == 0 else "❌ FAIL"
        report += f"""### {r['test_name']} {status}

**Descripción:** {r['description']}

| Métrica | Valor |
|---------|-------|
| Usuarios Concurrentes | {r['users']} |
| Total Requests | {r['total_requests']:,} |
| Errores | {r['failures']} ({r['failure_rate']:.2f}%) |
| Tiempo Respuesta Promedio | {r['avg_response_time']} ms |
| Tiempo Respuesta Mínimo | {r['min_response_time']} ms |
| Tiempo Respuesta Máximo | {r['max_response_time']} ms |
| Requests/segundo | {r['requests_per_second']:.2f} |
| Duración | {r['duration_seconds']:.1f}s |

---

"""
    
    report += """## 📊 Gráficas

### 1. Total de Requests por Prueba
![Total Requests](graficas/01_total_requests.png)

### 2. Tasa de Errores
![Failure Rate](graficas/02_failure_rate.png)

### 3. Tiempo de Respuesta Promedio
![Avg Response Time](graficas/03_avg_response_time.png)

### 4. Throughput (RPS)
![Requests per Second](graficas/04_requests_per_second.png)

### 5. Distribución de Tiempos de Respuesta
![Response Time Distribution](graficas/05_response_time_distribution.png)

### 6. Usuarios vs RPS
![Users vs RPS](graficas/06_users_vs_rps.png)

### 7. Dashboard Resumen
![Dashboard](graficas/07_dashboard_resumen.png)

---

## 🔍 Análisis

"""
    
    # Análisis automático
    best_rps = max(all_results, key=lambda x: x['requests_per_second'])
    best_response = min(all_results, key=lambda x: x['avg_response_time'])
    
    report += f"""### Rendimiento
- **Mayor throughput:** {best_rps['test_name']} con {best_rps['requests_per_second']:.2f} RPS
- **Mejor tiempo de respuesta:** {best_response['test_name']} con {best_response['avg_response_time']} ms promedio

### Estabilidad
- Todas las pruebas se completaron {'sin errores' if overall_failure_rate == 0 else 'con algunos errores'}
- El sistema mantuvo {'estabilidad' if overall_failure_rate < 1 else 'cierta inestabilidad'} bajo carga

### Recomendaciones
"""
    
    if overall_failure_rate == 0:
        report += """- ✅ El sistema está funcionando correctamente bajo las cargas probadas
- Se recomienda ejecutar pruebas con mayor carga para encontrar límites
- Considerar implementar pruebas de soak (larga duración) para verificar estabilidad
"""
    else:
        report += """- ⚠️ Se detectaron errores durante las pruebas
- Revisar logs del servidor para identificar causas de los errores
- Optimizar endpoints con mayor tasa de errores
"""
    
    report += f"""
---

*Reporte generado automáticamente por el sistema de pruebas de carga de HeartGuard*
"""
    
    # Guardar reporte
    report_path = os.path.join(RESULTS_DIR, 'REPORTE_PRUEBAS.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ Reporte guardado en: {report_path}")
    return report

def main():
    """Función principal."""
    print("="*60)
    print("HeartGuard - Ejecución de Pruebas de Carga")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Host: {HOST}")
    print("="*60)
    
    ensure_dirs()
    
    all_results = []
    
    for test in TESTS:
        try:
            result = run_test(test)
            all_results.append(result)
            print(f"  ✓ Completado: {result['total_requests']} requests, "
                  f"{result['failure_rate']:.2f}% errores, "
                  f"{result['requests_per_second']:.2f} RPS")
        except Exception as e:
            print(f"  ✗ Error en {test['name']}: {e}")
    
    if all_results:
        print("\n" + "="*60)
        print("Generando gráficas...")
        print("="*60)
        generate_comparison_charts(all_results)
        
        print("\n" + "="*60)
        print("Generando reporte...")
        print("="*60)
        report = generate_markdown_report(all_results)
        
        # Guardar resultados JSON
        json_path = os.path.join(RESULTS_DIR, 'resultados.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2)
        print(f"✓ Resultados JSON guardados en: {json_path}")
        
        # Imprimir resumen final
        print("\n" + "="*60)
        print("RESUMEN FINAL")
        print("="*60)
        print(f"\n{'Prueba':<20} {'Requests':>10} {'Errores':>10} {'RPS':>10} {'Avg(ms)':>10}")
        print("-"*60)
        for r in all_results:
            name = r['test_name'].replace(' Test', '')
            print(f"{name:<20} {r['total_requests']:>10,} {r['failure_rate']:>9.2f}% "
                  f"{r['requests_per_second']:>10.2f} {r['avg_response_time']:>10}")
        print("-"*60)
        total_req = sum(r['total_requests'] for r in all_results)
        avg_err = sum(r['failure_rate'] for r in all_results) / len(all_results)
        avg_rps = sum(r['requests_per_second'] for r in all_results) / len(all_results)
        avg_time = sum(r['avg_response_time'] for r in all_results) / len(all_results)
        print(f"{'TOTAL/PROMEDIO':<20} {total_req:>10,} {avg_err:>9.2f}% {avg_rps:>10.2f} {avg_time:>10.0f}")
        
        print(f"\n✅ Todas las gráficas guardadas en: {OUTPUT_DIR}/")
        print(f"✅ Reporte completo en: {RESULTS_DIR}/REPORTE_PRUEBAS.md")

if __name__ == "__main__":
    main()
