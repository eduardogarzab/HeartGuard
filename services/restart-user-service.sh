#!/bin/bash
# Script para reiniciar el user-service con la nueva configuración de base de datos

echo "🔄 Reiniciando user-service..."

# Detener procesos actuales
pkill -f "gunicorn.*user" && echo "✅ Procesos anteriores detenidos"

# Esperar un momento
sleep 2

# Cambiar al directorio del servicio
cd /root/HeartGuard/services/user

# Activar entorno virtual
source .venv/bin/activate

# Iniciar el servicio
nohup gunicorn -w 4 -b 0.0.0.0:5003 "src.user.app:create_app()" > /tmp/user-service.log 2>&1 &

echo "✅ User-service reiniciado"
echo "📋 Ver logs: tail -f /tmp/user-service.log"
echo ""
echo "🧪 Probar health:"
sleep 3
curl -s http://localhost:5003/health | jq .
