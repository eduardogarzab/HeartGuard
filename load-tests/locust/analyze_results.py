"""
Script de análisis de resultados de pruebas Locust.

Uso:
    python analyze_results.py resultados/20231127_143022_baseline_stats.csv
"""
import sys
import csv
from pathlib import Path
from datetime import datetime


def analyze_stats(csv_file):
    """Analiza archivo CSV de estadísticas de Locust."""
    
    print("=" * 70)
    print(f"Análisis de Resultados - {Path(csv_file).name}")
    print("=" * 70)
    print()
    
    # Leer CSV
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ Archivo CSV vacío")
        return
    
    # Análisis por endpoint
    print("📊 RESUMEN POR ENDPOINT")
    print("-" * 70)
    print(f"{'Endpoint':<40} {'Requests':>10} {'Fails':>10} {'Avg (ms)':>10}")
    print("-" * 70)
    
    total_requests = 0
    total_failures = 0
    endpoints_with_issues = []
    
    for row in rows:
        name = row.get('Name', 'Unknown')
        if name == 'Aggregated':
            continue
            
        requests = int(row.get('Request Count', 0))
        failures = int(row.get('Failure Count', 0))
        avg_time = float(row.get('Average Response Time', 0))
        
        total_requests += requests
        total_failures += failures
        
        # Determinar color/estado
        status = "✓"
        if failures > 0:
            status = "⚠"
            endpoints_with_issues.append(name)
        if avg_time > 1000:
            status = "❌"
        
        print(f"{status} {name:<38} {requests:>10} {failures:>10} {avg_time:>10.2f}")
    
    print("-" * 70)
    
    # Resumen general
    print()
    print("📈 RESUMEN GENERAL")
    print("-" * 70)
    
    failure_rate = (total_failures / total_requests * 100) if total_requests > 0 else 0
    
    # Buscar fila Aggregated
    aggregated = next((r for r in rows if r.get('Name') == 'Aggregated'), None)
    
    if aggregated:
        avg_time = float(aggregated.get('Average Response Time', 0))
        min_time = float(aggregated.get('Min Response Time', 0))
        max_time = float(aggregated.get('Max Response Time', 0))
        p50 = float(aggregated.get('50%', 0))
        p95 = float(aggregated.get('95%', 0))
        p99 = float(aggregated.get('99%', 0))
        rps = float(aggregated.get('Requests/s', 0))
        
        print(f"Total Requests:        {total_requests:,}")
        print(f"Total Failures:        {total_failures:,}")
        print(f"Failure Rate:          {failure_rate:.2f}%")
        print(f"Requests/sec:          {rps:.2f}")
        print()
        print(f"Avg Response Time:     {avg_time:.2f} ms")
        print(f"Min Response Time:     {min_time:.2f} ms")
        print(f"Max Response Time:     {max_time:.2f} ms")
        print()
        print(f"50th Percentile:       {p50:.2f} ms")
        print(f"95th Percentile:       {p95:.2f} ms")
        print(f"99th Percentile:       {p99:.2f} ms")
    
    print("-" * 70)
    
    # Evaluación
    print()
    print("🎯 EVALUACIÓN")
    print("-" * 70)
    
    if aggregated:
        status = "✅ PASSED"
        issues = []
        
        if failure_rate > 5:
            status = "❌ FAILED"
            issues.append(f"Failure rate muy alto: {failure_rate:.2f}% (objetivo: < 5%)")
        elif failure_rate > 1:
            status = "⚠️  WARNING"
            issues.append(f"Failure rate elevado: {failure_rate:.2f}% (objetivo: < 1%)")
        
        if avg_time > 1000:
            status = "❌ FAILED"
            issues.append(f"Latencia promedio muy alta: {avg_time:.2f}ms (objetivo: < 1000ms)")
        elif avg_time > 500:
            if status == "✅ PASSED":
                status = "⚠️  WARNING"
            issues.append(f"Latencia promedio elevada: {avg_time:.2f}ms (objetivo: < 500ms)")
        
        if p95 > 2000:
            status = "❌ FAILED"
            issues.append(f"P95 muy alto: {p95:.2f}ms (objetivo: < 2000ms)")
        elif p95 > 1000:
            if status == "✅ PASSED":
                status = "⚠️  WARNING"
            issues.append(f"P95 elevado: {p95:.2f}ms (objetivo: < 1000ms)")
        
        print(f"Estado: {status}")
        print()
        
        if issues:
            print("Problemas detectados:")
            for issue in issues:
                print(f"  • {issue}")
        else:
            print("✓ Todas las métricas dentro de los objetivos")
        
        if endpoints_with_issues:
            print()
            print("Endpoints con fallos:")
            for endpoint in endpoints_with_issues:
                print(f"  • {endpoint}")
    
    print("-" * 70)
    print()


def main():
    """Punto de entrada principal."""
    if len(sys.argv) < 2:
        print("Uso: python analyze_results.py <archivo_stats.csv>")
        print()
        print("Ejemplo:")
        print("  python analyze_results.py resultados/20231127_143022_baseline_stats.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"❌ Archivo no encontrado: {csv_file}")
        sys.exit(1)
    
    analyze_stats(csv_file)


if __name__ == "__main__":
    main()
