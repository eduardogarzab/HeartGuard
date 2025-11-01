#!/bin/bash
# =========================================================
# Script para configurar deployment distribuido
# Uso: ./setup_distributed_deployment.sh <IP_MICROSERVICIOS>
# =========================================================

set -e

if [ -z "$1" ]; then
    echo "❌ Error: Debes proporcionar la IP del servidor de microservicios"
    echo ""
    echo "Uso: $0 <IP_MICROSERVICIOS>"
    echo "Ejemplo: $0 192.168.1.100"
    exit 1
fi

MICROSERVICES_IP="$1"
BACKEND_IP="134.199.133.125"

echo "=== 🌐 Configuración de Despliegue Distribuido ==="
echo ""
echo "📍 IP Backend: $BACKEND_IP"
echo "📍 IP Microservicios: $MICROSERVICES_IP"
echo ""

# =========================================================
# CONFIGURACIÓN MÁQUINA 1 (Backend)
# =========================================================

echo "1️⃣ Configurando firewall en MÁQUINA 1 (Backend)..."
echo ""
echo "Ejecuta estos comandos en la máquina del backend ($BACKEND_IP):"
echo ""
echo "# Permitir PostgreSQL desde microservicios"
echo "sudo ufw allow from $MICROSERVICES_IP to any port 5432 proto tcp comment 'PostgreSQL from microservices'"
echo ""
echo "# Permitir Redis TLS desde microservicios"
echo "sudo ufw allow from $MICROSERVICES_IP to any port 6380 proto tcp comment 'Redis TLS from microservices'"
echo ""
echo "# Verificar reglas"
echo "sudo ufw status numbered"
echo ""

echo "2️⃣ Actualizando .env.production del backend..."
if [ -f ".env.production" ]; then
    # Verificar si ya existe la configuración de microservicios
    if grep -q "MICROSERVICES_GATEWAY_URL" .env.production; then
        # Actualizar IP existente
        sed -i "s|MICROSERVICES_GATEWAY_URL=.*|MICROSERVICES_GATEWAY_URL=http://$MICROSERVICES_IP:5000|" .env.production
        echo "✅ MICROSERVICES_GATEWAY_URL actualizada"
    else
        # Agregar nueva configuración
        echo "" >> .env.production
        echo "# MICROSERVICIOS - URL del Gateway" >> .env.production
        echo "MICROSERVICES_GATEWAY_URL=http://$MICROSERVICES_IP:5000" >> .env.production
        echo "✅ MICROSERVICES_GATEWAY_URL agregada"
    fi
else
    echo "⚠️  Archivo .env.production no encontrado en el directorio actual"
fi

echo ""
echo "3️⃣ Configurando PostgreSQL para conexiones remotas..."
echo ""
echo "Ejecuta estos comandos en la máquina del backend ($BACKEND_IP):"
echo ""
echo "# Permitir conexión desde microservicios en pg_hba.conf"
echo "docker exec -it heartguard-postgres bash -c \\"
echo "  'echo \"hostssl heartguard heartguard_app $MICROSERVICES_IP/32 md5\" >> /var/lib/postgresql/data/pg_hba.conf'"
echo ""
echo "# Recargar configuración de PostgreSQL"
echo "docker exec heartguard-postgres psql -U postgres -c 'SELECT pg_reload_conf();'"
echo ""

# =========================================================
# CONFIGURACIÓN MÁQUINA 2 (Microservicios)
# =========================================================

echo ""
echo "=" | tr '=' '-' | head -c 60 && echo ""
echo ""
echo "4️⃣ Configurando firewall en MÁQUINA 2 (Microservicios)..."
echo ""
echo "Ejecuta estos comandos en la máquina de microservicios ($MICROSERVICES_IP):"
echo ""
echo "# Permitir Gateway desde backend"
echo "sudo ufw allow from $BACKEND_IP to any port 5000 proto tcp comment 'Gateway from backend'"
echo ""
echo "# Habilitar firewall"
echo "sudo ufw enable"
echo ""
echo "# Verificar reglas"
echo "sudo ufw status numbered"
echo ""

echo "5️⃣ Archivo .env.production para microservicios..."
echo ""
echo "Crea el archivo Microservicios/.env.production con este contenido:"
echo ""
cat << EOF
# =========================================================
# PRODUCCIÓN - Microservicios HeartGuard
# Backend: $BACKEND_IP
# Microservicios: $MICROSERVICES_IP
# =========================================================

# --- API Key para comunicación interna ---
INTERNAL_API_KEY=390013313c6a189bdda05ae90274990af7a8c5e76ce448fb1ae32225254516f1

# --- PostgreSQL (SSL HABILITADO) ---
DATABASE_URL=postgresql://heartguard_app:Yj01Q8dJQ+Nif3pQ8+t5Sd52BzFG5TFp@$BACKEND_IP:5432/heartguard?sslmode=require

# --- Redis (TLS HABILITADO) ---
REDIS_URL=rediss://:75674a5b7adcabc7822812cb56d90768@$BACKEND_IP:6380/0
REDIS_TLS_ENABLED=true

# --- Backend Configuration ---
BACKEND_INSTANCE_HOST=$BACKEND_IP
BACKEND_HTTPS_URL=https://admin.heartguard.live

# --- Security ---
REQUIRE_API_KEY=true
SSL_VERIFY=false

# --- JWT (mismo que backend) ---
JWT_SECRET=3iKrvQlWmvFIClfczNN0Qe0bcg64DrLUH7BXsFeHnvM=

# --- RabbitMQ ---
RABBITMQ_HOST=rabbitmq
RABBITMQ_DEFAULT_PASS=HG_RabbitMQ_2025_Secure!

# --- Service Ports ---
GATEWAY_PORT=5000
AUTH_PORT=5001
ORGANIZATION_PORT=5002
USER_PORT=5003
PATIENT_PORT=5004
DEVICE_PORT=5005
INFLUX_SERVICE_PORT=5006
INFERENCE_PORT=5007
ALERT_PORT=5008
NOTIFICATION_PORT=5009
MEDIA_PORT=5010
AUDIT_PORT=5011
EOF

echo ""
echo "=" | tr '=' '-' | head -c 60 && echo ""
echo ""
echo "6️⃣ Comandos de despliegue..."
echo ""
echo "MÁQUINA 2 (Microservicios - $MICROSERVICES_IP):"
echo ""
echo "cd /root/HeartGuard/Microservicios"
echo "docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo ""

echo "=" | tr '=' '-' | head -c 60 && echo ""
echo ""
echo "✅ Configuración generada exitosamente"
echo ""
echo "📝 Próximos pasos:"
echo "  1. Configurar firewall en ambas máquinas (comandos arriba)"
echo "  2. Configurar PostgreSQL para conexiones remotas"
echo "  3. Copiar .env.production a la máquina de microservicios"
echo "  4. Desplegar microservicios"
echo "  5. Ejecutar pruebas de conectividad"
echo ""
echo "📚 Ver guía completa: docs/deployment/distributed_deployment.md"
