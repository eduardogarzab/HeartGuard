@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem --------------------------------------------------------------
rem  Script de validacion para el microservicio alert_service
rem --------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "SERVICE_DIR=%cd%"
set "VENV_DIR=%SERVICE_DIR%\.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYTEST_ARGS=-q"

call :find_python
if errorlevel 1 goto :fail

if not exist "%VENV_DIR%" (
    echo [alert] Creando entorno virtual...
    "%PYTHON_BOOTSTRAP%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :fail
) else (
    echo [alert] Entorno virtual existente.
)

if not exist "%PYTHON_EXE%" (
    echo [alert] No se encontro el interprete en el entorno virtual.
    goto :fail
)

echo [alert] Instalando dependencias del servicio...
"%PYTHON_EXE%" -m pip install --upgrade pip >nul
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install -r "%SERVICE_DIR%\requirements.txt" >nul
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install pytest >nul
if errorlevel 1 goto :fail

for %%I in ("%SERVICE_DIR%\..") do set "MICROSERVICES_DIR=%%~fI"
for %%I in ("%MICROSERVICES_DIR%\..") do set "REPO_DIR=%%~fI"
if defined PYTHONPATH (
    set "PYTHONPATH=%REPO_DIR%;%MICROSERVICES_DIR%;%SERVICE_DIR%;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%REPO_DIR%;%MICROSERVICES_DIR%;%SERVICE_DIR%"
)
set "FLASK_ENV=testing"
set "DATABASE_URL=sqlite+pysqlite:///:memory:"
set "JWT_SECRET=test-secret"
set "AUDIT_SERVICE_URL=http://localhost:5000/v1/log"
set "ANALYTICS_SERVICE_URL=http://localhost:5001/v1/ingest"

rem Se utiliza sqlite en memoria para las pruebas unitarias
set "SQLALCHEMY_SILENCE_UBER_WARNING=1"

echo [alert] Ejecutando pruebas unitarias...
"%PYTHON_EXE%" -m pytest "%SERVICE_DIR%\tests" %PYTEST_ARGS%
set "TEST_EXIT=%ERRORLEVEL%"

if "%TEST_EXIT%"=="0" (
    echo [alert] Todas las pruebas pasaron correctamente.
    goto :success
) else (
    echo [alert] Fallo durante la ejecucion de pruebas (codigo %TEST_EXIT%).
    goto :fail
)

:find_python
for %%P in (py python python3) do (
    where %%P >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_BOOTSTRAP=%%P"
        exit /b 0
    )
)
echo [alert] No se encontro un interprete de Python en el PATH.
exit /b 1

:success
endlocal & exit /b 0

:fail
set "EXIT_CODE=%ERRORLEVEL%"
if not defined EXIT_CODE set "EXIT_CODE=1"
endlocal & exit /b %EXIT_CODE%
