@echo off
echo ========================================
echo HeartGuard - Prueba del Sistema (Windows)
echo ========================================

echo.
echo Verificando que el backend este corriendo...
powershell -Command "try { Invoke-RestMethod -Uri 'http://localhost:8080/' -Method Get | Out-Null; Write-Host 'Backend verificado' } catch { Write-Host 'ERROR: Backend no esta corriendo en localhost:8080'; Write-Host 'Por favor ejecuta: cd backend ^&^& docker-compose up -d'; pause; exit 1 }"

echo.
echo ========================================
echo Probando endpoints del sistema...
echo ========================================

echo.
echo 1. Probando endpoint raiz...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8080/' -Method Get; Write-Host 'OK - Backend funcionando'; Write-Host 'Version:' $response.version } catch { Write-Host 'ERROR:' $_.Exception.Message }"

echo.
echo 2. Probando login...
powershell -Command "try { $body = @{ username='maria_admin'; password='admin123' } | ConvertTo-Json; $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/login' -Method Post -Body $body -ContentType 'application/json'; Write-Host 'OK - Login exitoso'; Write-Host 'Token obtenido:' $response.token.Substring(0,20)... } catch { Write-Host 'ERROR en login:' $_.Exception.Message }"

echo.
echo 3. Probando listar colonias...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/colonias' -Method Get; Write-Host 'OK - Colonias listadas' } catch { Write-Host 'ERROR en colonias:' $_.Exception.Message }"

echo.
echo 4. Probando listar familias...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/familias' -Method Get; Write-Host 'OK - Familias listadas' } catch { Write-Host 'ERROR en familias:' $_.Exception.Message }"

echo.
echo 5. Probando listar usuarios...
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v1/usuarios' -Method Get; Write-Host 'OK - Usuarios listados' } catch { Write-Host 'ERROR en usuarios:' $_.Exception.Message }"

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
pause
