@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_ROOT=%~dp0"
cd /d "%REPO_ROOT%"
set "REPO_ROOT=%cd%"
set "MICRO_DIR=%REPO_ROOT%\microservicios"
set "LOG_DIR=%MICRO_DIR%\validation_logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "REPORT=%LOG_DIR%\validation_report.txt"
if exist "%REPORT%" del "%REPORT%"

set "ADMIN_EMAIL=ana.ruiz@heartguard.com"
set "ADMIN_PASSWORD=Demo#2025"
set "POSTGRES_HOST=35.184.124.76"
set "POSTGRES_PORT=5432"
set "REDIS_PORT=6379"
set "ANALYTICS_SERVICE_PORT=5010"
set "ANALYTICS_INTERNAL_API_KEY=analytics-validation-key"
set "ANALYTICS_DATABASE_URL=postgresql://heartguard_app:dev_change_me@%POSTGRES_HOST%:%POSTGRES_PORT%/heartguard"
set "ANALYTICS_AUDIT_DATABASE_URL=%ANALYTICS_DATABASE_URL%"
set "ANALYTICS_ORG_DATABASE_URL=%ANALYTICS_DATABASE_URL%"
set "TIMESTAMP="
set "PASS_TOTAL=0"
set "FAIL_TOTAL=0"
set "TEST_COUNTER=0"
set "LAST_RESULT=UNKNOWN"
set "EXIT_CODE=0"
set "ABORT_TESTS="

call :timestamp
echo Validation run started at %TIMESTAMP% > "%REPORT%"
echo ==================================================>> "%REPORT%"
call :log "Repositorio" "!REPO_ROOT!"
call :log "Logs" "!LOG_DIR!"

call :find_python
if defined ABORT_TESTS goto finalize

call :setup_service_env "auth" "%MICRO_DIR%\auth_service"
if errorlevel 1 set "ABORT_TESTS=1"
call :setup_service_env "org" "%MICRO_DIR%\org_service"
if errorlevel 1 set "ABORT_TESTS=1"
call :setup_service_env "audit" "%MICRO_DIR%\audit_service"
if errorlevel 1 set "ABORT_TESTS=1"
call :setup_service_env "gateway" "%MICRO_DIR%\gateway"
if errorlevel 1 set "ABORT_TESTS=1"
call :setup_service_env "analytics" "%MICRO_DIR%\analytics_service"
if errorlevel 1 set "ABORT_TESTS=1"
if defined ABORT_TESTS goto finalize

call :check_dependency "PostgreSQL" "%POSTGRES_HOST%" "%POSTGRES_PORT%"
call :check_dependency "Redis" "%POSTGRES_HOST%" "%REDIS_PORT%"

call :verify_postgres
if errorlevel 1 set "ABORT_TESTS=1"
call :verify_redis
if errorlevel 1 set "ABORT_TESTS=1"
if defined ABORT_TESTS goto cleanup
rem signal_service DB init/seed removed

call :start_service "AUTH" "%MICRO_DIR%\auth_service" "%MICRO_DIR%\auth_service\.venv\Scripts\python.exe"
if errorlevel 1 set "ABORT_TESTS=1"
call :start_service "ORG" "%MICRO_DIR%\org_service" "%MICRO_DIR%\org_service\.venv\Scripts\python.exe"
if errorlevel 1 set "ABORT_TESTS=1"
call :start_service "AUDIT" "%MICRO_DIR%\audit_service" "%MICRO_DIR%\audit_service\.venv\Scripts\python.exe"
if errorlevel 1 set "ABORT_TESTS=1"
call :start_service "GATEWAY" "%MICRO_DIR%\gateway" "%MICRO_DIR%\gateway\.venv\Scripts\python.exe"
if errorlevel 1 set "ABORT_TESTS=1"
call :start_service "ANALYTICS" "%MICRO_DIR%\analytics_service" "%MICRO_DIR%\analytics_service\.venv\Scripts\python.exe"
if errorlevel 1 set "ABORT_TESTS=1"
if defined ABORT_TESTS goto cleanup

call :run_tests

:degradation_test
if defined ORG_PID if defined GW_ACCESS_TOKEN (
    call :log "Degradacion" "Deteniendo org_service (PID !ORG_PID!)"
    powershell -NoProfile -Command "Try { Stop-Process -Id !ORG_PID! -Force -ErrorAction Stop } Catch { Write-Host $_.Exception.Message }" > "%LOG_DIR%\stop_org_service.log"
    set "ORG_PID="
    set "ORG_PID_KILLED=1"
    set "TEST_NAME=Gateway routing with org_service offline"
    set /a TEST_COUNTER+=1
    set "TMP_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!TMP_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "Authorization: Bearer !GW_ACCESS_TOKEN!" "http://127.0.0.1:5000/v1/orgs/me" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "!TEST_NAME!" "!HTTP_CODE!" "503" "!TMP_FILE!"
) else (
    call :record_fail "Gateway routing with org_service offline" "No se pudo simular degradacion (PID o token ausente)"
)

if not defined GW_ACCESS_TOKEN (
    call :record_fail "Gateway routing without token" "No se pudo evaluar respuesta sin token por falla previa"
) else (
    set "TEST_NAME=Gateway without token"
    set /a TEST_COUNTER+=1
    set "TMP_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!TMP_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 "http://127.0.0.1:5000/v1/orgs/me" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "!TEST_NAME!" "!HTTP_CODE!" "401" "!TMP_FILE!"
)

:cleanup
call :log "Cleanup" "Deteniendo microservicios"
call :stop_service "AUTH"
call :stop_service "ORG"
call :stop_service "AUDIT"
call :stop_service "GATEWAY"
call :stop_service "ANALYTICS"

:finalize
call :timestamp
echo ==================================================>> "%REPORT%"
echo Validation run finished at %TIMESTAMP%>> "%REPORT%"
echo Totals: PASS=%PASS_TOTAL% FAIL=%FAIL_TOTAL%>> "%REPORT%"
echo ==================================================
echo Validacion completada. PASS=%PASS_TOTAL% FAIL=%FAIL_TOTAL%
if %FAIL_TOTAL% GTR 0 (
    set "EXIT_CODE=1"
) else (
    set "EXIT_CODE=0"
)
endlocal & exit /b %EXIT_CODE%

:: ------------------------- helper functions -------------------------

:find_python
for %%P in (py python python3) do (
    where %%P >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_BOOTSTRAP=%%P"
        call :log "Python" "Usando interprete %%P"
        goto :eof
    )
)
call :record_fail "Prerequisito" "No se encontro interprete 'py' o 'python' en PATH"
set "ABORT_TESTS=1"
exit /b 1

:setup_service_env
set "SERVICE_KEY=%~1"
set "SERVICE_DIR=%~2"
set "REQ_FILE=%SERVICE_DIR%\requirements.txt"
set "VENV_DIR=%SERVICE_DIR%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "PIP_LOG=%LOG_DIR%\%SERVICE_KEY%_pip.log"
if exist "%PIP_LOG%" del "%PIP_LOG%"
if not exist "%SERVICE_DIR%" (
    call :record_fail "Setup %SERVICE_KEY%" "Directorio no encontrado: %SERVICE_DIR%"
    exit /b 1
)
if not exist "%VENV_PY%" (
    call :log "Setup %SERVICE_KEY%" "Creando entorno virtual"
    "%PYTHON_BOOTSTRAP%" -m venv "%VENV_DIR%" > "%PIP_LOG%" 2>&1
    if errorlevel 1 (
        call :record_fail "Setup %SERVICE_KEY%" "Fallo creando entorno virtual (ver %PIP_LOG%)"
        exit /b 1
    )
) else (
    call :log "Setup %SERVICE_KEY%" "Entorno virtual existente"
)
if exist "%REQ_FILE%" (
    call :log "Setup %SERVICE_KEY%" "Instalando dependencias"
    "%VENV_PY%" -m pip install --upgrade pip >> "%PIP_LOG%" 2>&1
    if errorlevel 1 goto pip_fail
    "%VENV_PY%" -m pip install -r "%REQ_FILE%" >> "%PIP_LOG%" 2>&1
    if errorlevel 1 goto pip_fail
) else (
    call :log "Setup %SERVICE_KEY%" "No se encontro requirements.txt"
)
call :record_pass "Setup %SERVICE_KEY%" "Entorno virtual listo"
exit /b 0

:pip_fail
call :record_fail "Setup %SERVICE_KEY%" "Fallo instalando dependencias (ver %PIP_LOG%)"
exit /b 1

:check_dependency
set "DEP_NAME=%~1"
set "DEP_HOST=%~2"
set "DEP_PORT=%~3"
for /f "usebackq delims=" %%R in (`powershell -NoProfile -Command "(Test-NetConnection -ComputerName '%DEP_HOST%' -Port %DEP_PORT% -WarningAction SilentlyContinue).TcpTestSucceeded"`) do set "NET_RESULT=%%R"
if /I "!NET_RESULT!"=="True" (
    call :record_pass "Conectividad %DEP_NAME%" "Puerto %DEP_PORT% accesible"
) else (
    call :record_fail "Conectividad %DEP_NAME%" "Fallo al alcanzar %DEP_HOST%:%DEP_PORT%"
)
exit /b 0

:verify_postgres
pushd "%MICRO_DIR%\auth_service"
"%MICRO_DIR%\auth_service\.venv\Scripts\python.exe" -c "from db import get_conn, put_conn; conn = get_conn(); cur = conn.cursor(); cur.execute('SELECT 1'); cur.fetchone(); put_conn(conn)" > "%LOG_DIR%\postgres_check.log" 2>&1
set "RC=%ERRORLEVEL%"
popd
if %RC% EQU 0 (
    call :record_pass "Conexion Postgres" "Consulta SELECT 1 exitosa"
    exit /b 0
) else (
    call :record_fail "Conexion Postgres" "Fallo verificacion (ver postgres_check.log)"
    exit /b 1
)

:verify_redis
pushd "%MICRO_DIR%\auth_service"
"%MICRO_DIR%\auth_service\.venv\Scripts\python.exe" -c "from redis_client import get_redis; client = get_redis(); client.ping()" > "%LOG_DIR%\redis_check.log" 2>&1
set "RC=%ERRORLEVEL%"
popd
if %RC% EQU 0 (
    call :record_pass "Conexion Redis" "Ping exitoso"
    exit /b 0
) else (
    call :record_fail "Conexion Redis" "Fallo verificacion (ver redis_check.log)"
    exit /b 1
)

:start_service
set "SERVICE_TAG=%~1"
set "SERVICE_DIR=%~2"
set "SERVICE_PY=%~3"
set "STDOUT_FILE=%LOG_DIR%\!SERVICE_TAG!_stdout.log"
set "STDERR_FILE=%LOG_DIR%\!SERVICE_TAG!_stderr.log"
if exist "%STDOUT_FILE%" del "%STDOUT_FILE%"
if exist "%STDERR_FILE%" del "%STDERR_FILE%"

set "SHARED_ENV_FILE=%MICRO_DIR%\.env"
if exist "!SHARED_ENV_FILE!" (
    for /f "usebackq delims=" %%i in ("!SHARED_ENV_FILE!") do (
        set "%%i"
    )
)

set "SERVICE_ENV_FILE=%SERVICE_DIR%\.env"
if exist "!SERVICE_ENV_FILE!" (
    for /f "usebackq delims=" %%i in ("!SERVICE_ENV_FILE!") do (
        set "%%i"
    )
)

powershell -NoProfile -Command "Try { $p = Start-Process -FilePath '%SERVICE_PY%' -ArgumentList 'app.py' -WorkingDirectory '%SERVICE_DIR%' -RedirectStandardOutput '%STDOUT_FILE%' -RedirectStandardError '%STDERR_FILE%' -PassThru -WindowStyle Hidden; Write-Output $p.Id } Catch { Write-Output 'ERROR:' + $_.Exception.Message; exit 1 }" > "%LOG_DIR%\start_%SERVICE_TAG%.log"
set /p START_RESULT=<"%LOG_DIR%\start_%SERVICE_TAG%.log"
if /I "!START_RESULT:~0,6!"=="ERROR:" (
    call :record_fail "Start %SERVICE_TAG%" "No se pudo iniciar (ver start_%SERVICE_TAG%.log)"
    exit /b 1
)
set "%SERVICE_TAG%_PID=!START_RESULT!"
call :log "Start %SERVICE_TAG%" "PID !START_RESULT!"
timeout /t 6 /nobreak >nul
tasklist /FI "PID eq !START_RESULT!" | find "!START_RESULT!" >nul
if errorlevel 1 (
    call :record_fail "Start %SERVICE_TAG%" "Proceso finalizo prematuramente (ver stderr)"
    exit /b 1
)
call :record_pass "Start %SERVICE_TAG%" "Servicio activo"
exit /b 0

:stop_service
set "SERVICE_TAG=%~1"
set "PID="
for /f "tokens=2 delims==" %%A in ('set !SERVICE_TAG!_PID 2^>nul') do set "PID=%%A"
if defined PID (
    powershell -NoProfile -Command "Try { Stop-Process -Id %PID% -Force -ErrorAction Stop } Catch { }" >nul 2>&1
    call :log "Stop %SERVICE_TAG%" "PID %PID% detenido"
    set "!SERVICE_TAG!_PID="
)
exit /b 0

:run_tests
call :http_test "Health auth_service" "http://127.0.0.1:5001/health" "200"
call :http_test "Health org_service" "http://127.0.0.1:5002/health" "200"
call :http_test "Health audit_service" "http://127.0.0.1:5006/health" "200"
call :http_test "Health gateway" "http://127.0.0.1:5000/health" "200"
call :http_test "Health analytics_service" "http://127.0.0.1:%ANALYTICS_SERVICE_PORT%/health" "200"

rem signal_service ingest test removed

set "ANALYTICS_HEARTBEAT_PAYLOAD=%LOG_DIR%\payload_analytics_heartbeat.json"
powershell -NoProfile -Command "$payload = @{ service_name = 'gateway'; status = 'ok'; metadata = @{ source = 'validator' } } | ConvertTo-Json -Compress; Set-Content -Path '%ANALYTICS_HEARTBEAT_PAYLOAD%' -Value $payload" >nul
set /a TEST_COUNTER+=1
set "ANALYTICS_HEARTBEAT_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!ANALYTICS_HEARTBEAT_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:%ANALYTICS_SERVICE_PORT%/v1/metrics/heartbeat" -H "Content-Type: application/json" -H "X-Internal-API-Key: !ANALYTICS_INTERNAL_API_KEY!" --data-binary "@!ANALYTICS_HEARTBEAT_PAYLOAD!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Analytics heartbeat ingest" "!HTTP_CODE!" "202" "!ANALYTICS_HEARTBEAT_FILE!"

set /a TEST_COUNTER+=1
set "ANALYTICS_OVERVIEW_ADMIN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!ANALYTICS_OVERVIEW_ADMIN_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "X-User-Id: !ADMIN_EMAIL!" -H "X-User-Role: admin" -H "X-Org-Id: validation-org" "http://127.0.0.1:%ANALYTICS_SERVICE_PORT%/v1/metrics/overview" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Analytics overview admin" "!HTTP_CODE!" "200" "!ANALYTICS_OVERVIEW_ADMIN_FILE!"

set /a TEST_COUNTER+=1
set "ANALYTICS_OVERVIEW_SUPERADMIN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!ANALYTICS_OVERVIEW_SUPERADMIN_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "X-User-Id: superadmin@heartguard.com" -H "X-User-Role: superadmin" "http://127.0.0.1:%ANALYTICS_SERVICE_PORT%/v1/metrics/overview" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Analytics overview superadmin" "!HTTP_CODE!" "200" "!ANALYTICS_OVERVIEW_SUPERADMIN_FILE!"

set "LOGIN_PAYLOAD=%LOG_DIR%\payload_login.json"
powershell -NoProfile -Command "$payload = @{ email = '%ADMIN_EMAIL%' ; password = '%ADMIN_PASSWORD%' } | ConvertTo-Json -Compress; Set-Content -Path '%LOGIN_PAYLOAD%' -Value $payload" >nul
set /a TEST_COUNTER+=1
set "LOGIN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!LOGIN_FILE!" -w "%%{http_code}" --connect-timeout 15 --max-time 30 -X POST "http://127.0.0.1:5001/v1/auth/login" -H "Content-Type: application/json" --data-binary "@!LOGIN_PAYLOAD!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Auth login directo" "!HTTP_CODE!" "200" "!LOGIN_FILE!"
if /I "!LAST_RESULT!"=="PASS" (
    for /f "usebackq tokens=*" %%t in (`powershell -NoProfile -Command "(Get-Content '!LOGIN_FILE!' -Raw | ConvertFrom-Json).data.access_token"`) do set "AUTH_ACCESS_TOKEN=%%t"
    for /f "usebackq tokens=*" %%t in (`powershell -NoProfile -Command "(Get-Content '!LOGIN_FILE!' -Raw | ConvertFrom-Json).data.refresh_token"`) do set "AUTH_REFRESH_TOKEN=%%t"
)

if not defined AUTH_ACCESS_TOKEN (
    call :record_fail "Auth refresh" "No hay token de acceso"
) else (
    set /a TEST_COUNTER+=1
    set "REFRESH_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!REFRESH_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:5001/v1/auth/refresh" -H "Authorization: Bearer !AUTH_REFRESH_TOKEN!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Auth refresh" "!HTTP_CODE!" "200" "!REFRESH_FILE!"
)

if defined AUTH_ACCESS_TOKEN (
    set /a TEST_COUNTER+=1
    set "ME_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!ME_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "Authorization: Bearer !AUTH_ACCESS_TOKEN!" "http://127.0.0.1:5001/v1/users/me" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Auth users/me" "!HTTP_CODE!" "200" "!ME_FILE!"
)

set /a TEST_COUNTER+=1
set "GW_LOGIN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!GW_LOGIN_FILE!" -w "%%{http_code}" --connect-timeout 15 --max-time 30 -X POST "http://127.0.0.1:5000/v1/auth/login" -H "Content-Type: application/json" --data-binary "@!LOGIN_PAYLOAD!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Gateway login" "!HTTP_CODE!" "200" "!GW_LOGIN_FILE!"
if /I "!LAST_RESULT!"=="PASS" (
    for /f "usebackq tokens=*" %%t in (`powershell -NoProfile -Command "(Get-Content '!GW_LOGIN_FILE!' -Raw | ConvertFrom-Json).data.access_token"`) do set "GW_ACCESS_TOKEN=%%t"
)

if defined GW_ACCESS_TOKEN (
    set /a TEST_COUNTER+=1
    set "GW_ORG_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!GW_ORG_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "Authorization: Bearer !GW_ACCESS_TOKEN!" "http://127.0.0.1:5000/v1/orgs/me" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Gateway orgs/me" "!HTTP_CODE!" "200" "!GW_ORG_FILE!"
    if /I "!LAST_RESULT!"=="PASS" (
        for /f "usebackq tokens=*" %%t in (`powershell -NoProfile -Command "$json = Get-Content '!GW_ORG_FILE!' -Raw | ConvertFrom-Json; if ($json.data.organizations.Count -gt 0) { $json.data.organizations[0].id }"`) do set "PRIMARY_ORG_ID=%%t"
    )
)

if defined GW_ACCESS_TOKEN if defined PRIMARY_ORG_ID (
    set /a TEST_COUNTER+=1
    set "GW_ORG_DETAIL_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!GW_ORG_DETAIL_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "Authorization: Bearer !GW_ACCESS_TOKEN!" "http://127.0.0.1:5000/v1/orgs/!PRIMARY_ORG_ID!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Gateway org detalle" "!HTTP_CODE!" "200" "!GW_ORG_DETAIL_FILE!"
)

if defined GW_ACCESS_TOKEN (
    powershell -NoProfile -Command "$payload = @{ action = 'validation_probe'; source = 'validate_script'; actor = '%ADMIN_EMAIL%'; details = @{ message = 'test entry' } } | ConvertTo-Json -Compress; Set-Content -Path '%LOG_DIR%\payload_audit.json' -Value $payload" >nul
    set /a TEST_COUNTER+=1
    set "AUDIT_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!AUDIT_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:5000/v1/audit" -H "Authorization: Bearer !GW_ACCESS_TOKEN!" -H "Content-Type: application/json" --data-binary "@%LOG_DIR%\payload_audit.json" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Gateway audit log" "!HTTP_CODE!" "201" "!AUDIT_FILE!"
)

if defined GW_ACCESS_TOKEN if defined PRIMARY_ORG_ID (
    set /a TEST_COUNTER+=1
    set "ORG_FORBIDDEN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
    for /f "delims=" %%s in ('curl -s -o "!ORG_FORBIDDEN_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -H "Authorization: Bearer !GW_ACCESS_TOKEN!" "http://127.0.0.1:5000/v1/orgs/00000000-0000-0000-0000-000000000000" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
    call :assert_status "Gateway org inexistente" "!HTTP_CODE!" "403" "!ORG_FORBIDDEN_FILE!"
)

set /a TEST_COUNTER+=1
set "INVALID_LOGIN_PAYLOAD=%LOG_DIR%\payload_login_invalid.json"
powershell -NoProfile -Command "$payload = @{ email = '%ADMIN_EMAIL%' } | ConvertTo-Json -Compress; Set-Content -Path '%INVALID_LOGIN_PAYLOAD%' -Value $payload" >nul
set "INVALID_LOGIN_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!INVALID_LOGIN_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 -X POST "http://127.0.0.1:5001/v1/auth/login" -H "Content-Type: application/json" --data-binary "@!INVALID_LOGIN_PAYLOAD!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "Auth login incompleto" "!HTTP_CODE!" "401" "!INVALID_LOGIN_FILE!"

exit /b 0

:http_test
set "TEST_NAME=%~1"
set "TEST_URL=%~2"
set "EXPECTED=%~3"
set /a TEST_COUNTER+=1
set "TMP_FILE=%LOG_DIR%\test_!TEST_COUNTER!.json"
for /f "delims=" %%s in ('curl -s -o "!TMP_FILE!" -w "%%{http_code}" --connect-timeout 10 --max-time 20 "!TEST_URL!" 2^>"%LOG_DIR%\curl_errors.log"') do set "HTTP_CODE=%%s"
call :assert_status "!TEST_NAME!" "!HTTP_CODE!" "!EXPECTED!" "!TMP_FILE!"
exit /b 0

:assert_status
set "ASSERT_NAME=%~1"
set "ACTUAL=%~2"
set "EXPECTED=%~3"
set "BODY_FILE=%~4"
if "%ACTUAL%"=="%EXPECTED%" (
    set "LAST_RESULT=PASS"
    call :record_pass "!ASSERT_NAME!" "HTTP %ACTUAL%"
) else (
    set "LAST_RESULT=FAIL"
    call :record_fail "!ASSERT_NAME!" "HTTP %ACTUAL% (esperado %EXPECTED%)"
    call :log_response "!BODY_FILE!"
)
exit /b 0

:record_pass
set "MSG=%~1"
set "INFO=%~2"
call :timestamp
set /a PASS_TOTAL+=1
echo [%TIMESTAMP%] [PASS] %MSG% - %INFO%
echo [%TIMESTAMP%] [PASS] %MSG% - %INFO%>> "%REPORT%"
exit /b 0

:record_fail
set "MSG=%~1"
set "INFO=%~2"
call :timestamp
set /a FAIL_TOTAL+=1
echo [%TIMESTAMP%] [FAIL] %MSG% - %INFO%
echo [%TIMESTAMP%] [FAIL] %MSG% - %INFO%>> "%REPORT%"
exit /b 0

:log
set "KEY=%~1"
set "VALUE=%~2"
call :timestamp
echo [%TIMESTAMP%] [INFO] %KEY%: %VALUE%
echo [%TIMESTAMP%] [INFO] %KEY%: %VALUE%>> "%REPORT%"
exit /b 0

:log_response
set "BODY_FILE=%~1"
if exist "%BODY_FILE%" (
    powershell -NoProfile -Command "$raw = Get-Content '%BODY_FILE%' -Raw; if ($raw.Length -gt 800) { $raw = $raw.Substring(0,800) + '...'; } Add-Content -Path '%REPORT%' -Value '    Body: ' + $raw" >nul
)
exit /b 0

:timestamp
for /f "usebackq tokens=*" %%t in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "TIMESTAMP=%%t"
exit /b 0
