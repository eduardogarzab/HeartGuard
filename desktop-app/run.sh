#!/bin/bash
# ============================================================================
# HeartGuard Desktop App - Script de Ejecución para Linux/Mac
# ============================================================================

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  HeartGuard Desktop App - Iniciando...                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Verificar si Java está instalado
if ! command -v java &> /dev/null; then
    echo -e "${RED}[ERROR] Java no está instalado${NC}"
    echo ""
    echo "Por favor instala Java 11 o superior desde:"
    echo "  - Ubuntu/Debian: sudo apt install openjdk-11-jdk"
    echo "  - Fedora/RHEL: sudo dnf install java-11-openjdk"
    echo "  - macOS: brew install openjdk@11"
    echo "  - O descarga desde: https://adoptium.net/"
    echo ""
    exit 1
fi

# Mostrar versión de Java
echo -e "${BLUE}[INFO] Versión de Java:${NC}"
java -version
echo ""

# Verificar si el JAR existe
if [ ! -f "target/desktop-app-1.0.0.jar" ]; then
    echo -e "${YELLOW}[WARNING] El archivo JAR no existe. Compilando proyecto...${NC}"
    echo ""
    
    # Verificar si Maven está instalado
    if ! command -v mvn &> /dev/null; then
        echo -e "${RED}[ERROR] Maven no está instalado${NC}"
        echo ""
        echo "Por favor instala Maven desde:"
        echo "  - Ubuntu/Debian: sudo apt install maven"
        echo "  - Fedora/RHEL: sudo dnf install maven"
        echo "  - macOS: brew install maven"
        echo "  - O descarga desde: https://maven.apache.org/download.cgi"
        echo ""
        exit 1
    fi
    
    echo -e "${BLUE}[INFO] Compilando proyecto con Maven...${NC}"
    mvn clean package -DskipTests
    
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR] La compilación falló${NC}"
        echo ""
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}[SUCCESS] Compilación exitosa${NC}"
    echo ""
fi

# Ejecutar la aplicación
echo -e "${BLUE}[INFO] Iniciando HeartGuard Desktop App...${NC}"
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

java -jar target/desktop-app-1.0.0.jar

# Capturar el código de salida
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
