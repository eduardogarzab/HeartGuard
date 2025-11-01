#!/bin/bash
# Script para actualizar automáticamente la IP permitida en el firewall
# Se ejecuta al conectarse via SSH

# Obtener la IP del cliente SSH actual
CLIENT_IP=$(echo $SSH_CONNECTION | awk '{print $1}')

if [ -z "$CLIENT_IP" ]; then
    echo "❌ No se pudo detectar la IP del cliente SSH"
    exit 1
fi

# Verificar si la IP ya está permitida
CURRENT_ALLOWED=$(iptables -L DOCKER-USER -n | grep "ACCEPT.*tcp dpt:443" | grep -v "ctstate" | grep -v "lo" | awk '{print $4}' | head -1)

if [ "$CLIENT_IP" = "$CURRENT_ALLOWED" ]; then
    echo "✅ Tu IP ($CLIENT_IP) ya está permitida en el firewall"
    exit 0
fi

echo "🔄 Actualizando firewall con tu nueva IP: $CLIENT_IP"

# Flush existing DOCKER-USER rules
iptables -F DOCKER-USER

# Allow established connections
iptables -A DOCKER-USER -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Allow from localhost
iptables -A DOCKER-USER -i lo -j ACCEPT

# Allow current SSH client IP to access ports 443 and 80
iptables -A DOCKER-USER -p tcp --dport 443 -s $CLIENT_IP -j ACCEPT
iptables -A DOCKER-USER -p tcp --dport 80 -s $CLIENT_IP -j ACCEPT

# Drop all other external access to ports 80 and 443
iptables -A DOCKER-USER -p tcp --dport 80 -j DROP
iptables -A DOCKER-USER -p tcp --dport 443 -j DROP

# Allow everything else (for other Docker services)
iptables -A DOCKER-USER -j RETURN

# Actualizar el script de persistencia
sed -i "s/-s [0-9.]*/-s $CLIENT_IP/g" /root/HeartGuard/docker-ufw-fix.sh

echo "✅ Firewall actualizado - acceso permitido solo para $CLIENT_IP"
echo "   Puedes acceder a: https://admin.heartguard.live"
