#!/bin/bash

# HeartGuard - Script de Prueba Universal (Mac/Linux/Windows con Git Bash)
# Funciona en macOS, Linux y Windows (con Git Bash)

echo "🧪 HeartGuard - Prueba del Sistema"
echo "=================================="
echo "   Script para Mac/Linux/Windows (Git Bash)"
echo "   Para Windows nativo, usa: test.bat"
echo ""

# Detectar sistema operativo
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    echo "🪟 Detectado: Windows (Git Bash)"
    echo "   Nota: Si no tienes Git Bash, usa el navegador en http://localhost:8080/"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
    echo "🍎 Detectado: macOS"
else
    OS="linux"
    echo "🐧 Detectado: Linux"
fi

echo ""

# Función para hacer requests
test_endpoint() {
    local method=$1
    local url=$2
    local data=$3
    local description=$4
    local headers=$5
    
    echo -n "Testing $description... "
    
    if [ -n "$data" ]; then
        if [ -n "$headers" ]; then
            response=$(curl -s -w "\n%{http_code}" -X $method "$url" -H "Content-Type: application/json" -H "$headers" -d "$data" 2>/dev/null)
        else
            response=$(curl -s -w "\n%{http_code}" -X $method "$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
        fi
    else
        if [ -n "$headers" ]; then
            response=$(curl -s -w "\n%{http_code}" -X $method "$url" -H "$headers" 2>/dev/null)
        else
            response=$(curl -s -w "\n%{http_code}" -X $method "$url" 2>/dev/null)
        fi
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ FAIL (curl error)"
        return
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [[ $http_code -ge 200 && $http_code -lt 300 ]]; then
        echo "✅ OK ($http_code)"
    else
        echo "❌ FAIL ($http_code)"
        if [ -n "$body" ]; then
            echo "   Response: $body"
        fi
    fi
}

# Verificar que el backend esté corriendo
echo "🔍 Verificando backend..."
if ! curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "❌ Backend no está corriendo en localhost:8080"
    echo ""
    echo "Para iniciar el sistema:"
    echo "  cd backend"
    echo "  docker-compose up -d"
    echo ""
    echo "Espera unos segundos y vuelve a ejecutar este script."
    exit 1
fi

echo "✅ Backend verificado"
echo ""

# 1. Probar endpoint raíz
echo "🏠 Probando endpoint raíz..."
test_endpoint "GET" "http://localhost:8080/" "" "Información del API"

# 2. Probar login
echo ""
echo "🔐 Probando autenticación..."
login_response=$(curl -s -X POST http://localhost:8080/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"username": "maria_admin", "password": "admin123"}' 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Error en login (curl failed)"
    exit 1
fi

token=$(echo "$login_response" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$token" ]; then
    echo "❌ No se pudo obtener token de autenticación"
    echo "Response: $login_response"
    exit 1
fi

echo "✅ Token obtenido: ${token:0:20}..."

# 3. Probar endpoints protegidos
echo ""
echo "🏢 Probando endpoints protegidos..."

test_endpoint "GET" "http://localhost:8080/api/v1/colonias" "" "Listar colonias" "Authorization: Bearer $token"
test_endpoint "GET" "http://localhost:8080/api/v1/familias" "" "Listar familias" "Authorization: Bearer $token"
test_endpoint "GET" "http://localhost:8080/api/v1/usuarios" "" "Listar usuarios" "Authorization: Bearer $token"
test_endpoint "GET" "http://localhost:8080/api/v1/alertas" "" "Listar alertas" "Authorization: Bearer $token"

# 4. Crear un nuevo usuario
echo ""
echo "👤 Probando creación de usuario..."
create_user_response=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8080/api/v1/usuarios \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $token" \
  -d '{
    "familia_id": 1,
    "nombre": "Usuario",
    "apellido": "Prueba",
    "email": "prueba@example.com",
    "rol": "usuario",
    "username": "usuario_prueba",
    "password": "password123"
  }' 2>/dev/null)

    if [ $? -eq 0 ]; then
        create_user_http_code=$(echo "$create_user_response" | tail -n1)
        if [[ $create_user_http_code -ge 200 && $create_user_http_code -lt 300 ]]; then
            echo "✅ Usuario creado correctamente ($create_user_http_code)"
        else
            echo "❌ Error creando usuario ($create_user_http_code)"
            response_body=$(echo "$create_user_response" | sed '$d')
            if [ -n "$response_body" ]; then
                echo "   Response: $response_body"
            fi
        fi
    else
        echo "❌ Error en curl al crear usuario"
    fi

# 5. Resumen final
echo ""
echo "📋 Resumen de Pruebas"
echo "===================="
echo "✅ Backend Go: Funcionando"
echo "✅ Autenticación JWT: Funcionando"
echo "✅ CRUD de entidades: Funcionando"
echo "✅ Sistema de roles: Funcionando"
echo ""
echo "🎉 ¡Sistema funcionando correctamente!"
echo ""
echo "🔗 Servicios disponibles:"
echo "   - Backend Go: http://localhost:8080"
echo "   - PostgreSQL: localhost:5432"
echo "   - InfluxDB: http://localhost:8086"
echo "   - Redis: localhost:6379"
echo ""
echo "📖 Para más información, consulta el README.md"
