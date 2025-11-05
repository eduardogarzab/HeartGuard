@echo off
REM ============================================================================
REM HeartGuard Desktop App - Compilar y Ejecutar
REM ============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  HeartGuard Desktop App - Compilar y Ejecutar             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar si Maven está instalado
mvn -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Maven no está instalado o no está en el PATH
    echo.
    echo Por favor instala Maven desde:
    echo https://maven.apache.org/download.cgi
    echo.
    pause
    exit /b 1
)

echo [INFO] Limpiando proyecto...
call mvn clean

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Error al limpiar el proyecto
    pause
    exit /b 1
)

echo.
echo [INFO] Compilando proyecto...
call mvn package -DskipTests

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La compilación falló
    echo.
    echo Revisa los errores anteriores
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Compilación exitosa
echo.
echo ────────────────────────────────────────────────────────────
echo.
echo [INFO] Iniciando aplicación...
echo.

java -jar target\desktop-app-1.0.0.jar

if %errorlevel% neq 0 (
    echo.
    echo ────────────────────────────────────────────────────────────
    echo.
    echo [ERROR] La aplicación terminó con errores
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ────────────────────────────────────────────────────────────
echo.
echo [INFO] Aplicación cerrada correctamente
echo.
pause
