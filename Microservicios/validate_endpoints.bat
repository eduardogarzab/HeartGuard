@echo off
setlocal
cd /d "%~dp0"
set "TMP_PS=%TEMP%\validate_endpoints_%RANDOM%.ps1"
(
  echo Param()
  echo $ErrorActionPreference = 'Stop'
  echo $baseUrl = if (![string]::IsNullOrWhiteSpace($env:GATEWAY_BASE_URL)) { $env:GATEWAY_BASE_URL } else { 'http://localhost:5000' }
  echo $adminEmail = if (![string]::IsNullOrWhiteSpace($env:VALIDATE_ADMIN_EMAIL)) { $env:VALIDATE_ADMIN_EMAIL } else { 'admin@heartguard.io' }
  echo $adminPassword = if (![string]::IsNullOrWhiteSpace($env:VALIDATE_ADMIN_PASSWORD)) { $env:VALIDATE_ADMIN_PASSWORD } else { 'ChangeMe123!' }
  echo $summaryJson = New-TemporaryFile
  echo $summaryXml = New-TemporaryFile
  echo Write-Host "[INFO] Autenticando contra $baseUrl"
  echo $loginUri = "$baseUrl/auth/login"
  echo $loginBody = @{ email = $adminEmail; password = $adminPassword } ^| ConvertTo-Json
  echo $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
  echo try {
  echo ^    $response = Invoke-WebRequest -Uri $loginUri -Method Post -Headers @{ Accept = 'application/json' } -Body $loginBody -ContentType 'application/json' -UseBasicParsing
  echo ^    $loginStatus = [int]$response.StatusCode
  echo ^    $loginBodyContent = $response.Content
  echo } catch {
  echo ^    if ($_.Exception.Response) {
  echo ^        try { $loginStatus = [int]$_.Exception.Response.StatusCode } catch { $loginStatus = 0 }
  echo ^        try {
  echo ^            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
  echo ^            $loginBodyContent = $reader.ReadToEnd()
  echo ^            $reader.Dispose()
  echo ^        } catch { $loginBodyContent = '' }
  echo ^    } else {
  echo ^        $loginStatus = 0
  echo ^        $loginBodyContent = ''
  echo ^    }
  echo }
  echo $stopwatch.Stop()
  echo $loginLatency = '{0:N3}' -f $stopwatch.Elapsed.TotalSeconds
  echo $accessToken = ''
  echo if ($loginStatus -ne 200) {
  echo ^  Write-Host "[WARN] Login fallo (HTTP $loginStatus). Servicios protegidos se validaran sin token."
  echo } else {
  echo ^  Write-Host "[INFO] Login exitoso en $loginLatency s"
  echo ^  try {
  echo ^      $parsedLogin = $loginBodyContent ^| ConvertFrom-Json
  echo ^      if ($parsedLogin.access_token) { $accessToken = $parsedLogin.access_token }
  echo ^  } catch {
  echo ^      Write-Host '[WARN] No se pudo analizar la respuesta de login.'
  echo ^  }
  echo }
  echo $endpoints = @(
  echo ^  [PSCustomObject]@{ Name = 'Gateway Health'; Path = '/gateway/health'; Method = 'GET'; Access = 'public' },
  echo ^  [PSCustomObject]@{ Name = 'Auth Profile'; Path = '/auth/profile'; Method = 'GET'; Access = 'protected' },
  echo ^  [PSCustomObject]@{ Name = 'Organization Get'; Path = '/organization'; Method = 'GET'; Access = 'protected' },
  echo ^  [PSCustomObject]@{ Name = 'User Self'; Path = '/users/me'; Method = 'GET'; Access = 'protected' },
  echo ^  [PSCustomObject]@{ Name = 'Media List'; Path = '/media/items'; Method = 'GET'; Access = 'protected' },
  echo ^  [PSCustomObject]@{ Name = 'Influx Health'; Path = '/timeseries/health'; Method = 'GET'; Access = 'public' },
  echo ^  [PSCustomObject]@{ Name = 'Audit Health'; Path = '/audit/health'; Method = 'GET'; Access = 'protected' }
  echo )
  echo $results = @()
  echo Write-Host 'SERVICE^|FORMAT^|HTTP_CODE^|LATENCY_S^|STATUS'
  echo foreach ($endpoint in $endpoints) {
  echo ^  foreach ($format in @('json','xml')) {
  echo ^      $headers = @{ Accept = "application/$format" }
  echo ^      if ($endpoint.Access -eq 'protected' -and $accessToken) {
  echo ^          $headers['Authorization'] = "Bearer $accessToken"
  echo ^      }
  echo ^      $requestUri = "$baseUrl$($endpoint.Path)"
  echo ^      $sw = [System.Diagnostics.Stopwatch]::StartNew()
  echo ^      $statusCode = 0
  echo ^      $body = ''
  echo ^      try {
  echo ^          $resp = Invoke-WebRequest -Uri $requestUri -Method $endpoint.Method -Headers $headers -UseBasicParsing
  echo ^          $statusCode = [int]$resp.StatusCode
  echo ^          $body = $resp.Content
  echo ^      } catch {
  echo ^          if ($_.Exception.Response) {
  echo ^              try { $statusCode = [int]$_.Exception.Response.StatusCode } catch { $statusCode = 0 }
  echo ^              try {
  echo ^                  $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
  echo ^                  $body = $reader.ReadToEnd()
  echo ^                  $reader.Dispose()
  echo ^              } catch { $body = '' }
  echo ^          }
  echo ^      }
  echo ^      $sw.Stop()
  echo ^      $latency = '{0:N3}' -f $sw.Elapsed.TotalSeconds
  echo ^      $statusText = if ($statusCode -ge 200 -and $statusCode -lt 300) { 'OK' } else { 'FAIL' }
  echo ^      if ($format -eq 'json') {
  echo ^          Set-Content -Path $summaryJson -Value $body -Encoding UTF8
  echo ^      } else {
  echo ^          Set-Content -Path $summaryXml -Value $body -Encoding UTF8
  echo ^      }
  echo ^      Write-Host "$($endpoint.Name)^|$($format.ToUpper())^|$statusCode^|$latency^|$statusText"
  echo ^      $results += [PSCustomObject]@{
  echo ^          Service = $endpoint.Name
  echo ^          Format = $format
  echo ^          StatusCode = $statusCode
  echo ^          Latency = $latency
  echo ^          Status = $statusText
  echo ^      }
  echo ^  }
  echo }
  echo Write-Host ''
  echo Write-Host 'Resumen por servicio:'
  echo foreach ($endpoint in $endpoints) {
  echo ^  $serviceResults = $results ^| Where-Object { $_.Service -eq $endpoint.Name }
  echo ^  if ($serviceResults ^| Where-Object { $_.Status -ne 'OK' }) {
  echo ^      Write-Host "[FAIL] $($endpoint.Name)"
  echo ^  } else {
  echo ^      Write-Host "[OK] $($endpoint.Name)"
  echo ^  }
  echo }
  echo Write-Host ''
  echo Write-Host "Para más detalle revise los archivos temporales: $summaryJson $summaryXml"
) > "%TMP_PS%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%TMP_PS%"
del "%TMP_PS%" >nul 2>&1
endlocal
