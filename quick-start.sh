#!/bin/bash
# Quick Start Guide - HeartGuard Real-time Monitoring System

echo "=============================================="
echo "HeartGuard - Real-time Monitoring Quick Start"
echo "=============================================="
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Paso 1: Verificar conexiones
echo "Paso 1: Verificando conexiones..."
echo ""

# PostgreSQL
echo -n "PostgreSQL (134.199.204.58:5432): "
if nc -z 134.199.204.58 5432 2>/dev/null; then
    print_status "Accesible"
else
    print_error "No accesible"
fi

# InfluxDB
echo -n "InfluxDB (134.199.204.58:8086): "
if curl -s -o /dev/null -w "%{http_code}" http://134.199.204.58:8086/health | grep -q 200; then
    print_status "Accesible"
else
    print_error "No accesible"
fi

echo ""

# Paso 2: Verificar pacientes en la base de datos
echo "Paso 2: Verificando pacientes en la base de datos..."
PATIENT_COUNT=$(PGPASSWORD=dev_change_me psql -h 134.199.204.58 -U heartguard_app -d heartguard -t -c "SELECT COUNT(*) FROM heartguard.patients;" 2>/dev/null | tr -d ' ')

if [ -n "$PATIENT_COUNT" ] && [ "$PATIENT_COUNT" -gt 0 ]; then
    print_status "Encontrados $PATIENT_COUNT pacientes"
else
    print_warning "No se encontraron pacientes. Considera ejecutar el script de seed."
fi

echo ""

# Paso 3: Iniciar generador de datos
echo "Paso 3: Iniciando generador de datos en tiempo real..."
echo ""
print_warning "El generador se ejecutará en primer plano."
print_warning "Presiona Ctrl+C para detenerlo."
echo ""
read -p "¿Continuar? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    cd "$(dirname "$0")/services/realtime-data-generator"
    
    # Activar entorno virtual
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        print_error "No se encontró el entorno virtual. Ejecuta: python3 -m venv venv && pip install -r requirements.txt"
        exit 1
    fi
    
    # Ejecutar generador
    python generator.py
else
    echo ""
    print_warning "Para iniciar manualmente:"
    echo "  cd services/realtime-data-generator"
    echo "  ./start.sh"
    echo ""
fi
