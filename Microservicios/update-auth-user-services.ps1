# Script para actualizar auth_service y user_service con organización dinámica
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Actualizando Auth y User Services" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Cambiar al directorio de Microservicios
$microservicesPath = "d:\Usuarios\jeser\OneDrive\Documentos\UDEM\HeartGuard\Microservicios"
Set-Location $microservicesPath

Write-Host "`n1. Deteniendo servicios..." -ForegroundColor Yellow
docker-compose stop auth_service user_service

Write-Host "`n2. Reconstruyendo imágenes..." -ForegroundColor Yellow
docker-compose build auth_service user_service

Write-Host "`n3. Iniciando servicios..." -ForegroundColor Yellow
docker-compose up -d auth_service user_service

Write-Host "`n4. Esperando 10 segundos para que los servicios inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "`n5. Verificando estado de los servicios..." -ForegroundColor Yellow
docker-compose ps auth_service user_service

Write-Host "`n6. Mostrando logs de auth_service..." -ForegroundColor Yellow
docker-compose logs --tail=15 auth_service

Write-Host "`n7. Mostrando logs de user_service..." -ForegroundColor Yellow
docker-compose logs --tail=15 user_service

Write-Host "`n==================================" -ForegroundColor Green
Write-Host "Actualización completada!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

Write-Host "`nPrueba el frontend:" -ForegroundColor Cyan
Write-Host "1. Cierra sesión si ya estás logueado" -ForegroundColor White
Write-Host "2. Vuelve a hacer login" -ForegroundColor White
Write-Host "3. La organización se obtendrá automáticamente" -ForegroundColor White
Write-Host "4. Navega a 'Usuarios' para ver los usuarios de TU organización" -ForegroundColor White

Write-Host "`nPara ver logs en tiempo real:" -ForegroundColor Cyan
Write-Host "docker-compose logs -f auth_service user_service" -ForegroundColor White
