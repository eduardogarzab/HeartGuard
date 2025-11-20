#!/bin/bash
# Script para configurar la ruta hacia Digital Ocean Spaces
# Este script debe ejecutarse con privilegios de root

SPACES_IP="134.199.128.128"
GATEWAY_IP="129.212.176.1"
INTERFACE="eth0"

# Verificar si la ruta ya existe
if ip route show | grep -q "$SPACES_IP"; then
    echo "✓ La ruta a Digital Ocean Spaces ya existe"
    ip route get $SPACES_IP
else
    echo "📡 Agregando ruta a Digital Ocean Spaces ($SPACES_IP)"
    ip route add ${SPACES_IP}/32 via $GATEWAY_IP dev $INTERFACE
    
    if [ $? -eq 0 ]; then
        echo "✓ Ruta agregada exitosamente"
        ip route get $SPACES_IP
    else
        echo "✗ Error al agregar la ruta"
        exit 1
    fi
fi

# Probar conectividad
echo ""
echo "🔍 Probando conectividad a Digital Ocean Spaces..."
if ping -c 2 -W 3 $SPACES_IP > /dev/null 2>&1; then
    echo "✓ Conectividad ICMP exitosa"
else
    echo "⚠ No se pudo alcanzar con ICMP (puede estar bloqueado)"
fi

# Probar HTTPS
if command -v curl > /dev/null 2>&1; then
    echo ""
    echo "🔍 Probando conexión HTTPS..."
    if curl -s -I --connect-timeout 5 https://atl1.digitaloceanspaces.com | head -1 | grep -q "HTTP"; then
        echo "✓ Conexión HTTPS exitosa a Digital Ocean Spaces"
    else
        echo "✗ Error en conexión HTTPS"
        exit 1
    fi
fi

echo ""
echo "✅ Configuración completada exitosamente"
