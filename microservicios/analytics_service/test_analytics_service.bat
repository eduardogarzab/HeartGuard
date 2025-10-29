@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem --------------------------------------------------------------
rem  Script de validación para el microservicio analytics_service
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
    echo [analytics] Creando entorno virtual...
    "%PYTHON_BOOTSTRAP%" -m venv "%VENV_DIR%"
    if errorlevel 1 goto :fail
) else (
    echo [analytics] Entorno virtual existente.
)

if not exist "%PYTHON_EXE%" (
    echo [analytics] No se encontro el interprete en el entorno virtual.
    goto :fail
)

echo [analytics] Instalando dependencias del servicio...
"%PYTHON_EXE%" -m pip install --upgrade pip >nul
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install -r "%SERVICE_DIR%\requirements.txt" >nul
if errorlevel 1 goto :fail
"%PYTHON_EXE%" -m pip install pytest >nul
if errorlevel 1 goto :fail

set "PYTHONPATH=%SERVICE_DIR%;%PYTHONPATH%"
set "FLASK_ENV=testing"
set "DATABASE_URL=sqlite+pysqlite:///:memory:"
set "READ_ONLY_DATABASE_URL=%DATABASE_URL%"
set "AUDIT_DATABASE_URL="
set "ORG_DATABASE_URL="
set "INGEST_API_KEY=test-key"
set "ANALYTICS_SERVICE_PORT=5010"

echo [analytics] Ejecutando pruebas unitarias...
"%PYTHON_EXE%" -m pytest "%SERVICE_DIR%\tests" %PYTEST_ARGS%
set "TEST_EXIT=%ERRORLEVEL%"

if %TEST_EXIT% EQU 0 (
    echo [analytics] Todas las pruebas pasaron correctamente.
    goto :success
) else (
    echo [analytics] Fallo durante la ejecucion de pruebas (codigo %TEST_EXIT%).
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
echo [analytics] No se encontro un interprete de Python en el PATH.
exit /b 1

:success
endlocal & exit /b 0

:fail
set "EXIT_CODE=%ERRORLEVEL%"
if not defined EXIT_CODE set "EXIT_CODE=1"
endlocal & exit /b %EXIT_CODE%
