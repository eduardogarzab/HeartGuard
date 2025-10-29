@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SERVICE=alert_service"
set "SCRIPT_DIR=%~dp0"
set "TMP_DIR=%SCRIPT_DIR%tmp"
if not exist "%TMP_DIR%" mkdir "%TMP_DIR%" >nul 2>&1

if not defined BASE_URL set "BASE_URL=http://34.70.7.33"
if "%BASE_URL:~-1%"=="/" set "BASE_URL=%BASE_URL:~0,-1%"
if not defined AUTH_URL set "AUTH_URL=%BASE_URL%"
if "%AUTH_URL:~-1%"=="/" set "AUTH_URL=%AUTH_URL:~0,-1%"
if not defined ADMIN_EMAIL set "ADMIN_EMAIL=ana.ruiz@heartguard.com"
if not defined ADMIN_PASSWORD set "ADMIN_PASSWORD=Demo#2025"

set "LOGIN_PAYLOAD=%TMP_DIR%\login_payload.json"
set "LOGIN_RESPONSE=%TMP_DIR%\login_response.json"

del /f /q "%LOGIN_PAYLOAD%" "%LOGIN_RESPONSE%" >nul 2>&1

set "PY_CMD=import json, os"
set "PY_CMD=!PY_CMD!; payload={'email': os.environ.get('ADMIN_EMAIL'), 'password': os.environ.get('ADMIN_PASSWORD')}"
set "PY_CMD=!PY_CMD!; open(os.environ['LOGIN_PAYLOAD'],'w', encoding='utf-8').write(json.dumps(payload, separators=(',',':')))"
python -c "!PY_CMD!" || goto fail

curl --fail --silent --show-error -X POST "%AUTH_URL%/v1/auth/login" -H "Content-Type: application/json" --data-binary "@%LOGIN_PAYLOAD%" -o "%LOGIN_RESPONSE%" >nul || goto fail

set "PY_TOKEN=import json, os"
set "PY_TOKEN=!PY_TOKEN!; data=json.load(open(os.environ['LOGIN_RESPONSE'], encoding='utf-8'))"
set "PY_TOKEN=!PY_TOKEN!; print(data['data']['access_token'])"
set "ACCESS_TOKEN="
for /f "usebackq delims=" %%i in (`python -c "!PY_TOKEN!"`) do set "ACCESS_TOKEN=%%i"
if not defined ACCESS_TOKEN goto fail

echo [%SERVICE%] Checking %BASE_URL%/health...
curl --fail --silent --show-error -H "Authorization: Bearer %ACCESS_TOKEN%" "%BASE_URL%/health" >nul || goto fail

echo [%SERVICE%] Health check OK.
exit /b 0

:fail
echo [%SERVICE%] Error durante la validacion.
exit /b 1
