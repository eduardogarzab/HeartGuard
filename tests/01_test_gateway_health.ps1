# ============================================================
# PRUEBA 1: Health Check del Gateway
# ============================================================

Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  PRUEBA 1: Health Check del Gateway                       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host "`n🔍 Verificando conexión al gateway..." -ForegroundColor Yellow
Write-Host "URL: http://136.115.53.140:5000/health" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri "http://136.115.53.140:5000/health" -Method GET -ErrorAction Stop
    
    Write-Host "`n✅ RESULTADO: EXITOSO" -ForegroundColor Green
    Write-Host "`nDatos recibidos:" -ForegroundColor Yellow
    Write-Host "  Service: $($response.service)" -ForegroundColor White
    Write-Host "  Status: $($response.status)" -ForegroundColor White
    
    if ($response.service -eq "gateway" -and $response.status -eq "healthy") {
        Write-Host "`n🎉 Gateway está funcionando correctamente!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n⚠️  Gateway responde pero con valores inesperados" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "`n❌ RESULTADO: ERROR" -ForegroundColor Red
    Write-Host "`nDetalles del error:" -ForegroundColor Yellow
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    
    Write-Host "`n🔧 Posibles causas:" -ForegroundColor Yellow
    Write-Host "  1. El gateway no está corriendo en 136.115.53.140:5000" -ForegroundColor White
    Write-Host "  2. Hay un problema de red/firewall" -ForegroundColor White
    Write-Host "  3. La VM está apagada" -ForegroundColor White
    
    exit 1
}
