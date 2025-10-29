@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "ROOT_DIR=%~dp0"
set "MICRO_DIR=%ROOT_DIR%microservicios"

if not defined BASE_URL set "BASE_URL=http://34.70.7.33"
if "%BASE_URL:~-1%"=="/" set "BASE_URL=%BASE_URL:~0,-1%"
if not defined AUTH_URL set "AUTH_URL=%BASE_URL%"
if "%AUTH_URL:~-1%"=="/" set "AUTH_URL=%AUTH_URL:~0,-1%"
if not defined ADMIN_EMAIL set "ADMIN_EMAIL=ana.ruiz@heartguard.com"
if not defined ADMIN_PASSWORD set "ADMIN_PASSWORD=Demo#2025"

set "SERVICES=auth_service org_service audit_service gateway media_service alert_service analytics_service"
set "STATUS=0"

for %%S in (%SERVICES%) do (
    set "SCRIPT=%MICRO_DIR%\%%S\test_%%S.bat"
    if exist "!SCRIPT!" (
        echo.
        echo [validate] Ejecutando %%S...
        call cmd /c ""!SCRIPT!""
        set "ERR=!ERRORLEVEL!"
        if not "!ERR!"=="0" (
            echo [validate] %%S fallo con codigo !ERR!
            if "!STATUS!"=="0" set "STATUS=!ERR!"
        ) else (
            echo [validate] %%S OK.
        )
    ) else (
        echo [validate] Script no encontrado para %%S: !SCRIPT!
        if "!STATUS!"=="0" set "STATUS=1"
    )
)

set "EXIT_CODE=!STATUS!"
endlocal & exit /b %EXIT_CODE%
