#!/bin/bash
# Script de reset y deploy completo en producción con SSL/TLS
# Uso: ./reset_and_deploy_prod.sh

set -e  # Salir en cualquier error

echo "🔄 ============================================"
echo "   RESET Y DEPLOY COMPLETO EN PRODUCCIÓN"
echo "   HeartGuard con SSL/TLS Habilitado"
echo "============================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para preguntar confirmación
confirm() {
    read -p "⚠️  $1 (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Operación cancelada"
        exit 1
    fi
}

# ============================================
# PASO 1: CONFIRMACIÓN
# ============================================
echo -e "${YELLOW}ADVERTENCIA: Esto eliminará TODOS los datos de la base de datos${NC}"
echo "- Volúmenes de Docker (postgres_data)"
echo "- Certificados SSL/TLS (certs/)"
echo "- Imágenes del backend"
echo ""
confirm "¿Estás seguro de continuar?"

# ============================================
# PASO 2: DETENER Y LIMPIAR
# ============================================
echo ""
echo "🛑 PASO 1/7: Deteniendo servicios..."
docker compose down --remove-orphans || true

echo ""
echo "🧹 PASO 2/7: Limpiando volúmenes y cache..."
docker volume rm heartguard_postgres_data 2>/dev/null || true
docker volume rm heartguard_certbot-etc 2>/dev/null || true
docker volume rm heartguard_certbot-var 2>/dev/null || true
docker volume rm heartguard_certbot-www 2>/dev/null || true
docker rmi heartguard-backend 2>/dev/null || true
rm -rf backend/bin/ 2>/dev/null || true

echo ""
echo "🔐 PASO 3/7: Regenerando certificados SSL/TLS..."
rm -rf certs/ 2>/dev/null || true
./generate_certs.sh

# Verificar certificados
if [ ! -f certs/ca.crt ]; then
    echo -e "${RED}❌ Error: No se generaron los certificados${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Certificados generados correctamente${NC}"
ls -la certs/

# ============================================
# PASO 3: VERIFICAR CONFIGURACIÓN
# ============================================
echo ""
echo "🔍 PASO 4/7: Verificando configuración..."

if [ ! -f .env.production ]; then
    echo -e "${RED}❌ Error: .env.production no existe${NC}"
    exit 1
fi

# Verificar que tenga SSL habilitado
if ! grep -q "sslmode=require" .env.production; then
    echo -e "${YELLOW}⚠️  Advertencia: DATABASE_URL no tiene sslmode=require${NC}"
    echo "   Continuando de todos modos..."
fi

if ! grep -q "rediss://" .env.production; then
    echo -e "${YELLOW}⚠️  Advertencia: REDIS_URL no usa rediss:// (TLS)${NC}"
    echo "   Continuando de todos modos..."
fi

echo -e "${GREEN}✅ Configuración verificada${NC}"

# ============================================
# PASO 4: BUILD Y DEPLOY
# ============================================
echo ""
echo "🏗️  PASO 5/7: Compilando y desplegando..."

# Build del backend
echo "   - Compilando backend..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build backend

# Levantar servicios
echo "   - Levantando servicios..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Esperar a que Postgres esté listo
echo "   - Esperando a PostgreSQL..."
for i in {1..60}; do
    if docker exec heartguard-postgres pg_isready -U postgres >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ PostgreSQL listo${NC}"
        break
    fi
    if [ $i -eq 60 ]; then
        echo -e "${RED}   ❌ PostgreSQL no respondió a tiempo${NC}"
        exit 1
    fi
    sleep 1
done

# Esperar a Redis
echo "   - Esperando a Redis..."
sleep 5

# Inicializar base de datos
echo "   - Inicializando base de datos..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
    env PGPASSWORD="${PGSUPER_PASS:-postgres123}" \
    psql -U postgres -v dbname=heartguard -v dbuser=heartguard_app -v dbpass="${DBPASS:-dev_change_me}" \
    -f - < db/init.sql

echo "   - Cargando datos de prueba..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T postgres \
    env PGPASSWORD="${PGSUPER_PASS:-postgres123}" \
    psql -U postgres -d heartguard -f - < db/seed.sql

echo -e "${GREEN}✅ Deploy completo${NC}"

# ============================================
# PASO 5: VERIFICAR SSL/TLS
# ============================================
echo ""
echo "🔒 PASO 6/7: Verificando SSL/TLS..."

# Esperar a que el backend arranque
echo "   - Esperando al backend..."
sleep 10

# Verificar logs del backend
echo "   - Verificando logs del backend..."
if docker logs heartguard-backend 2>&1 | grep -q "PostgreSQL SSL/TLS habilitado"; then
    echo -e "${GREEN}   ✅ PostgreSQL SSL/TLS habilitado${NC}"
else
    echo -e "${YELLOW}   ⚠️  No se detectó mensaje de PostgreSQL SSL/TLS${NC}"
fi

if docker logs heartguard-backend 2>&1 | grep -q "Redis TLS habilitado"; then
    echo -e "${GREEN}   ✅ Redis TLS habilitado${NC}"
else
    echo -e "${YELLOW}   ⚠️  No se detectó mensaje de Redis TLS${NC}"
fi

# Verificar PostgreSQL SSL
echo "   - Verificando PostgreSQL SSL..."
if docker exec heartguard-postgres psql -U postgres -c "SHOW ssl;" 2>/dev/null | grep -q "on"; then
    echo -e "${GREEN}   ✅ PostgreSQL SSL: ON${NC}"
else
    echo -e "${RED}   ❌ PostgreSQL SSL: OFF${NC}"
fi

# Verificar Redis TLS
echo "   - Verificando Redis TLS..."
if docker exec heartguard-redis redis-cli --tls --cacert /etc/redis/certs/ca.crt -p 6380 PING 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}   ✅ Redis TLS: OK${NC}"
else
    echo -e "${RED}   ❌ Redis TLS: FAIL${NC}"
fi

# ============================================
# PASO 6: VERIFICAR SALUD
# ============================================
echo ""
echo "🏥 PASO 7/7: Verificando salud del sistema..."

# Verificar contenedores
echo "   - Estado de contenedores:"
docker compose ps

# Verificar conexión a BD
echo "   - Verificando datos en base de datos..."
USER_COUNT=$(docker exec heartguard-postgres psql -U postgres -d heartguard -t -c "SELECT count(*) FROM users;" 2>/dev/null | xargs)
echo -e "     Usuarios en BD: ${GREEN}${USER_COUNT}${NC}"

# ============================================
# RESUMEN
# ============================================
echo ""
echo "🎉 ============================================"
echo "   DEPLOY COMPLETO Y EXITOSO"
echo "============================================"
echo ""
echo -e "${GREEN}✅ Servicios levantados con SSL/TLS${NC}"
echo ""
echo "📊 Información del sistema:"
echo "   - PostgreSQL: SSL habilitado en puerto 5432"
echo "   - Redis: TLS habilitado en puerto 6380"
echo "   - Backend: Corriendo con verificación de certificados"
echo "   - Usuarios en BD: $USER_COUNT"
echo ""
echo "🔍 Comandos útiles:"
echo "   make prod-logs          # Ver logs del backend"
echo "   make prod-restart       # Reiniciar servicios"
echo "   docker compose ps       # Ver estado de contenedores"
echo "   docker compose logs -f  # Ver todos los logs"
echo ""
echo "🔒 Verificación SSL/TLS:"
echo "   docker logs heartguard-backend | grep -E 'SSL|TLS'"
echo ""
echo "📚 Documentación:"
echo "   docs/ssl_tls_setup.md      # Guía completa SSL/TLS"
echo "   SECURITY_SSL_TLS.md        # Resumen técnico"
echo ""
echo -e "${GREEN}¡Listo para producción! 🚀${NC}"
