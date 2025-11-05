@echo off
REM ============================================================================
REM HeartGuard Desktop App - Script de Ejecución para Windows
REM ============================================================================

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  HeartGuard Desktop App - Iniciando...                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Verificar si Java está instalado
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Java no está instalado o no está en el PATH
    echo.
    echo Por favor instala Java 11 o superior desde:
    echo https://adoptium.net/
    echo.
    pause
    exit /b 1
)

REM Verificar si el JAR existe
if not exist "target\desktop-app-1.0.0.jar" (
    echo [WARNING] El archivo JAR no existe. Compilando proyecto...
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
    
    echo [INFO] Compilando proyecto con Maven...
    call mvn clean package -DskipTests
    
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] La compilación falló
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Compilación exitosa
    echo.
)

REM Ejecutar la aplicación
echo [INFO] Iniciando HeartGuard Desktop App...
echo.
echo ────────────────────────────────────────────────────────────
echo.

java -jar target\desktop-app-1.0.0.jar

REM Capturar el código de salida
if %errorlevel% neq 0 (
    echo.
    echo ────────────────────────────────────────────────────────────
    echo.
    echo [ERROR] La aplicación terminó con errores (código: %errorlevel%)
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
