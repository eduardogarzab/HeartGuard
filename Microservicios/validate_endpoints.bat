@echo off
setlocal enabledelayedexpansion
if "%~1"=="" (
  echo Usage: %0 ^<host^>
  exit /b 1
)
set HOST=%~1
set SERVICES=gateway:5000 auth:5001 organization:5002 user:5003 media:5004 timeseries:5005 audit:5006

echo ==============================================
echo Validating Heartguard endpoints on %HOST%
echo ==============================================
for %%S in (%SERVICES%) do (
  for /f "tokens=1,2 delims=:" %%A in ("%%S") do (
    set NAME=%%A
    set PORT=%%B
    for %%F in (application/json application/xml) do (
      set ACCEPT=%%F
      for /f "tokens=1-2 delims==" %%L in ('powershell -NoLogo -NoProfile -Command "\
        $stopwatch=[System.Diagnostics.Stopwatch]::StartNew();\
        $resp=Invoke-WebRequest -Uri ('http://%HOST%:'+"%PORT%"+'/health') -Headers @{'Accept'='%ACCEPT%'} -UseBasicParsing;\
        $stopwatch.Stop();\
        $lat=[math]::Round($stopwatch.Elapsed.TotalMilliseconds);\
        $body=$resp.Content;\
        $status=[int]$resp.StatusCode;\
        Write-Output ('latency='+$lat);\
        Write-Output ('status='+$status);\
        Write-Output ('body='+$body.Replace("`r`n",""));"') do (
        if %%L==latency set LATENCY=%%M
        if %%L==status set STATUS=%%M
        if %%L==body set BODY=%%M
      )
      if "!STATUS!"=="200" (set RESULT=OK) else (set RESULT=FAIL)
      echo [!NAME!][!ACCEPT!] code=!STATUS! latency_ms=!LATENCY! status=!RESULT!
      echo !BODY!
      echo ----------------------------------------------
    )
    echo.
    echo ==============================================
  )
)
endlocal
