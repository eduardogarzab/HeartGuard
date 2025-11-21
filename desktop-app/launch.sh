#!/bin/bash

# =============================================================================
# HeartGuard Desktop App - Launch Script
# =============================================================================

echo "=========================================="
echo "HeartGuard Desktop App"
echo "=========================================="
echo ""

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo "❌ Archivo .env no encontrado"
    echo ""
    echo "Crea un archivo .env con la configuración necesaria:"
    echo "  cp .env.example .env"
    echo "  # Edita .env con tus valores"
    echo ""
    exit 1
fi

echo "✓ Archivo .env encontrado"
echo ""

# Verificar que existe el JAR
if [ ! -f "target/heartguard-desktop-1.0-SNAPSHOT.jar" ]; then
    echo "❌ El JAR no existe. Ejecuta 'mvn clean package' primero."
    exit 1
fi

echo "✓ JAR encontrado"
echo ""
echo "🚀 Iniciando aplicación..."
echo "   (La configuración se cargará desde el archivo .env)"
echo ""

# Ejecutar la aplicación
# El archivo .env será leído automáticamente por la clase AppConfig
java -jar target/heartguard-desktop-1.0-SNAPSHOT.jar

