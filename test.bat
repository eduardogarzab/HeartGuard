@echo off
echo ========================================
echo HeartGuard - Prueba del Sistema (Windows)
echo ========================================

echo.
echo Verificando que el backend este corriendo...
curl -s http://localhost:8080/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Backend no esta corriendo en localhost:8080
    echo.
    echo Para iniciar el sistema:
    echo   cd backend
    echo   docker-compose up -d
    echo.
    pause
    exit /b 1
)
echo OK - Backend verificado

echo.
echo ========================================
echo Probando endpoints del sistema...
echo ========================================

echo.
echo 1. Probando endpoint raiz...
curl -s http://localhost:8080/
if %errorlevel% equ 0 (
    echo OK - Backend funcionando
) else (
    echo ERROR - No se pudo conectar al backend
)

echo.
echo 2. Probando login...
curl -s -X POST http://localhost:8080/api/v1/login -H "Content-Type: application/json" -d "{\"username\": \"maria_admin\", \"password\": \"admin123\"}"
if %errorlevel% equ 0 (
    echo OK - Login exitoso
) else (
    echo ERROR - Fallo en login
)

echo.
echo 3. Probando listar colonias...
curl -s http://localhost:8080/api/v1/colonias
if %errorlevel% equ 0 (
    echo OK - Colonias listadas
) else (
    echo ERROR - Fallo al listar colonias
)

echo.
echo 4. Probando listar familias...
curl -s http://localhost:8080/api/v1/familias
if %errorlevel% equ 0 (
    echo OK - Familias listadas
) else (
    echo ERROR - Fallo al listar familias
)

echo.
echo 5. Probando listar usuarios...
curl -s http://localhost:8080/api/v1/usuarios
if %errorlevel% equ 0 (
    echo OK - Usuarios listados
) else (
    echo ERROR - Fallo al listar usuarios
)

echo.
echo ========================================
echo Resumen de Pruebas
echo ========================================
echo.
echo Servicios disponibles:
echo   - Backend Go: http://localhost:8080
echo   - PostgreSQL: localhost:5432
echo   - InfluxDB: http://localhost:8086
echo   - Redis: localhost:6379
echo.
echo Para mas pruebas, abre el navegador en:
echo   http://localhost:8080/
echo.
echo O usa Postman para probar la API completa
echo.
echo Si curl no funciona, usa Git Bash con: ./test.sh
echo.
pause
