@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if not exist .env (
  echo [ERROR] Archivo .env no encontrado. Copie .env.example a .env y configure las variables.
  goto :fail
)
echo [INFO] Construyendo y levantando servicios...
docker-compose --env-file .env up -d --build
set TRIES=30
for /l %%I in (1,1,%TRIES%) do (
  set STATUS=
  for /f "usebackq tokens=1" %%S in (`curl -sk -o NUL -w "%%{http_code}" http://localhost:5000/gateway/health 2^>NUL`) do set STATUS=%%S
  if "!STATUS!"=="200" (
    echo [INFO] Gateway saludable.
    goto :success
  )
  echo [INFO] Esperando gateway... (%%I/%TRIES%)
  timeout /t 2 >nul
)
echo [WARN] No se pudo verificar la salud del gateway tras %TRIES% intentos. Revise logs con docker-compose logs.
goto :fail

:success
endlocal
exit /b 0

:fail
endlocal
exit /b 1
