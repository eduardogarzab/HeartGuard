#!/bin/bash
# ============================================================================
# HeartGuard Desktop App - Compilar y Ejecutar
# ============================================================================

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  HeartGuard Desktop App - Compilar y Ejecutar             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar si Maven está instalado
if ! command -v mvn &> /dev/null; then
    echo -e "${RED}[ERROR] Maven no está instalado${NC}"
    echo ""
    echo "Por favor instala Maven desde:"
    echo "  - Ubuntu/Debian: sudo apt install maven"
    echo "  - Fedora/RHEL: sudo dnf install maven"
    echo "  - macOS: brew install maven"
    echo ""
    exit 1
fi

echo -e "${BLUE}[INFO] Limpiando proyecto...${NC}"
mvn clean

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERROR] Error al limpiar el proyecto${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[INFO] Compilando proyecto...${NC}"
mvn package -DskipTests

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}[ERROR] La compilación falló${NC}"
    echo ""
    echo "Revisa los errores anteriores"
    exit 1
fi

echo ""
echo -e "${GREEN}[SUCCESS] Compilación exitosa${NC}"
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""
echo -e "${BLUE}[INFO] Iniciando aplicación...${NC}"
echo ""

java -jar target/desktop-app-1.0.0.jar

EXIT_CODE=$?

echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}[ERROR] La aplicación terminó con errores (código: $EXIT_CODE)${NC}"
    echo ""
    exit $EXIT_CODE
fi

echo -e "${GREEN}[INFO] Aplicación cerrada correctamente${NC}"
echo ""
