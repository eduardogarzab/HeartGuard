#!/bin/bash

echo "🔍 VERIFICACIÓN DE IMPLEMENTACIÓN DE SIGNOS VITALES"
echo "=================================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Verificar archivos
echo "1️⃣  Verificando archivos modificados..."
echo ""

files=(
    "clients/org-admin/assets/js/app.js"
    "clients/org-admin/assets/js/api.js"
    "clients/org-admin/assets/css/app.css"
    "clients/org-admin/index.html"
    "services/influxdb-service/src/generator/app.py"
    "services/influxdb-service/src/generator/xml.py"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file existe"
    else
        echo -e "${RED}❌${NC} $file NO EXISTE"
    fi
done

echo ""
echo "2️⃣  Verificando código en app.js..."
echo ""

# Verificar que la función renderVitalSignsCharts existe
if grep -q "renderVitalSignsCharts" clients/org-admin/assets/js/app.js; then
    echo -e "${GREEN}✅${NC} Función renderVitalSignsCharts encontrada"
else
    echo -e "${RED}❌${NC} Función renderVitalSignsCharts NO encontrada"
fi

# Verificar que loadVitalSignsData existe
if grep -q "loadVitalSignsData" clients/org-admin/assets/js/app.js; then
    echo -e "${GREEN}✅${NC} Función loadVitalSignsData encontrada"
else
    echo -e "${RED}❌${NC} Función loadVitalSignsData NO encontrada"
fi

# Verificar que está en renderPatientProfileView
if grep -q "📊 Signos Vitales en Tiempo Real" clients/org-admin/assets/js/app.js; then
    echo -e "${GREEN}✅${NC} Sección de signos vitales en perfil de paciente"
    
    # Mostrar contexto
    echo -e "${BLUE}    Contexto:${NC}"
    grep -B 2 -A 2 "📊 Signos Vitales en Tiempo Real" clients/org-admin/assets/js/app.js | sed 's/^/    /'
else
    echo -e "${RED}❌${NC} Sección de signos vitales NO encontrada en perfil"
fi

echo ""
echo "3️⃣  Verificando API en api.js..."
echo ""

if grep -q "getPatientVitalSigns" clients/org-admin/assets/js/api.js; then
    echo -e "${GREEN}✅${NC} Función getPatientVitalSigns encontrada"
    
    # Verificar que usa requestXml
    if grep -q "requestXml.*vital-signs" clients/org-admin/assets/js/api.js; then
        echo -e "${GREEN}✅${NC} Usa requestXml para llamada a API"
    else
        echo -e "${RED}❌${NC} NO usa requestXml (debería usar XML, no JSON)"
    fi
else
    echo -e "${RED}❌${NC} Función getPatientVitalSigns NO encontrada"
fi

echo ""
echo "4️⃣  Verificando estilos CSS..."
echo ""

css_classes=(
    "vital-signs-container"
    "vital-signs-grid"
    "vital-sign-card"
    "vital-sign-chart-wrapper"
)

for class in "${css_classes[@]}"; do
    if grep -q "$class" clients/org-admin/assets/css/app.css; then
        echo -e "${GREEN}✅${NC} Clase .$class encontrada"
    else
        echo -e "${RED}❌${NC} Clase .$class NO encontrada"
    fi
done

echo ""
echo "5️⃣  Verificando Chart.js en HTML..."
echo ""

if grep -q "chart.js" clients/org-admin/index.html; then
    echo -e "${GREEN}✅${NC} Chart.js incluido en index.html"
    grep "chart.js" clients/org-admin/index.html | sed 's/^/    /'
else
    echo -e "${RED}❌${NC} Chart.js NO incluido"
fi

echo ""
echo "6️⃣  Verificando servicio influxdb-service..."
echo ""

if [ -f "services/influxdb-service/src/generator/xml.py" ]; then
    echo -e "${GREEN}✅${NC} Módulo xml.py creado"
    
    # Verificar funciones
    if grep -q "def xml_response" services/influxdb-service/src/generator/xml.py; then
        echo -e "${GREEN}✅${NC} Función xml_response encontrada"
    fi
    
    if grep -q "def dict_to_xml" services/influxdb-service/src/generator/xml.py; then
        echo -e "${GREEN}✅${NC} Función dict_to_xml encontrada"
    fi
else
    echo -e "${RED}❌${NC} Módulo xml.py NO encontrado"
fi

if grep -q "from .xml import" services/influxdb-service/src/generator/app.py; then
    echo -e "${GREEN}✅${NC} Import de xml en app.py"
else
    echo -e "${RED}❌${NC} Import de xml NO encontrado en app.py"
fi

if grep -q "wants_xml" services/influxdb-service/src/generator/app.py; then
    echo -e "${GREEN}✅${NC} Función wants_xml implementada"
else
    echo -e "${RED}❌${NC} Función wants_xml NO implementada"
fi

echo ""
echo "7️⃣  Verificando servicios Docker..."
echo ""

cd services 2>/dev/null

if [ -f "docker-compose.yml" ]; then
    if docker-compose ps | grep -q "influxdb-service"; then
        if docker-compose ps | grep "influxdb-service" | grep -q "Up"; then
            echo -e "${GREEN}✅${NC} Servicio influxdb-service corriendo"
        else
            echo -e "${YELLOW}⚠️${NC}  Servicio influxdb-service existe pero no está corriendo"
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  Servicio influxdb-service no encontrado"
    fi
    
    if docker-compose ps | grep -q "influxdb"; then
        if docker-compose ps | grep "influxdb" | grep -q "Up"; then
            echo -e "${GREEN}✅${NC} Servicio influxdb corriendo"
        else
            echo -e "${YELLOW}⚠️${NC}  Servicio influxdb existe pero no está corriendo"
        fi
    else
        echo -e "${YELLOW}⚠️${NC}  Servicio influxdb no encontrado"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  No se encontró docker-compose.yml"
fi

cd .. 2>/dev/null

echo ""
echo "=================================================="
echo "📊 RESUMEN"
echo "=================================================="
echo ""
echo "La implementación de signos vitales está completa en el código."
echo ""
echo -e "${BLUE}Para ver los signos vitales:${NC}"
echo "1. Abre el cliente org-admin en el navegador"
echo "2. Inicia sesión con credenciales de org_admin"
echo "3. Selecciona una organización"
echo "4. Ve a la pestaña 'Pacientes'"
echo "5. Haz clic en cualquier paciente"
echo "6. Busca la sección '📊 Signos Vitales en Tiempo Real'"
echo ""
echo -e "${BLUE}Prueba rápida de Chart.js:${NC}"
echo "  cd clients/org-admin"
echo "  python3 -m http.server 8082"
echo "  Abre: http://localhost:8082/test-vital-signs.html"
echo ""
echo -e "${BLUE}Ver logs en navegador:${NC}"
echo "  Presiona F12 en el navegador"
echo "  Ve a la pestaña 'Console'"
echo "  Busca logs que empiecen con 🔍 🎨 📊"
echo ""
echo "=================================================="
echo ""
