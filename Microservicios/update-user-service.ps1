# Script para actualizar y reiniciar el user_service
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Actualizando User Service" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Cambiar al directorio de Microservicios
$microservicesPath = "d:\Usuarios\jeser\OneDrive\Documentos\UDEM\HeartGuard\Microservicios"
Set-Location $microservicesPath

Write-Host "`n1. Deteniendo user_service..." -ForegroundColor Yellow
docker-compose stop user_service

Write-Host "`n2. Reconstruyendo imagen del user_service..." -ForegroundColor Yellow
docker-compose build user_service

Write-Host "`n3. Iniciando user_service..." -ForegroundColor Yellow
docker-compose up -d user_service

Write-Host "`n4. Esperando 5 segundos para que el servicio inicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n5. Verificando estado del servicio..." -ForegroundColor Yellow
docker-compose ps user_service

Write-Host "`n6. Mostrando últimos logs..." -ForegroundColor Yellow
docker-compose logs --tail=20 user_service

Write-Host "`n==================================" -ForegroundColor Green
Write-Host "Actualización completada!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

Write-Host "`nPara ver logs en tiempo real:" -ForegroundColor Cyan
Write-Host "docker-compose logs -f user_service" -ForegroundColor White

Write-Host "`nAhora puedes probar el frontend en:" -ForegroundColor Cyan
Write-Host "http://localhost:8000" -ForegroundColor White
