@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo [Heartguard] Starting services with docker-compose...
docker-compose up -d

echo [Heartguard] Current containers:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
endlocal
