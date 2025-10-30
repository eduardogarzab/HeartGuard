@echo off
setlocal
cd /d "%~dp0"
echo [INFO] Deteniendo servicios...
docker-compose --env-file .env down
endlocal
