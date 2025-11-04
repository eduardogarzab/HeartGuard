#!/bin/bash
# =============================================================================
# HeartGuard Services - Inicio Rápido
# =============================================================================
# Este script demuestra el uso básico del sistema de gestión de servicios
# =============================================================================

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  HeartGuard Services - Demo de Inicio Rápido"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Cambiar al directorio de services
cd "$(dirname "$0")"

# 1. Mostrar ayuda
echo "📚 Comandos disponibles:"
echo ""
make help
echo ""
read -p "Presiona Enter para continuar..."

# 2. Instalar dependencias (si es necesario)
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 1: Instalación de Dependencias"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Verificando entornos virtuales..."
if [ ! -d "auth/.venv" ] || [ ! -d "admin/.venv" ] || [ ! -d "gateway/.venv" ]; then
    echo "⚠️  Instalando dependencias (esto puede tomar unos minutos)..."
    make install
else
    echo "✓ Entornos virtuales ya instalados"
fi
echo ""
read -p "Presiona Enter para continuar..."

# 3. Iniciar servicios
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 2: Iniciando Servicios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
make start
echo ""
read -p "Presiona Enter para continuar..."

# 4. Ver estado
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 3: Estado de Servicios"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
make status
echo ""
read -p "Presiona Enter para continuar..."

# 5. Probar endpoints
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 4: Probando Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Health check - Auth Service:"
curl -s http://localhost:5001/health/ | python3 -m json.tool || echo "Error"
echo ""
echo "Health check - Admin Service:"
curl -s http://localhost:5002/health/ | python3 -m json.tool || echo "Error"
echo ""
echo "Health check - Gateway:"
curl -s http://localhost:8080/health/ | python3 -m json.tool || echo "Error"
echo ""
read -p "Presiona Enter para continuar..."

# 6. Ver logs
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 5: Últimas Líneas de Logs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Logs de Gateway (últimas 10 líneas):"
make logs-gateway | tail -10
echo ""
read -p "Presiona Enter para continuar..."

# 7. Ejemplo de reinicio
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Paso 6: Demo de Reinicio de Servicio Específico"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Reiniciando gateway..."
make restart-gateway
echo ""
make status
echo ""
read -p "Presiona Enter para finalizar..."

# 8. Resumen final
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✓ Demo Completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Comandos útiles:"
echo "  make status           - Ver estado de servicios"
echo "  make logs             - Ver todos los logs"
echo "  make tail-gateway     - Seguir logs de gateway"
echo "  make restart-admin    - Reiniciar admin-service"
echo "  make test             - Ejecutar todos los tests"
echo "  make stop             - Detener todos los servicios"
echo ""
echo "Servicios corriendo en:"
echo "  - Auth:    http://localhost:5001"
echo "  - Admin:   http://localhost:5002"
echo "  - Gateway: http://localhost:8080"
echo ""
echo "Para detener los servicios: make stop"
echo ""
