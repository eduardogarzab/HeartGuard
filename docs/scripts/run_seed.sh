#!/bin/bash
# =========================================================
# Script para ejecutar seed.sql con contraseña segura
# Uso:
#   ./run_seed.sh                    # Usa ADMIN_PASSWORD de .env.production
#   ./run_seed.sh "MiPassword123!"   # Especifica contraseña directamente
# =========================================================

set -e

# Directorio base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Determinar la contraseña
if [ -n "$1" ]; then
    # Contraseña pasada como argumento
    ADMIN_PWD="$1"
    echo "🔑 Usando contraseña proporcionada como argumento"
elif [ -f ".env.production" ]; then
    # Leer de .env.production
    ADMIN_PWD=$(grep "^ADMIN_PASSWORD=" .env.production | cut -d= -f2-)
    if [ -z "$ADMIN_PWD" ]; then
        echo "❌ Error: ADMIN_PASSWORD no encontrada en .env.production"
        echo ""
        echo "Opciones:"
        echo "  1. Agregar ADMIN_PASSWORD=tu_password a .env.production"
        echo "  2. Pasar la contraseña como argumento: $0 'tu_password'"
        exit 1
    fi
    echo "🔑 Usando ADMIN_PASSWORD de .env.production"
else
    echo "❌ Error: .env.production no encontrado"
    echo "Por favor especifica la contraseña como argumento: $0 'tu_password'"
    exit 1
fi

# Leer otras variables de entorno necesarias
source .env.production

echo "📦 Ejecutando seed.sql en la base de datos..."
echo "   Host: $PGHOST"
echo "   DB: $DBNAME"
echo "   User: $PGSUPER"
echo ""

# Ejecutar seed con la contraseña como variable de psql
docker exec -i heartguard-postgres psql \
    -U "$PGSUPER" \
    -d "$DBNAME" \
    -v admin_password="$ADMIN_PWD" \
    -f - < db/seed.sql

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Seed ejecutado exitosamente"
    echo ""
    echo "📧 Usuario: admin@heartguard.com"
    echo "🔐 Password: [configurada desde variable de entorno]"
    echo ""
    echo "⚠️  IMPORTANTE: Cambia la contraseña después del primer login"
else
    echo ""
    echo "❌ Error ejecutando seed"
    exit 1
fi
