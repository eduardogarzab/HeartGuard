#!/bin/bash
echo "🔍 VERIFICACIÓN COMPLETA DEL SISTEMA DE PRODUCCIÓN"
echo "=================================================="
echo ""

echo "1️⃣ Estado de Contenedores Docker"
docker ps --filter "name=heartguard" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "2️⃣ Healthchecks"
for container in heartguard-postgres heartguard-redis heartguard-backend-1 heartguard-nginx-1; do
  status=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "no health")
  echo "  $container: $status"
done
echo ""

echo "3️⃣ SSL/TLS PostgreSQL"
docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;" -t 2>/dev/null | xargs
echo ""

echo "4️⃣ TLS Redis"
REDIS_PASS=$(grep REDIS_PASSWORD /root/HeartGuard/.env.production | cut -d= -f2)
docker exec heartguard-redis redis-cli --tls --insecure \
  -p 6380 \
  -a "$REDIS_PASS" PING 2>&1 | grep -q "PONG" && echo "✅ PONG" || echo "❌ Error conectando a Redis"
echo ""

echo "5️⃣ Certificado HTTPS"
curl -sI https://admin.heartguard.live | grep -E "HTTP|Server|Strict-Transport"
echo ""

echo "6️⃣ Certificado Let's Encrypt"
docker run --rm -v heartguard_certbot-etc:/etc/letsencrypt alpine sh -c "
  if [ -f /etc/letsencrypt/live/admin.heartguard.live/fullchain.pem ]; then
    openssl x509 -in /etc/letsencrypt/live/admin.heartguard.live/fullchain.pem -noout -dates | grep notAfter
  else
    echo 'Certificado no encontrado'
  fi
" 2>/dev/null
echo ""

echo "7️⃣ Firewall UFW"
ufw status | grep -E "Status|80|443"
echo ""

echo "8️⃣ iptables DOCKER-USER"
iptables -L DOCKER-USER -n | grep -E "tcp dpt:80|tcp dpt:443" | head -2
echo ""

echo "9️⃣ Timer de Renovación"
systemctl is-active certbot-renew.timer
systemctl list-timers certbot-renew.timer --no-pager | grep -A1 "certbot-renew"
echo ""

echo "🔟 IP Reservada"
ip addr show eth0 | grep "134.199.133.125" && echo "✅ IP Reservada activa" || echo "❌ IP Reservada no activa"
echo ""

echo "1️⃣1️⃣ DNS Resolution"
dig +short admin.heartguard.live
echo ""

echo "✅ VERIFICACIÓN COMPLETA"
echo "Fecha: $(date)"
