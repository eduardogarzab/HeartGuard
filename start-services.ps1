# Script para ejecutar los microservicios de HeartGuard

Write-Host "=== HeartGuard Microservices Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python no encontrado. Por favor instale Python 3.8 o superior." -ForegroundColor Red
    exit 1
}

# Directorio base
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$servicesDir = Join-Path $baseDir "services"

# Función para iniciar un servicio
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$ServicePath,
        [int]$Port
    )
    
    Write-Host ""
    Write-Host "Iniciando $ServiceName en puerto $Port..." -ForegroundColor Yellow
    
    if (-not (Test-Path $ServicePath)) {
        Write-Host "✗ Directorio no encontrado: $ServicePath" -ForegroundColor Red
        return $false
    }
    
    # Cambiar al directorio del servicio
    Set-Location $ServicePath
    
    # Verificar si existe .env
    if (Test-Path ".env") {
        Write-Host "✓ Archivo .env encontrado" -ForegroundColor Green
    } else {
        Write-Host "⚠ Archivo .env no encontrado, usando valores por defecto" -ForegroundColor Yellow
    }
    
    # Verificar requirements.txt
    if (Test-Path "requirements.txt") {
        Write-Host "Verificando dependencias..." -ForegroundColor Cyan
        pip install -r requirements.txt -q
    }
    
    # Iniciar el servicio en una nueva ventana de PowerShell
    $appPath = Join-Path "src" $ServiceName "app.py"
    $env:FLASK_APP = $appPath
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ServicePath'; `$env:FLASK_APP='$appPath'; flask run --host=0.0.0.0 --port=$Port"
    
    Write-Host "✓ $ServiceName iniciado en http://localhost:$Port" -ForegroundColor Green
    return $true
}

# Iniciar Auth Service
$authPath = Join-Path $servicesDir "auth"
Start-Service -ServiceName "auth" -ServicePath $authPath -Port 5001

Start-Sleep -Seconds 3

# Iniciar Gateway Service
$gatewayPath = Join-Path $servicesDir "gateway"
Start-Service -ServiceName "gateway" -ServicePath $gatewayPath -Port 8000

# Volver al directorio base
Set-Location $baseDir

Write-Host ""
Write-Host "=== Servicios iniciados ===" -ForegroundColor Cyan
Write-Host "Auth Service:    http://localhost:5001" -ForegroundColor White
Write-Host "Gateway Service: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "Presione Ctrl+C en cada ventana para detener los servicios" -ForegroundColor Yellow
Write-Host ""
