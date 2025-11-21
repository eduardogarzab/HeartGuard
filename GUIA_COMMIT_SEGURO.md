# Guía para Commit Seguro al Repositorio

## ✅ Archivos Seguros para Commit

Los siguientes archivos están limpios y NO contienen credenciales hardcodeadas:

### Desktop App
```
desktop-app/
├── src/main/java/              # ✅ Código Java sin credenciales
├── .env.example                # ✅ Plantilla sin valores reales
├── .gitignore                  # ✅ Incluye .env
├── pom.xml                     # ✅ Solo dependencias
├── launch.sh                   # ✅ Lee de .env
├── verify.sh                   # ✅ Scripts de utilidad
└── README.md                   # ✅ Documentación
```

### Backend Services
```
services/
├── realtime-data-generator/
│   ├── src/                    # ✅ Código Python sin IPs
│   ├── .env.example            # ✅ Plantilla sin valores
│   └── Makefile                # ✅ Scripts de build
├── gateway/
│   ├── src/                    # ✅ Código Python
│   └── .env.example            # ✅ Plantilla
└── [otros servicios]/          # ✅ Misma estructura
```

## ⚠️ Archivos que NO se Deben Commitear

Estos archivos están en `.gitignore` y contienen configuración específica del entorno:

```
# NO COMMITEAR:
desktop-app/.env                # Contiene IPs y tokens reales
services/**/.env                # Contiene configuración del servidor
*.log                           # Archivos de log
target/                         # Binarios compilados
.venv/                          # Entornos virtuales Python
__pycache__/                    # Cache de Python
```

## Verificación Pre-Commit

Antes de hacer commit, ejecuta:

```bash
# 1. Verificar que .env no está staged
git status | grep ".env$"
# Debe mostrar: nothing (vacío) o "Untracked"

# 2. Verificar archivos staged
git diff --cached --name-only

# 3. Buscar IPs hardcodeadas en código Java
grep -r "134.199.204.58" desktop-app/src/
# Debe mostrar: nothing (vacío)

# 4. Buscar tokens hardcodeados
grep -r "heartguard-dev-token" desktop-app/src/
# Debe mostrar: nothing (vacío)
```

## Estructura de Configuración Correcta

### ❌ INCORRECTO (valores hardcodeados):
```java
// NO HACER ESTO:
String url = "http://134.199.204.58:8086";
String token = "heartguard-dev-token-change-me";
```

### ✅ CORRECTO (desde .env):
```java
// HACER ESTO:
AppConfig config = AppConfig.getInstance();
String url = config.getInfluxdbUrl();       // Lee de .env
String token = config.getInfluxdbToken();   // Lee de .env
```

## Comandos Git Seguros

### 1. Agregar cambios (excluye .env automáticamente)
```bash
cd /root/HeartGuard
git add desktop-app/src/
git add desktop-app/.env.example
git add desktop-app/.gitignore
git add desktop-app/pom.xml
git add desktop-app/README.md
git add services/realtime-data-generator/src/
```

### 2. Verificar qué se va a commitear
```bash
git status
git diff --cached
```

### 3. Commit
```bash
git commit -m "feat: Add real-time vital signs monitoring with secure configuration

- Created AppConfig for centralized configuration management
- All credentials loaded from .env file (not hardcoded)
- Added InfluxDB integration for time-series data
- Real-time charts with auto-update every 10 seconds
- Proper .gitignore to exclude .env files
- Documentation updated with security best practices"
```

### 4. Push
```bash
git push origin main
```

## Archivo .gitignore Verificado

El archivo `desktop-app/.gitignore` incluye:

```gitignore
# Environment variables - DO NOT COMMIT
.env

# Compiled files
*.class
target/

# IDE
.idea/
*.iml
.vscode/

# Logs
*.log

# OS
.DS_Store
```

## Checklist Final Antes de Push

- [ ] ✅ No hay archivos `.env` en el commit
- [ ] ✅ No hay IPs hardcodeadas en código Java
- [ ] ✅ No hay tokens hardcodeados en código
- [ ] ✅ Archivo `.env.example` actualizado con plantilla
- [ ] ✅ `.gitignore` incluye `.env`
- [ ] ✅ Documentación actualizada
- [ ] ✅ `AppConfig.java` implementado correctamente
- [ ] ✅ Todos los servicios usan configuración desde .env

## Para Otros Desarrolladores

Cuando alguien clone el repositorio, deberá:

1. **Clonar**:
   ```bash
   git clone https://github.com/eduardogarzab/HeartGuard.git
   cd HeartGuard/desktop-app
   ```

2. **Crear su .env**:
   ```bash
   cp .env.example .env
   nano .env  # Editar con sus valores
   ```

3. **Compilar y ejecutar**:
   ```bash
   mvn clean package
   ./launch.sh
   ```

## Seguridad

### ✅ Implementado:
- Configuración externa en `.env`
- Sin credenciales en código fuente
- `.env` en `.gitignore`
- Tokens enmascarados en logs
- Validación de configuración requerida
- AppConfig centralizado

### ✅ Beneficios:
- ✅ Código limpio y seguro para GitHub público/privado
- ✅ Cada desarrollador tiene su propia configuración
- ✅ Fácil deployment en diferentes entornos
- ✅ No hay riesgo de exponer credenciales
- ✅ Cumple con mejores prácticas de seguridad

## Comandos de Verificación Rápida

```bash
# Verificar que no hay secrets en staged files
git diff --cached | grep -i "134.199.204.58"
git diff --cached | grep -i "heartguard-dev-token"

# Si alguno retorna resultados: NO HACER COMMIT
# Si ambos están vacíos: SEGURO PARA COMMIT ✅
```

## Resumen

**TODO LISTO PARA COMMIT SEGURO** ✅

- ✅ Código refactorizado para usar AppConfig
- ✅ Todas las IPs y tokens se leen desde .env
- ✅ .gitignore configurado correctamente
- ✅ Documentación actualizada
- ✅ Sin valores hardcodeados en el código

Puedes hacer commit y push sin preocupaciones.
