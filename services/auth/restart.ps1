# Script para reiniciar el servicio de Auth limpiando caché
Write-Host "Limpiando cache de Python..." -ForegroundColor Yellow
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Write-Host "Iniciando servicio Auth..." -ForegroundColor Green
$env:FLASK_APP="src\auth\app.py"
$env:FLASK_DEBUG="1"
flask run --host=0.0.0.0 --port=5001
