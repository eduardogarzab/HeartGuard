#!/bin/bash

# Script para ejecutar HeartGuard Desktop App con Java 21
# Este script configura todas las opciones necesarias de JVM

echo "🚀 Iniciando HeartGuard Desktop App con Java 21..."

# Verificar versión de Java
JAVA_VERSION=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}' | cut -d'.' -f1)
if [ "$JAVA_VERSION" != "21" ]; then
    echo "⚠️  Advertencia: Se esperaba Java 21 pero se detectó Java $JAVA_VERSION"
fi

# Opciones de JVM para JavaFX WebView en Java 21
JVM_OPTS=(
    # Opciones de apertura de módulos para JavaFX WebView
    "--add-opens" "javafx.web/com.sun.webkit=ALL-UNNAMED"
    "--add-opens" "javafx.web/com.sun.javafx.webkit=ALL-UNNAMED"
    "--add-opens" "javafx.graphics/com.sun.javafx.sg.prism=ALL-UNNAMED"
    "--add-opens" "javafx.graphics/com.sun.prism=ALL-UNNAMED"
    "--add-opens" "javafx.graphics/com.sun.glass.ui=ALL-UNNAMED"
    "--add-opens" "javafx.graphics/com.sun.javafx.tk=ALL-UNNAMED"
    
    # Exportar módulos necesarios
    "--add-exports" "javafx.web/com.sun.webkit=ALL-UNNAMED"
    "--add-exports" "javafx.web/com.sun.javafx.webkit=ALL-UNNAMED"
    "--add-exports" "javafx.graphics/com.sun.glass.ui=ALL-UNNAMED"
    
    # Opciones de rendimiento
    "-Xms512m"
    "-Xmx2048m"
    "-XX:+UseG1GC"
    "-XX:+UseStringDeduplication"
)

# Ejecutar la aplicación
java "${JVM_OPTS[@]}" -jar target/desktop-app-1.0.0.jar

echo "✅ Aplicación cerrada"
