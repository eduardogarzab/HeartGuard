#!/bin/bash

# =========================================================
# HeartGuard - Test Script para Vista Web
# =========================================================

echo "🏥 HeartGuard - Probando Vista Web del Superadministrador"
echo "=========================================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_step() {
    echo -e "\n${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Verificar que Docker esté corriendo
print_step "Verificando Docker..."
if ! docker info > /dev/null 2>&1; then
    print_error "Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi
print_success "Docker está corriendo"

# Verificar que los archivos necesarios existan
print_step "Verificando archivos del proyecto..."
required_files=(
    "main.go"
    "crud.go"
    "monitoring.go"
    "init.sql"
    "docker-compose.yml"
    "Dockerfile"
    "templates/index.html"
    "static/css/style.css"
    "static/js/app.js"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo faltante: $file"
        exit 1
    fi
done
print_success "Todos los archivos necesarios están presentes"

# Construir y levantar los servicios
print_step "Construyendo y levantando servicios Docker..."
docker-compose down > /dev/null 2>&1
docker-compose build --no-cache
if [ $? -ne 0 ]; then
    print_error "Error construyendo los servicios Docker"
    exit 1
fi

docker-compose up -d
if [ $? -ne 0 ]; then
    print_error "Error levantando los servicios Docker"
    exit 1
fi
print_success "Servicios Docker levantados correctamente"

# Esperar a que los servicios estén listos
print_step "Esperando a que los servicios estén listos..."
sleep 10

# Verificar que los servicios estén corriendo
print_step "Verificando estado de los servicios..."
services=("postgres" "redis" "influxdb" "backend-go")
for service in "${services[@]}"; do
    if docker-compose ps | grep -q "$service.*Up"; then
        print_success "Servicio $service está corriendo"
    else
        print_error "Servicio $service no está corriendo"
        docker-compose logs "$service"
        exit 1
    fi
done

# Verificar conectividad de la API
print_step "Verificando conectividad de la API..."
sleep 5

# Test 1: Verificar que el backend responda
print_info "Probando endpoint principal..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/api)
if [ "$response" = "200" ]; then
    print_success "Backend respondiendo correctamente"
else
    print_error "Backend no responde (HTTP $response)"
    print_info "Logs del backend:"
    docker-compose logs backend-go | tail -20
    exit 1
fi

# Test 2: Verificar que la vista web cargue
print_info "Probando vista web..."
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/)
if [ "$response" = "200" ]; then
    print_success "Vista web cargando correctamente"
else
    print_error "Vista web no carga (HTTP $response)"
    exit 1
fi

# Test 3: Verificar archivos estáticos
print_info "Probando archivos estáticos..."
static_files=("/static/css/style.css" "/static/js/app.js")
for file in "${static_files[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080$file")
    if [ "$response" = "200" ]; then
        print_success "Archivo estático $file cargando correctamente"
    else
        print_error "Archivo estático $file no carga (HTTP $response)"
    fi
done

# Test 4: Verificar login (debe fallar sin credenciales)
print_info "Probando endpoint de login..."
response=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -w "%{http_code}" \
    http://localhost:8080/admin/login)
if [ "$response" = "401" ] || [ "$response" = "400" ]; then
    print_success "Endpoint de login funcionando (rechaza credenciales incorrectas)"
else
    print_error "Endpoint de login no funciona correctamente (HTTP $response)"
fi

# Test 5: Verificar login con credenciales correctas
print_info "Probando login con credenciales del superadmin..."
login_response=$(curl -s -X POST -H "Content-Type: application/json" \
    -d '{"email":"admin@heartguard.com","password":"admin123"}' \
    http://localhost:8080/admin/login)

if echo "$login_response" | grep -q '"success":true'; then
    print_success "Login con superadmin exitoso"
    
    # Extraer token para pruebas adicionales
    token=$(echo "$login_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    # Test 6: Verificar dashboard
    print_info "Probando endpoint de dashboard..."
    dashboard_response=$(curl -s -H "Authorization: Bearer $token" \
        http://localhost:8080/admin/dashboard)
    
    if echo "$dashboard_response" | grep -q '"success":true'; then
        print_success "Dashboard funcionando correctamente"
    else
        print_error "Dashboard no funciona correctamente"
    fi
    
    # Test 7: Verificar usuarios
    print_info "Probando endpoint de usuarios..."
    users_response=$(curl -s -H "Authorization: Bearer $token" \
        http://localhost:8080/admin/usuarios)
    
    if echo "$users_response" | grep -q '"success":true'; then
        print_success "Endpoint de usuarios funcionando correctamente"
    else
        print_error "Endpoint de usuarios no funciona correctamente"
    fi
    
else
    print_error "Login con superadmin falló"
    print_info "Respuesta del login: $login_response"
fi

# Mostrar información de acceso
print_step "Información de Acceso"
echo "=========================================================="
print_info "🌐 Vista Web: http://localhost:8080"
print_info "🔗 API REST: http://localhost:8080/admin"
print_info "📊 InfluxDB: http://localhost:8086"
print_info "🗄️ PostgreSQL: localhost:5432"
print_info "🔴 Redis: localhost:6379"
echo ""
print_info "👤 Credenciales del Superadmin:"
print_info "   Email: admin@heartguard.com"
print_info "   Password: admin123"
echo ""
print_info "📋 Comandos útiles:"
print_info "   Ver logs: docker-compose logs -f"
print_info "   Parar servicios: docker-compose down"
print_info "   Reiniciar: docker-compose restart"
echo ""

# Verificar puertos
print_step "Verificando puertos..."
ports=("8080:Backend" "5432:PostgreSQL" "6379:Redis" "8086:InfluxDB")
for port_info in "${ports[@]}"; do
    port=$(echo "$port_info" | cut -d: -f1)
    service=$(echo "$port_info" | cut -d: -f2)
    if netstat -an 2>/dev/null | grep -q ":$port " || lsof -i :$port >/dev/null 2>&1; then
        print_success "Puerto $port ($service) está en uso"
    else
        print_warning "Puerto $port ($service) no está en uso"
    fi
done

print_step "¡Pruebas completadas!"
echo "=========================================================="
print_success "🎉 La vista web del superadministrador está lista!"
print_info "Abre http://localhost:8080 en tu navegador para acceder al dashboard"
print_info "Usa las credenciales del superadmin para iniciar sesión"

# Opción para abrir el navegador automáticamente
if command -v open >/dev/null 2>&1; then
    echo ""
    read -p "¿Quieres abrir el navegador automáticamente? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open http://localhost:8080
    fi
elif command -v xdg-open >/dev/null 2>&1; then
    echo ""
    read -p "¿Quieres abrir el navegador automáticamente? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open http://localhost:8080
    fi
fi
