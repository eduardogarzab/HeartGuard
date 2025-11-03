# Script para compilar y ejecutar la aplicación Java

Write-Host "=== HeartGuard Desktop App Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Java
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "✓ Java encontrado: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Java no encontrado. Por favor instale Java 11 o superior." -ForegroundColor Red
    exit 1
}

# Verificar Maven
try {
    $mavenVersion = mvn --version 2>&1 | Select-String "Apache Maven"
    Write-Host "✓ Maven encontrado: $mavenVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Maven no encontrado. Por favor instale Apache Maven." -ForegroundColor Red
    exit 1
}

# Directorio de la aplicación
$appDir = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "desktop-app"

if (-not (Test-Path $appDir)) {
    Write-Host "✗ Directorio desktop-app no encontrado" -ForegroundColor Red
    exit 1
}

Set-Location $appDir

Write-Host ""
Write-Host "Compilando aplicación..." -ForegroundColor Yellow
mvn clean package -q

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Compilación exitosa" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ejecutando aplicación..." -ForegroundColor Yellow
    Write-Host ""
    
    # Buscar el JAR con dependencias
    $jarFile = Get-ChildItem -Path "target" -Filter "*-shaded.jar" | Select-Object -First 1
    if (-not $jarFile) {
        $jarFile = Get-ChildItem -Path "target" -Filter "desktop-app-*.jar" | Where-Object { $_.Name -notlike "*-original.jar" } | Select-Object -First 1
    }
    
    if ($jarFile) {
        java -jar $jarFile.FullName
    } else {
        Write-Host "✗ No se encontró el archivo JAR" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ Error en la compilación" -ForegroundColor Red
    exit 1
}
