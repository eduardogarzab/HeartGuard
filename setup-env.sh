#!/bin/bash

# Script para copiar .env.example a .env en todos los servicios y backend
# Autor: HeartGuard Team
# Fecha: 2025-11-05

set -e

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Configurando archivos .env ===${NC}\n"

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Función para copiar .env.example a .env
copy_env() {
    local dir=$1
    local service_name=$2
    
    if [ -f "$dir/.env.example" ]; then
        if [ -f "$dir/.env" ]; then
            echo -e "${YELLOW}⚠️  $service_name: .env ya existe, omitiendo...${NC}"
        else
            cp "$dir/.env.example" "$dir/.env"
            echo -e "${GREEN}✓ $service_name: .env creado${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  $service_name: .env.example no encontrado en $dir${NC}"
    fi
}

# Backend (raíz del proyecto)
echo "📦 Backend (raíz)"
copy_env "$PROJECT_ROOT" "Backend"
echo ""

# Microservicios
echo "🔧 Microservicios"
SERVICES=(
    "admin"
    "auth"
    "gateway"
    "patient"
    "user"
)

for service in "${SERVICES[@]}"; do
    service_dir="$PROJECT_ROOT/services/$service"
    if [ -d "$service_dir" ]; then
        copy_env "$service_dir" "  - $service"
    else
        echo -e "${YELLOW}⚠️  - $service: directorio no encontrado${NC}"
    fi
done

echo ""
echo -e "${GREEN}=== Configuración completada ===${NC}"
echo -e "${BLUE}Nota: Recuerda actualizar los valores en los archivos .env según tu entorno${NC}"
