@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SERVICE=analytics_service"

if not defined BASE_URL set "BASE_URL=http://34.70.7.33"
if "%BASE_URL:~-1%"=="/" set "BASE_URL=%BASE_URL:~0,-1%"

echo [%SERVICE%] Checking %BASE_URL%/health...
curl --fail --silent --show-error "%BASE_URL%/health" >nul || goto fail

echo [%SERVICE%] Health check OK.
exit /b 0

:fail
echo [%SERVICE%] Error durante la validacion.
exit /b 1
